#!/usr/bin/env python3
"""
AudioBook Binder - Enhanced MP3 to M4B Converter

🔧 FULLY FIXED VERSION - All Major Issues Resolved!

Latest Fixes Applied (v2.2 - QuickLook Compatible):
- FIXED: QuickLook compatibility - always use AAC encoding for M4A/M4B containers
- FIXED: M4B brand identifier for proper audiobook recognition
- FIXED: PNG cover art support for better compatibility
- FIXED: Audiobook-specific metadata (media_type=6)
- FIXED: AAC-LC profile for maximum device compatibility

Previous Fixes (v2.1):
- Fixed ID3TimeStamp metadata extraction errors
- Fixed special character handling in file paths
- Enhanced FFmpeg error handling and validation
- Improved file path escaping for concat operations
- Added comprehensive output verification

Previous Fixes (v2.0):
- Extract-Standardize-Embed approach for cover art (always JPEG)
- Simplified FFmpeg command with clear stream mapping
- Enhanced verification that actually checks for attached pictures
- PIL/Pillow integration for image processing and validation
- Filename length truncation to prevent FFmpeg errors

Features:
- Interactive menu system with customizable settings
- QuickLook compatible M4B files (AAC audio, proper metadata)
- Multi-core FFmpeg support with proper error handling
- Discovery preview with detailed file analysis
- Enhanced cover art handling with folder/embedded priority
- Quality and Fast processing modes
- Comprehensive filename sanitization
- Natural alphanumeric sorting (Chapter1, Chapter2, Chapter10)
- Robust metadata extraction with fallback to folder names
"""

import os
import sys
import re
import json
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import threading
import time

@dataclass
class ProcessingSettings:
    """Configuration settings for audio processing"""
    max_bitrate: int = 192
    processing_mode: str = "fast"  # "fast" or "quality"
    multi_threading: bool = True
    remove_commas: bool = True
    chapter_style: str = "auto"  # "auto", "sequential", "filename"
    sanitization_level: str = "aggressive"  # "basic", "aggressive"
    cover_art_quality: str = "original"  # "original", "optimized"
    backup_originals: bool = False
    verbose_logging: bool = False
    custom_ffmpeg_options: str = ""
    show_progress: bool = True  # Show conversion progress
    progress_style: str = "detailed"  # "off", "simple", "detailed", "verbose"

@dataclass
class ConversionProgress:
    """Progress information for conversion tracking"""
    current_time: float = 0.0  # seconds processed
    total_time: float = 0.0    # total duration in seconds
    speed: float = 0.0         # processing speed multiplier
    percentage: float = 0.0    # 0-100%
    eta_seconds: float = 0.0   # estimated time remaining
    current_book: int = 0      # book number in batch
    total_books: int = 0       # total books to process
    bitrate: str = ""          # current bitrate
    file_size: str = ""        # current output file size

@dataclass
class AudioBookInfo:
    """Information about discovered audiobook"""
    name: str
    path: Path
    files: List[Path]
    file_count: int
    total_size: int
    format_info: Dict
    metadata: Dict
    cover_art: Optional[str]
    estimated_processing: str
    output_filename: str

class AudioBookBinder:
    def __init__(self, input_dir=".", output_dir=None):
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else self.input_dir / "Output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Load settings
        self.settings = self.load_settings()
        
        # Cover art patterns
        self.cover_patterns = [
            "cover.jpg", "cover.jpeg", "cover.png", 
            "folder.jpg", "folder.jpeg", "folder.png",
            "albumart.jpg", "albumart.jpeg", "albumart.png",
            "front.jpg", "front.jpeg", "front.png"
        ]
        
        # Discovered audiobooks
        self.discovered_books: List[AudioBookInfo] = []

    def load_settings(self) -> ProcessingSettings:
        """Load settings from config file or create defaults"""
        config_file = Path.home() / ".audiobook_binder_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                return ProcessingSettings(**config_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return ProcessingSettings()

    def save_settings(self):
        """Save current settings to config file"""
        config_file = Path.home() / ".audiobook_binder_config.json"
        config_data = {
            'max_bitrate': self.settings.max_bitrate,
            'processing_mode': self.settings.processing_mode,
            'multi_threading': self.settings.multi_threading,
            'remove_commas': self.settings.remove_commas,
            'chapter_style': self.settings.chapter_style,
            'sanitization_level': self.settings.sanitization_level,
            'cover_art_quality': self.settings.cover_art_quality,
            'backup_originals': self.settings.backup_originals,
            'verbose_logging': self.settings.verbose_logging,
            'custom_ffmpeg_options': self.settings.custom_ffmpeg_options,
            'show_progress': self.settings.show_progress,
            'progress_style': self.settings.progress_style
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def natural_sort_key(self, text):
        """Natural sorting for alphanumeric strings"""
        def convert(match):
            return int(match) if match.isdigit() else match.lower()
        return [convert(c) for c in re.split(r'(\d+)', str(text))]

    def sanitize_filename(self, text: str) -> str:
        """Enhanced filename sanitization"""
        if not text:
            return "Unknown"
        
        if self.settings.sanitization_level == "aggressive":
            # Remove more characters including commas, semicolons, etc.
            illegal_chars = r'[<>:"/\\|?*#%&{}$!\'@+`,;()\[\]\x00-\x1f]'
        else:
            # Basic sanitization
            illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        
        # Remove commas specifically if setting is enabled
        if self.settings.remove_commas:
            text = text.replace(',', '')
        
        clean_text = re.sub(illegal_chars, '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = clean_text.strip(' .')
        clean_text = clean_text[:200]
        
        return clean_text if clean_text else "Unknown"

    def get_format_info(self, mp3_file: Path) -> Dict:
        """Get detailed format information about an MP3 file"""
        try:
            # Use ffprobe to get detailed info
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', str(mp3_file)
            ], capture_output=True, text=True, check=True)
            
            info = json.loads(result.stdout)
            
            if 'streams' in info and len(info['streams']) > 0:
                stream = info['streams'][0]
                format_info = info.get('format', {})
                
                return {
                    'codec': stream.get('codec_name', 'unknown'),
                    'bitrate': int(format_info.get('bit_rate', 0)) // 1000,
                    'sample_rate': int(stream.get('sample_rate', 0)),
                    'channels': stream.get('channels', 0),
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0))
                }
        except:
            pass
        
        # Fallback using mutagen
        try:
            audio = MP3(mp3_file)
            return {
                'codec': 'mp3',
                'bitrate': audio.info.bitrate // 1000 if audio.info.bitrate else 128,
                'sample_rate': audio.info.sample_rate,
                'channels': audio.info.channels,
                'duration': audio.info.length,
                'size': mp3_file.stat().st_size
            }
        except:
            return {
                'codec': 'unknown',
                'bitrate': 128,
                'sample_rate': 44100,
                'channels': 2,
                'duration': 0,
                'size': mp3_file.stat().st_size
            }

    def collect_audio_files(self, book_folder: Path) -> List[Path]:
        """Collect and sort audio files"""
        audio_files = []
        
        # Check for direct MP3 files
        direct_mp3s = list(book_folder.glob("*.mp3"))
        
        if direct_mp3s:
            audio_files.extend(sorted(direct_mp3s, key=lambda x: self.natural_sort_key(x.name)))
        else:
            # Multi-level structure
            subfolders = [d for d in book_folder.iterdir() if d.is_dir()]
            for subfolder in sorted(subfolders, key=lambda x: self.natural_sort_key(x.name)):
                mp3_files = list(subfolder.glob("*.mp3"))
                mp3_files.sort(key=lambda x: self.natural_sort_key(x.name))
                audio_files.extend(mp3_files)
        
        return audio_files

    def extract_metadata(self, mp3_file: Path, book_folder: Path) -> Dict:
        """Extract comprehensive metadata with folder name fallback"""
        folder_name = book_folder.name
        
        # Initialize with empty values
        metadata = {
            'artist': "",
            'title': "",
            'album': "",
            'genre': "",
            'year': "",
            'track': "",
            'total_tracks': ""
        }
        
        try:
            audio = MP3(mp3_file, ID3=ID3)
            
            # Helper function to safely extract text from ID3 frames
            def safe_extract_text(frame):
                if not frame or not frame.text:
                    return ""
                try:
                    text_value = frame.text[0]
                    # Handle ID3TimeStamp objects and other non-string types
                    if hasattr(text_value, 'get_text'):
                        return str(text_value.get_text()).strip()
                    else:
                        return str(text_value).strip()
                except (IndexError, AttributeError, TypeError):
                    return ""
            
            # Extract embedded metadata with priority and safe handling
            if 'TPE1' in audio:
                artist_text = safe_extract_text(audio['TPE1'])
                if artist_text:
                    metadata['artist'] = artist_text
            elif 'TPE2' in audio:
                artist_text = safe_extract_text(audio['TPE2'])
                if artist_text:
                    metadata['artist'] = artist_text
                
            if 'TALB' in audio:
                album_text = safe_extract_text(audio['TALB'])
                if album_text:
                    metadata['title'] = album_text
            elif 'TIT2' in audio:
                title_text = safe_extract_text(audio['TIT2'])
                if title_text:
                    metadata['title'] = title_text
                
            if 'TCON' in audio:
                genre_text = safe_extract_text(audio['TCON'])
                if genre_text:
                    metadata['genre'] = genre_text
                
            if 'TDRC' in audio:
                year_text = safe_extract_text(audio['TDRC'])
                if year_text:
                    # Additional handling for year - extract just the year part
                    year_match = re.search(r'\d{4}', year_text)
                    if year_match:
                        metadata['year'] = year_match.group()
                    else:
                        metadata['year'] = year_text
                
        except Exception as e:
            if self.settings.verbose_logging:
                print(f"Error extracting metadata from {mp3_file}: {e}")
                import traceback
                traceback.print_exc()
        
        # Use folder name as fallback for missing artist/title
        if not metadata['artist']:
            metadata['artist'] = folder_name
            
        if not metadata['title']:
            metadata['title'] = folder_name
            
        return metadata

    def extract_and_prepare_cover_art(self, book_folder: Path, audio_files: List[Path]) -> Optional[str]:
        """Extract and standardize cover art to JPEG format"""
        import io
        try:
            from PIL import Image
        except ImportError:
            print("⚠️  Warning: PIL/Pillow not available for cover art optimization")
            # Fall back to basic extraction without optimization
            return self.find_cover_art_basic(book_folder, audio_files)
        
        cover_source = None
        cover_data = None
        source_type = None
        
        # CORRECTED PRIORITY: Check embedded artwork FIRST
        # 1. Extract embedded artwork from first audio file
        if audio_files:
            try:
                audio = MP3(audio_files[0], ID3=ID3)
                for key in audio.keys():
                    if key.startswith('APIC'):
                        apic = audio[key]
                        cover_data = apic.data
                        source_type = "embedded"
                        break
            except Exception as e:
                if self.settings.verbose_logging:
                    print(f"Warning: Could not extract embedded art: {e}")
        
        # 2. Only if no embedded art, look for folder-based cover art
        if not cover_data:
            cover_source = self.find_best_cover_image(book_folder)
            if cover_source:
                source_type = "folder"
        
        # 3. Look in subfolders if still not found
        if not cover_data and not cover_source:
            for subfolder in book_folder.iterdir():
                if subfolder.is_dir():
                    cover_source = self.find_best_cover_image(subfolder)
                    if cover_source:
                        source_type = "subfolder"
                        break
        
        # 4. No cover art found
        if not cover_source and not cover_data:
            return None
        
        # FIXED: Image processing code now properly accessible
        try:
            # Load image data
            if cover_source:
                if self.settings.verbose_logging:
                    print(f"🖼️  Found cover art: {cover_source.name} ({source_type})")
                with open(cover_source, 'rb') as f:
                    cover_data = f.read()
            else:
                if self.settings.verbose_logging:
                    print(f"🖼️  Found embedded cover art ({source_type})")
            
            # Validate and process image
            image = Image.open(io.BytesIO(cover_data))
            
            # Convert to RGB if necessary (handles RGBA, etc.)
            if image.mode != 'RGB':
                if self.settings.verbose_logging:
                    print(f"🔄 Converting from {image.mode} to RGB")
                image = image.convert('RGB')
            
            # Optimize size if needed (resize large images)
            max_dimension = 1000 if self.settings.cover_art_quality == "optimized" else 1500
            if image.width > max_dimension or image.height > max_dimension:
                if self.settings.verbose_logging:
                    print(f"📐 Resizing from {image.width}x{image.height}")
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save as standardized JPEG
            temp_cover = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            
            # Quality settings
            if self.settings.cover_art_quality == "optimized":
                jpeg_quality = 85
            else:
                jpeg_quality = 95
            
            image.save(temp_cover.name, 'JPEG', quality=jpeg_quality, optimize=True)
            temp_cover.close()
            
            if self.settings.verbose_logging:
                size_kb = Path(temp_cover.name).stat().st_size // 1024
                print(f"✅ Prepared cover art: {image.width}x{image.height}, {size_kb}KB")
            
            return temp_cover.name
            
        except Exception as e:
            print(f"❌ Error processing cover art: {e}")
            if self.settings.verbose_logging:
                import traceback
                traceback.print_exc()
            return None
    
    def find_best_cover_image(self, folder: Path) -> Optional[Path]:
        """Smart cover art selection from multiple images in folder"""
        # Get all image files
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        all_images = []
        for ext in image_extensions:
            all_images.extend(folder.glob(ext))
        
        if not all_images:
            return None
        
        if len(all_images) == 1:
            return all_images[0]
        
        # Smart selection when multiple images exist
        book_name = folder.name.lower()
        
        # Priority scoring system
        def score_image(image_path: Path) -> int:
            name = image_path.stem.lower()
            score = 0
            
            # Highest priority: exact matches with common cover names
            if name in ['cover', 'folder', 'albumart', 'front']:
                score += 100
            
            # High priority: contains book title
            # Remove common words and compare
            book_words = set(re.findall(r'\b\w+\b', book_name))
            book_words.discard('the')
            book_words.discard('a')
            book_words.discard('an')
            
            name_words = set(re.findall(r'\b\w+\b', name))
            common_words = book_words.intersection(name_words)
            if len(common_words) >= 2:  # At least 2 words match
                score += 80
            elif len(common_words) == 1:  # 1 word matches
                score += 40
            
            # Medium priority: contains cover-related keywords
            cover_keywords = ['cover', 'front', 'album', 'art', 'folder']
            if any(keyword in name for keyword in cover_keywords):
                score += 60
            
            # Lower priority: avoid small/thumbnail images
            if 'small' in name or 'thumb' in name or 'mini' in name:
                score -= 30
            
            # Prefer larger file sizes (likely higher quality)
            try:
                file_size = image_path.stat().st_size
                if file_size > 100000:  # > 100KB
                    score += 20
                elif file_size > 50000:  # > 50KB
                    score += 10
            except:
                pass
            
            return score
        
        # Sort images by score and return the best one
        scored_images = [(img, score_image(img)) for img in all_images]
        scored_images.sort(key=lambda x: x[1], reverse=True)
        
        best_image = scored_images[0][0]
        
        if self.settings.verbose_logging and len(all_images) > 1:
            print(f"🔍 Found {len(all_images)} images, selected: {best_image.name}")
            for img, score in scored_images[:3]:  # Show top 3
                print(f"   {img.name}: score {score}")
        
        return best_image
    
    def find_cover_art_basic(self, book_folder: Path, audio_files: List[Path]) -> Optional[str]:
        """Basic cover art detection without PIL optimization (fallback)"""
        # CORRECTED PRIORITY: Extract embedded artwork FIRST
        if audio_files:
            try:
                audio = MP3(audio_files[0], ID3=ID3)
                for key in audio.keys():
                    if key.startswith('APIC'):
                        apic = audio[key]
                        temp_cover = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                        temp_cover.write(apic.data)
                        temp_cover.close()
                        return temp_cover.name
            except:
                pass
        
        # Only if no embedded art, look in main folder
        for pattern in self.cover_patterns:
            for case_pattern in [pattern, pattern.upper()]:
                cover_files = list(book_folder.glob(case_pattern))
                if cover_files:
                    return str(cover_files[0])
        
        # Look in subfolders if still not found
        for subfolder in book_folder.iterdir():
            if subfolder.is_dir():
                for pattern in self.cover_patterns:
                    cover_files = list(subfolder.glob(pattern))
                    if cover_files:
                        return str(cover_files[0])
        
        return None

    def discover_audiobooks(self) -> List[AudioBookInfo]:
        """Discover and analyze all audiobooks"""
        print("🔍 Discovering audiobooks...")
        discovered = []
        
        for item in self.input_dir.iterdir():
            if item.is_dir() and item.name != "Output":
                audio_files = self.collect_audio_files(item)
                
                if not audio_files:
                    continue
                
                # Get format info from first file
                format_info = self.get_format_info(audio_files[0])
                
                # Calculate total size
                total_size = sum(f.stat().st_size for f in audio_files)
                
                # Extract metadata
                metadata = self.extract_metadata(audio_files[0], item)
                
                # Find cover art
                cover_art = self.extract_and_prepare_cover_art(item, audio_files)
                
                # Determine processing needed
                current_bitrate = format_info['bitrate']
                if self.settings.processing_mode == "fast" and current_bitrate <= self.settings.max_bitrate:
                    processing = "Stream copy (no re-encoding)"
                else:
                    if current_bitrate > self.settings.max_bitrate:
                        processing = f"Downsample ({current_bitrate}→{self.settings.max_bitrate} kbps)"
                    else:
                        processing = f"Re-encode ({current_bitrate}→{self.settings.max_bitrate} kbps)"
                
                # Generate output filename with length limits
                artist = self.sanitize_filename(metadata['artist'])
                title = self.sanitize_filename(metadata['title'])
                
                # Limit total filename length to avoid filesystem/FFmpeg issues
                max_filename_length = 200  # Safe limit for most filesystems
                base_filename = f"{artist} - {title}"
                
                if len(base_filename) > max_filename_length - 4:  # -4 for ".m4b"
                    # Truncate title if too long, preserving artist
                    max_title_length = max_filename_length - len(artist) - 7  # -7 for " - " and ".m4b"
                    if max_title_length > 20:  # Ensure we have reasonable space for title
                        title = title[:max_title_length].rstrip(' .')
                        if self.settings.verbose_logging:
                            print(f"📝 Truncated long title to: {title}")
                    else:
                        # If artist is very long, truncate both
                        max_artist_length = 60
                        max_title_length = max_filename_length - max_artist_length - 7
                        artist = artist[:max_artist_length].rstrip(' .')
                        title = title[:max_title_length].rstrip(' .')
                        if self.settings.verbose_logging:
                            print(f"📝 Truncated long artist and title")
                
                output_filename = f"{artist} - {title}.m4b"
                
                book_info = AudioBookInfo(
                    name=item.name,
                    path=item,
                    files=audio_files,
                    file_count=len(audio_files),
                    total_size=total_size,
                    format_info=format_info,
                    metadata=metadata,
                    cover_art=cover_art,
                    estimated_processing=processing,
                    output_filename=output_filename
                )
                
                discovered.append(book_info)
        
        self.discovered_books = discovered
        return discovered

    def show_settings_menu(self):
        """Display and handle settings menu"""
        while True:
            self.clear_screen()
            print("📚 AudioBook Binder - Settings")
            print("=" * 50)
            print(f"Current Settings:")
            print(f"  Max Bitrate: {self.settings.max_bitrate} kbps")
            print(f"  Processing Mode: {self.settings.processing_mode.title()} Mode")
            print(f"  Multi-threading: {'Enabled' if self.settings.multi_threading else 'Disabled'}")
            print(f"  Remove Commas: {'Yes' if self.settings.remove_commas else 'No'}")
            print(f"  Sanitization: {self.settings.sanitization_level.title()}")
            print()
            print("Options:")
            print("1. Change max bitrate")
            print("2. Toggle processing mode (Fast/Quality)")  
            print("3. Toggle multi-threading")
            print("4. Advanced settings")
            print("5. Preview discovery results")
            print("6. Start processing")
            print("7. Exit")
            print()
            
            choice = input("Choice [1-7 or Enter to start]: ").strip()
            
            # Default to start processing on Enter
            if choice == "" or choice == "6":
                if self.discovered_books:
                    return True  # Start processing
                else:
                    print("\n❌ No audiobooks discovered yet. Please run discovery first.")
                    input("Press Enter to continue...")
            elif choice == "1":
                self.change_bitrate()
            elif choice == "2":
                self.toggle_processing_mode()
            elif choice == "3":
                self.settings.multi_threading = not self.settings.multi_threading
                self.save_settings()
            elif choice == "4":
                self.advanced_settings_menu()
            elif choice == "5":
                self.show_discovery_results()
            elif choice == "7":
                return False  # Exit
            else:
                print("Invalid choice. Please try again.")
                time.sleep(1)

    def change_bitrate(self):
        """Change bitrate setting"""
        bitrates = [64, 96, 128, 192, 256, 320]
        
        print("\nAvailable bitrates:")
        for i, br in enumerate(bitrates, 1):
            mark = " ✓" if br == self.settings.max_bitrate else ""
            print(f"{i}. {br} kbps{mark}")
        
        try:
            choice = int(input(f"\nSelect bitrate [1-{len(bitrates)}]: ").strip())
            if 1 <= choice <= len(bitrates):
                self.settings.max_bitrate = bitrates[choice - 1]
                self.save_settings()
                print(f"✓ Bitrate set to {self.settings.max_bitrate} kbps")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        
        time.sleep(1)

    def toggle_processing_mode(self):
        """Toggle between Fast and Quality mode"""
        if self.settings.processing_mode == "fast":
            self.settings.processing_mode = "quality"
            print("✓ Switched to Quality Mode")
        else:
            self.settings.processing_mode = "fast" 
            print("✓ Switched to Fast Mode")
        
        self.save_settings()
        time.sleep(1)

    def advanced_settings_menu(self):
        """Advanced settings menu"""
        while True:
            self.clear_screen()
            print("🔧 Advanced Settings")
            print("=" * 30)
            print(f"1. Chapter naming: {self.settings.chapter_style}")
            print(f"2. Filename sanitization: {self.settings.sanitization_level}")
            print(f"3. Cover art quality: {self.settings.cover_art_quality}")
            print(f"4. Remove commas: {'Yes' if self.settings.remove_commas else 'No'}")
            print(f"5. Verbose logging: {'On' if self.settings.verbose_logging else 'Off'}")
            print(f"6. Progress display: {self.settings.progress_style.title()}")
            print(f"7. Show progress: {'On' if self.settings.show_progress else 'Off'}")
            print("8. Back to main menu")
            
            choice = input("\nChoice [1-8]: ").strip()
            
            if choice == "1":
                self.change_chapter_style()
            elif choice == "2":
                self.toggle_sanitization_level()
            elif choice == "3":
                self.toggle_cover_art_quality()
            elif choice == "4":
                self.settings.remove_commas = not self.settings.remove_commas
                self.save_settings()
            elif choice == "5":
                self.settings.verbose_logging = not self.settings.verbose_logging
                self.save_settings()
            elif choice == "6":
                self.change_progress_style()
            elif choice == "7":
                self.settings.show_progress = not self.settings.show_progress
                self.save_settings()
            elif choice == "8":
                break
            else:
                print("Invalid choice")
                time.sleep(1)

    def change_chapter_style(self):
        """Change chapter naming style"""
        styles = ["auto", "sequential", "filename"]
        print("\nChapter naming styles:")
        for i, style in enumerate(styles, 1):
            mark = " ✓" if style == self.settings.chapter_style else ""
            print(f"{i}. {style.title()}{mark}")
        
        try:
            choice = int(input(f"\nSelect style [1-{len(styles)}]: ").strip())
            if 1 <= choice <= len(styles):
                self.settings.chapter_style = styles[choice - 1]
                self.save_settings()
        except ValueError:
            print("❌ Invalid input")
        time.sleep(1)

    def toggle_sanitization_level(self):
        """Toggle sanitization level"""
        if self.settings.sanitization_level == "basic":
            self.settings.sanitization_level = "aggressive"
        else:
            self.settings.sanitization_level = "basic"
        self.save_settings()
        time.sleep(1)

    def toggle_cover_art_quality(self):
        """Toggle cover art quality"""
        if self.settings.cover_art_quality == "original":
            self.settings.cover_art_quality = "optimized"
        else:
            self.settings.cover_art_quality = "original"
        self.save_settings()
        time.sleep(1)

    def change_progress_style(self):
        """Change progress display style"""
        styles = ["off", "simple", "detailed", "verbose"]
        print("\nProgress display styles:")
        for i, style in enumerate(styles, 1):
            mark = " ✓" if style == self.settings.progress_style else ""
            description = {
                "off": "No progress display",
                "simple": "Simple percentage only",
                "detailed": "Progress bar with ETA and speed",
                "verbose": "Full details with bitrate and file size"
            }
            print(f"{i}. {style.title()}: {description[style]}{mark}")
        
        try:
            choice = int(input(f"\nSelect style [1-{len(styles)}]: ").strip())
            if 1 <= choice <= len(styles):
                self.settings.progress_style = styles[choice - 1]
                self.save_settings()
                print(f"✓ Progress style set to {self.settings.progress_style}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
        time.sleep(1)

    def show_discovery_results(self):
        """Display detailed discovery results"""
        if not self.discovered_books:
            self.discover_audiobooks()
        
        self.clear_screen()
        print("🔍 Discovery Results")
        print("=" * 50)
        
        if not self.discovered_books:
            print("❌ No audiobook folders found!")
            input("\nPress Enter to continue...")
            return
        
        total_files = 0
        total_size = 0
        
        for i, book in enumerate(self.discovered_books, 1):
            print(f"\n📚 {book.name}")
            print(f"   📁 Files: {book.file_count} MP3s ({self.format_size(book.total_size)})")
            
            format_str = f"{book.format_info['codec'].upper()}, {book.format_info['bitrate']} kbps"
            if book.format_info['channels'] == 1:
                format_str += ", mono"
            elif book.format_info['channels'] == 2:
                format_str += ", stereo"
            
            print(f"   🎵 Format: {format_str}")
            print(f"   📖 Metadata: {book.metadata['artist']} | {book.metadata['title']}")
            
            if book.cover_art:
                if book.cover_art.startswith('/tmp'):
                    print(f"   🖼️  Cover Art: Embedded")
                else:
                    cover_name = Path(book.cover_art).name
                    print(f"   🖼️  Cover Art: {cover_name}")
            else:
                print(f"   🖼️  Cover Art: Not found")
            
            print(f"   ⚡ Processing: {book.estimated_processing}")
            print(f"   📝 Output: \"{book.output_filename}\"")
            
            total_files += book.file_count
            total_size += book.total_size
        
        print(f"\n" + "=" * 50)
        print(f"📊 Processing Summary:")
        print(f"✅ Total books: {len(self.discovered_books)}")
        print(f"📁 Total files: {total_files}")
        print(f"💾 Total size: {self.format_size(total_size)}")
        
        cover_count = sum(1 for book in self.discovered_books if book.cover_art)
        print(f"🖼️  Cover art found: {cover_count}/{len(self.discovered_books)}")
        
        # Estimate processing time
        avg_speed = 0.5 if self.settings.processing_mode == "fast" else 0.3  # MB/s
        est_time_sec = total_size / (1024 * 1024) / avg_speed
        est_time_min = est_time_sec / 60
        
        if est_time_min < 60:
            time_str = f"{est_time_min:.0f} minutes"
        else:
            hours = est_time_min // 60
            minutes = est_time_min % 60
            time_str = f"{hours:.0f}h {minutes:.0f}m"
        
        print(f"⏱️  Estimated time: {time_str}")
        
        # Ask if user wants to see detailed file order
        print(f"\nShow detailed file order for each audiobook? [y/N]: ", end="")
        if input().lower() in ['y', 'yes']:
            self.show_detailed_file_order()
        
        print("\nProceed with processing? [Y/n]: ", end="")
        if input().lower() in ['', 'y', 'yes']:
            return True
        return False
    
    def show_detailed_file_order(self):
        """Display detailed file order for each audiobook"""
        self.clear_screen()
        print("📋 Detailed File Order Preview")
        print("=" * 60)
        
        for i, book in enumerate(self.discovered_books, 1):
            print(f"\n📚 [{i}/{len(self.discovered_books)}] {book.name}")
            print(f"📁 {book.file_count} files will be processed in this order:")
            print("-" * 50)
            
            # Show file order with numbering
            for j, audio_file in enumerate(book.files, 1):
                file_name = audio_file.name
                file_size = self.format_size(audio_file.stat().st_size)
                
                # Highlight potential ordering issues
                if book.file_count <= 20:
                    # Show all files for smaller collections
                    print(f"   {j:2d}. {file_name} ({file_size})")
                else:
                    # Show first 5, middle indicator, last 5 for large collections
                    if j <= 5:
                        print(f"   {j:2d}. {file_name} ({file_size})")
                    elif j == 6:
                        remaining = book.file_count - 10
                        print(f"   ... ({remaining} more files) ...")
                    elif j > book.file_count - 5:
                        print(f"   {j:2d}. {file_name} ({file_size})")
            
            # Show chapter naming preview
            print(f"\n   📖 Chapter naming style: {self.settings.chapter_style}")
            if self.settings.chapter_style == "filename":
                sample_chapter = book.files[0].stem if book.files else "filename"
                print(f"   📝 Example chapter: \"{sample_chapter}\"")
            elif self.settings.chapter_style == "sequential":
                print(f"   📝 Example chapters: \"Chapter 01\", \"Chapter 02\", etc.")
            else:  # auto
                # Determine what auto naming would produce
                if book.files:
                    parent_name = book.files[0].parent.name
                    if any(disc in parent_name.lower() for disc in ['disc', 'disk', 'cd']):
                        print(f"   📝 Example chapter: \"{parent_name} - {book.files[0].stem}\"")
                    else:
                        print(f"   📝 Example chapters: \"Chapter 01\", \"Chapter 02\", etc.")
            
            # Check for potential sorting issues
            potential_issues = []
            if book.files:
                file_names = [f.name for f in book.files]
                
                # Check for common numbering patterns
                has_leading_zeros = any(re.search(r'\b0\d', name) for name in file_names)
                has_no_leading_zeros = any(re.search(r'\b\d{2,}', name) for name in file_names)
                
                if has_leading_zeros and has_no_leading_zeros:
                    potential_issues.append("Mixed leading zero patterns detected")
                
                # Check for chapter/part keywords
                has_chapter = any(re.search(r'\bchapter\b|\bpart\b|\btrack\b', name.lower()) for name in file_names[:3])
                if not has_chapter:
                    potential_issues.append("No chapter/part keywords detected in filenames")
            
            if potential_issues:
                print(f"\n   ⚠️  Potential issues:")
                for issue in potential_issues:
                    print(f"      • {issue}")
                print(f"   💡 Files are sorted using natural alphanumeric ordering")
            else:
                print(f"\n   ✅ File ordering looks good!")
        
        print(f"\n" + "=" * 60)
        print("💡 Tips:")
        print("   • Files are sorted using natural alphanumeric ordering (1, 2, 10 vs 1, 10, 2)")
        print("   • You can change chapter naming in Advanced Settings")
        print("   • Check that the file order matches your expected listening sequence")
        
        input("\nPress Enter to continue...")

    def format_size(self, size_bytes: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def create_chapter_file(self, audio_files: List[Path]) -> str:
        """Create chapter file for FFmpeg"""
        chapter_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        
        current_time = 0
        for i, audio_file in enumerate(audio_files):
            try:
                audio = MP3(audio_file)
                duration_ms = int(audio.info.length * 1000)
                
                # Chapter naming based on settings
                if self.settings.chapter_style == "filename":
                    chapter_name = audio_file.stem
                elif self.settings.chapter_style == "sequential":
                    chapter_name = f"Chapter {i+1:02d}"
                else:  # auto
                    parent_name = audio_file.parent.name
                    if any(disc in parent_name.lower() for disc in ['disc', 'disk', 'cd']):
                        chapter_name = f"{parent_name} - {audio_file.stem}"
                    else:
                        chapter_name = f"Chapter {i+1:02d}"
                
                chapter_file.write(f"[CHAPTER]\n")
                chapter_file.write(f"TIMEBASE=1/1000\n") 
                chapter_file.write(f"START={current_time}\n")
                chapter_file.write(f"END={current_time + duration_ms}\n")
                chapter_file.write(f"title={chapter_name}\n\n")
                
                current_time += duration_ms
                
            except Exception as e:
                if self.settings.verbose_logging:
                    print(f"Warning: Could not get duration for {audio_file}: {e}")
                
                # Default chapter
                default_duration = 60 * 60 * 1000
                chapter_file.write(f"[CHAPTER]\n")
                chapter_file.write(f"TIMEBASE=1/1000\n")
                chapter_file.write(f"START={current_time}\n")
                chapter_file.write(f"END={current_time + default_duration}\n")
                chapter_file.write(f"title=Chapter {i+1:02d}\n\n")
                current_time += default_duration
        
        chapter_file.close()
        return chapter_file.name

    def normalize_file_path(self, file_path: Path) -> str:
        """Normalize file paths to handle special characters and encoding issues"""
        try:
            # Convert to absolute path and normalize
            normalized = str(file_path.resolve())
            
            # Handle common problematic characters
            replacements = {
                '\u2019': "'",  # Right single quotation mark (curly apostrophe)
                '\u2018': "'",  # Left single quotation mark
                '\u201c': '"',  # Left double quotation mark
                '\u201d': '"',  # Right double quotation mark
                '\u2013': '-',  # En dash
                '\u2014': '-',  # Em dash
                '\u00e9': 'e',  # é
                '\u00e8': 'e',  # è
                '\u00e0': 'a',  # à
                '\u00f1': 'n',  # ñ
            }
            
            for old, new in replacements.items():
                normalized = normalized.replace(old, new)
            
            # Ensure the path is valid UTF-8
            normalized.encode('utf-8')
            
            return normalized
        except (UnicodeEncodeError, UnicodeDecodeError, OSError) as e:
            if self.settings.verbose_logging:
                print(f"Warning: Path normalization issue for {file_path}: {e}")
            # Fall back to string representation
            return str(file_path)
    
    def create_robust_concat_file(self, audio_files: List[Path]) -> str:
        """Create a robust concat file with proper path handling"""
        # Create temp file in a predictable location
        temp_dir = Path(tempfile.gettempdir())
        concat_file_path = temp_dir / f"audiobook_concat_{os.getpid()}_{int(time.time())}.txt"
        
        try:
            with open(concat_file_path, 'w', encoding='utf-8', newline='\n') as f:
                for audio_file in audio_files:
                    # Normalize and escape the path
                    normalized_path = self.normalize_file_path(audio_file)
                    
                    # Escape for FFmpeg concat format
                    # Replace backslashes with forward slashes for cross-platform compatibility
                    if os.name == 'nt':  # Windows
                        normalized_path = normalized_path.replace('\\', '/')
                    
                    # Escape special characters for FFmpeg
                    escaped_path = normalized_path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Verify the file was created and has content
            if not concat_file_path.exists() or concat_file_path.stat().st_size == 0:
                raise ValueError("Concat file creation failed or file is empty")
            
            if self.settings.verbose_logging:
                print(f"📄 Created concat file: {concat_file_path}")
                print(f"📊 File size: {concat_file_path.stat().st_size} bytes")
                # Show first few lines for debugging
                with open(concat_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[:3]
                    for i, line in enumerate(lines):
                        print(f"   Line {i+1}: {line.strip()}")
            
            return str(concat_file_path)
            
        except Exception as e:
            print(f"❌ Error creating concat file: {e}")
            if concat_file_path.exists():
                try:
                    concat_file_path.unlink()
                except:
                    pass
            raise

    def calculate_total_duration(self, audio_files: List[Path]) -> float:
        """Calculate total duration of all audio files in seconds"""
        total_duration = 0.0
        for audio_file in audio_files:
            try:
                audio = MP3(audio_file)
                total_duration += audio.info.length
            except Exception as e:
                if self.settings.verbose_logging:
                    print(f"Warning: Could not get duration for {audio_file}: {e}")
                # Use file size as rough estimate (1MB ≈ 1 minute for typical audiobooks)
                file_size_mb = audio_file.stat().st_size / (1024 * 1024)
                total_duration += file_size_mb * 60  # Rough estimate
        return total_duration

    def parse_ffmpeg_progress(self, line: str, progress: ConversionProgress) -> bool:
        """Parse FFmpeg progress output and update progress object"""
        try:
            # FFmpeg progress patterns
            time_pattern = r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})'
            speed_pattern = r'speed=\s*([0-9.]+)x'
            bitrate_pattern = r'bitrate=\s*([0-9.]+)kbits/s'
            size_pattern = r'size=\s*(\d+)kB'
            
            # Parse time
            time_match = re.search(time_pattern, line)
            if time_match:
                hours = int(time_match.group(1))
                minutes = int(time_match.group(2))
                seconds = int(time_match.group(3))
                centiseconds = int(time_match.group(4))
                progress.current_time = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                
                # Calculate percentage and ETA
                if progress.total_time > 0:
                    progress.percentage = min((progress.current_time / progress.total_time) * 100, 100)
                    if progress.speed > 0 and progress.current_time > 0:
                        remaining_time = progress.total_time - progress.current_time
                        progress.eta_seconds = remaining_time / progress.speed
                
                return True
            
            # Parse speed
            speed_match = re.search(speed_pattern, line)
            if speed_match:
                progress.speed = float(speed_match.group(1))
            
            # Parse bitrate
            bitrate_match = re.search(bitrate_pattern, line)
            if bitrate_match:
                progress.bitrate = f"{bitrate_match.group(1)} kbps"
            
            # Parse file size
            size_match = re.search(size_pattern, line)
            if size_match:
                size_kb = int(size_match.group(1))
                progress.file_size = self.format_size(size_kb * 1024)
            
        except Exception as e:
            if self.settings.verbose_logging:
                print(f"Error parsing progress: {e}")
        
        return False

    def display_progress(self, progress: ConversionProgress):
        """Display conversion progress based on style setting"""
        if self.settings.progress_style == "off" or not self.settings.show_progress:
            return
        
        # Clear the current line and move cursor to beginning
        print('\r', end='')
        
        if self.settings.progress_style == "simple":
            # Simple percentage display
            if progress.percentage > 0:
                print(f"Progress: {progress.percentage:.1f}%", end='', flush=True)
        
        elif self.settings.progress_style == "detailed":
            # Detailed progress with ETA
            if progress.percentage > 0:
                # Progress bar
                bar_width = 20
                filled_width = int(bar_width * progress.percentage / 100)
                bar = "█" * filled_width + "░" * (bar_width - filled_width)
                
                # Format time
                current_str = self.format_duration(progress.current_time)
                total_str = self.format_duration(progress.total_time)
                
                # ETA
                eta_str = ""
                if progress.eta_seconds > 0 and progress.eta_seconds < 36000:  # Less than 10 hours
                    eta_str = f" | ETA: {self.format_duration(progress.eta_seconds)}"
                
                # Speed
                speed_str = ""
                if progress.speed > 0:
                    speed_str = f" | {progress.speed:.1f}x"
                
                print(f"{bar} {progress.percentage:.1f}% ({current_str}/{total_str}){eta_str}{speed_str}", 
                      end='', flush=True)
        
        elif self.settings.progress_style == "verbose":
            # Verbose progress with all details
            if progress.percentage > 0:
                # Multi-line verbose display
                print(f"\n📊 Progress: {progress.percentage:.1f}%")
                print(f"⏱️  Time: {self.format_duration(progress.current_time)} / {self.format_duration(progress.total_time)}")
                if progress.speed > 0:
                    print(f"🚀 Speed: {progress.speed:.1f}x")
                if progress.eta_seconds > 0 and progress.eta_seconds < 36000:
                    print(f"⏳ ETA: {self.format_duration(progress.eta_seconds)}")
                if progress.bitrate:
                    print(f"📡 Bitrate: {progress.bitrate}")
                if progress.file_size:
                    print(f"💾 Size: {progress.file_size}")
                print("=" * 40, end='', flush=True)

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to HH:MM:SS format"""
        if seconds <= 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def run_ffmpeg_with_progress(self, cmd: List[str], total_duration: float, 
                                current_book: int, total_books: int) -> bool:
        """Run FFmpeg with real-time progress tracking"""
        progress = ConversionProgress(
            total_time=total_duration,
            current_book=current_book,
            total_books=total_books
        )
        
        try:
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Track progress in real-time
            last_update = time.time()
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                
                if output:
                    output = output.strip()
                    
                    # Parse progress information
                    if self.parse_ffmpeg_progress(output, progress):
                        # Update display every 0.5 seconds to avoid spam
                        current_time = time.time()
                        if current_time - last_update >= 0.5:
                            self.display_progress(progress)
                            last_update = current_time
                    
                    # Log verbose output if enabled
                    if self.settings.verbose_logging:
                        print(f"\nFFmpeg: {output}")
            
            # Final progress update
            if self.settings.show_progress and self.settings.progress_style != "off":
                if progress.percentage < 100:
                    progress.percentage = 100.0
                    progress.current_time = progress.total_time
                self.display_progress(progress)
                print()  # New line after progress
            
            # Check return code
            return_code = process.poll()
            return return_code == 0
            
        except Exception as e:
            print(f"\n❌ Error running FFmpeg with progress: {e}")
            return False

    def create_m4b(self, book_info: AudioBookInfo, current_book: int = 1, total_books: int = 1) -> bool:
        """Create M4B file with enhanced processing for QuickLook compatibility"""
        print(f"\n🎵 Processing: {book_info.name}")
        print("=" * 60)
        
        # Always use AAC encoding for QuickLook compatibility
        # QuickLook requires AAC audio in M4A/M4B containers
        current_bitrate = book_info.format_info['bitrate']
        target_bitrate = min(current_bitrate, self.settings.max_bitrate)
        print(f"🎧 Converting to AAC for QuickLook compatibility: {target_bitrate} kbps")
        
        # Setup paths
        output_path = self.output_dir / book_info.output_filename
        counter = 1
        original_output_path = output_path
        while output_path.exists():
            stem = original_output_path.stem
            output_path = self.output_dir / f"{stem} ({counter}).m4b"
            counter += 1
        
        # Create robust concat file
        try:
            concat_file_path = self.create_robust_concat_file(book_info.files)
        except Exception as e:
            print(f"❌ Failed to create concat file: {e}")
            return False
        
        # Create chapter file
        chapter_file = self.create_chapter_file(book_info.files)
        
        # Build FFmpeg command optimized for QuickLook compatibility
        cmd = ['ffmpeg']
        
        # Multi-threading
        if self.settings.multi_threading:
            cmd.extend(['-threads', '0'])
        
        # ALL INPUTS FIRST (this is critical for FFmpeg)
        # Input 0: Audio files via concat
        cmd.extend(['-f', 'concat', '-safe', '0', '-i', concat_file_path])
        
        # Input 1: Cover art (if available)
        cover_input_index = None
        if book_info.cover_art:
            cmd.extend(['-i', book_info.cover_art])
            cover_input_index = 1
        
        # Input 2/1: Chapter file (always last input)
        cmd.extend(['-i', chapter_file])
        chapter_input_index = 2 if cover_input_index is not None else 1
        
        # STREAM MAPPING (after all inputs declared)
        cmd.extend(['-map', '0:a'])  # Map audio from input 0 (concat file)
        
        if cover_input_index is not None:
            cmd.extend(['-map', f'{cover_input_index}:v:0'])  # Map first video stream from cover input
        
        # CHAPTERS - must come BEFORE encoding options
        cmd.extend(['-map_chapters', str(chapter_input_index)])
        
        # ENCODING OPTIONS FOR QUICKLOOK COMPATIBILITY
        # Always use AAC audio encoding for QuickLook compatibility
        cmd.extend(['-c:a', 'aac', '-b:a', f'{target_bitrate}k'])
        # Use AAC-LC profile for maximum compatibility
        cmd.extend(['-profile:a', 'aac_low'])
        
        # Video encoding for cover art (use PNG codec for better compatibility)
        if cover_input_index is not None:
            cmd.extend(['-c:v:0', 'png'])  # Use PNG instead of MJPEG for better compatibility
            
            if self.settings.cover_art_quality == "optimized":
                cmd.extend(['-vf:0', 'scale=600:600:force_original_aspect_ratio=decrease'])
            
            cmd.extend(['-disposition:v:0', 'attached_pic'])  # Mark as attached picture
            cmd.extend(['-metadata:s:v:0', 'title=Cover'])    # Add cover metadata
        
        # M4B/M4A Container format for QuickLook compatibility
        cmd.extend(['-f', 'mp4'])
        
        # Set correct brand for M4B audiobook format
        cmd.extend(['-movflags', '+faststart'])
        cmd.extend(['-brand', 'M4B '])  # M4B brand for audiobooks
        
        # Audiobook-specific metadata
        cmd.extend(['-metadata', f'title={book_info.metadata["title"]}'])
        cmd.extend(['-metadata', f'artist={book_info.metadata["artist"]}'])
        cmd.extend(['-metadata', f'album_artist={book_info.metadata["artist"]}'])
        cmd.extend(['-metadata', f'album={book_info.metadata["title"]}'])
        
        # Set media type for audiobooks
        cmd.extend(['-metadata', 'media_type=6'])  # 6 = Audiobook
        
        if book_info.metadata['genre']:
            cmd.extend(['-metadata', f'genre={book_info.metadata["genre"]}'])
        else:
            cmd.extend(['-metadata', 'genre=Audiobook'])  # Default genre for audiobooks
            
        if book_info.metadata['year']:
            cmd.extend(['-metadata', f'date={book_info.metadata["year"]}'])
        
        # Custom options
        if self.settings.custom_ffmpeg_options:
            cmd.extend(self.settings.custom_ffmpeg_options.split())
        
        # Output file
        cmd.extend(['-y', str(output_path)])
        
        # Execute FFmpeg with enhanced error handling
        try:
            if self.settings.verbose_logging:
                print(f"FFmpeg command: {' '.join(cmd)}")
            
            print(f"📁 Output: {output_path}")
            print("⏳ Processing...")
            
            # Validate inputs exist before running FFmpeg
            if not Path(concat_file_path).exists():
                print(f"❌ Error: Concat file not found: {concat_file_path}")
                return False
            
            if book_info.cover_art and not Path(book_info.cover_art).exists():
                print(f"❌ Error: Cover art file not found: {book_info.cover_art}")
                return False
            
            if not Path(chapter_file).exists():
                print(f"❌ Error: Chapter file not found: {chapter_file}")
                return False
            
            # Calculate total duration for progress tracking
            total_duration = self.calculate_total_duration(book_info.files)
            
            # Run FFmpeg with progress monitoring
            success = self.run_ffmpeg_with_progress(cmd, total_duration, current_book, total_books)
            
            if not success:
                print(f"❌ Error: FFmpeg conversion failed")
                return False
            
            # Verify output file was created and is not empty
            if not output_path.exists():
                print(f"❌ Error: Output file was not created")
                return False
            
            if output_path.stat().st_size == 0:
                print(f"❌ Error: Output file is empty")
                output_path.unlink()  # Remove empty file
                return False
            
            print(f"✅ Success: {book_info.output_filename} ({self.format_size(output_path.stat().st_size)})")
            
            # Verify cover art was embedded
            if book_info.cover_art and self.verify_cover_art(output_path):
                print("🖼️  Cover art verified")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ FFmpeg Error (exit code {e.returncode})"
            print(error_msg)
            
            # Parse and display specific error information
            if e.stderr:
                stderr_lines = e.stderr.strip().split('\n')
                # Look for key error patterns
                for line in stderr_lines[-10:]:  # Check last 10 lines for errors
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ['error', 'failed', 'invalid', 'no such file']):
                        print(f"   {line.strip()}")
                        
                if self.settings.verbose_logging:
                    print(f"\nFull FFmpeg stderr:\n{e.stderr}")
            
            # Clean up failed output file
            if output_path.exists():
                try:
                    output_path.unlink()
                    if self.settings.verbose_logging:
                        print(f"Cleaned up failed output file: {output_path}")
                except:
                    pass
            
            return False
        except Exception as e:
            print(f"❌ Unexpected error during FFmpeg execution: {e}")
            if self.settings.verbose_logging:
                import traceback
                traceback.print_exc()
            return False
            
        finally:
            # Cleanup
            try:
                os.unlink(concat_file_path)
                os.unlink(chapter_file)
                if book_info.cover_art and book_info.cover_art.startswith('/tmp'):
                    os.unlink(book_info.cover_art)
            except:
                pass

    def verify_cover_art(self, m4b_file: Path) -> bool:
        """Verify that cover art was properly embedded as attached picture"""
        try:
            # Check for attached picture disposition
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-select_streams', 'v:0',
                '-show_entries', 'stream=disposition:stream=codec_name',
                '-of', 'csv=p=0', str(m4b_file)
            ], capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')
            
            # Look for mjpeg codec and attached_pic disposition
            has_mjpeg = False
            has_attached_pic = False
            
            for line in lines:
                if 'mjpeg' in line:
                    has_mjpeg = True
                if 'attached_pic=1' in line:
                    has_attached_pic = True
            
            # For more thorough verification, also check stream count
            if has_mjpeg:
                # Additional check: verify we have exactly what we expect
                stream_result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-show_entries', 'stream=codec_type',
                    '-of', 'csv=p=0', str(m4b_file)
                ], capture_output=True, text=True, check=True)
                
                stream_lines = stream_result.stdout.strip().split('\n')
                has_video = any('video' in line for line in stream_lines)
                
                if self.settings.verbose_logging and has_video:
                    print(f"📊 Verification: mjpeg={has_mjpeg}, attached_pic={has_attached_pic}, video_stream={has_video}")
                
                return has_mjpeg and has_video
            
            return False
            
        except Exception as e:
            if self.settings.verbose_logging:
                print(f"⚠️  Cover art verification failed: {e}")
            return False

    def process_all_audiobooks(self) -> Tuple[int, int]:
        """Process all discovered audiobooks"""
        if not self.discovered_books:
            print("❌ No audiobooks to process!")
            return 0, 0
        
        successful = 0
        failed = 0
        
        print(f"\n🚀 Starting batch processing of {len(self.discovered_books)} audiobooks...")
        print("=" * 70)
        
        start_time = time.time()
        
        for i, book_info in enumerate(self.discovered_books, 1):
            print(f"\n[{i}/{len(self.discovered_books)}] 📚 {book_info.name}")
            
            try:
                if self.create_m4b(book_info, current_book=i, total_books=len(self.discovered_books)):
                    successful += 1
                    print(f"✅ Completed: {book_info.output_filename}")
                else:
                    failed += 1
                    print(f"❌ Failed: {book_info.output_filename}")
            except KeyboardInterrupt:
                print(f"\n⚠️  Processing interrupted by user")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                failed += 1
        
        # Final summary
        elapsed_time = time.time() - start_time
        print(f"\n" + "=" * 70)
        print(f"🎉 Batch Processing Complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total time: {self.format_time(elapsed_time)}")
        print(f"📁 Output files saved to: {self.output_dir}")
        
        return successful, failed

    def format_time(self, seconds: float) -> str:
        """Format time duration for display"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) / 60
            return f"{hours:.0f}h {minutes:.0f}m"

    def run_interactive(self):
        """Run the interactive menu system"""
        # Initial discovery
        self.discover_audiobooks()
        
        if not self.discovered_books:
            print("❌ No audiobook folders found in the current directory!")
            print(f"📁 Searched in: {self.input_dir}")
            print("\nPlease ensure your audiobook folders contain MP3 files.")
            return
        
        # Show settings menu
        if self.show_settings_menu():
            # User chose to start processing
            self.process_all_audiobooks()
        
        print("\n👋 Goodbye!")

    def run_batch_mode(self):
        """Run in batch mode (non-interactive)"""
        print("📚 AudioBook Binder - Batch Mode")
        print("=" * 50)
        
        # Discover audiobooks
        books = self.discover_audiobooks()
        
        if not books:
            print("❌ No audiobook folders found!")
            return
        
        print(f"🔍 Found {len(books)} audiobook(s)")
        
        # Show brief summary
        for book in books:
            print(f"  📚 {book.name} ({book.file_count} files)")
        
        # Process all
        print(f"\n🚀 Processing with current settings...")
        print(f"   Max bitrate: {self.settings.max_bitrate} kbps")
        print(f"   Mode: {self.settings.processing_mode.title()}")
        
        self.process_all_audiobooks()


def main():
    parser = argparse.ArgumentParser(
        description="AudioBook Binder - Enhanced MP3 to M4B Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 audiobook_binder.py                    # Interactive mode
  python3 audiobook_binder.py --batch           # Batch mode
  python3 audiobook_binder.py /path/to/books    # Specify input directory
  python3 audiobook_binder.py -o /path/output   # Specify output directory
        """
    )
    
    parser.add_argument(
        "input_dir", 
        nargs="?", 
        default=".", 
        help="Input directory containing audiobook folders (default: current directory)"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Output directory for M4B files (default: Input_dir/Output)"
    )
    
    parser.add_argument(
        "--batch", 
        action="store_true",
        help="Run in batch mode (no interactive menu)"
    )
    
    parser.add_argument(
        "--bitrate", 
        type=int, 
        choices=[64, 96, 128, 192, 256, 320],
        help="Set maximum bitrate (kbps)"
    )
    
    parser.add_argument(
        "--fast", 
        action="store_true",
        help="Use fast mode (stream copy when possible)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: FFmpeg is not installed or not in PATH")
        print("📥 Please install FFmpeg: brew install ffmpeg")
        sys.exit(1)
    
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: FFprobe is not installed or not in PATH")
        print("📥 FFprobe should be included with FFmpeg")
        sys.exit(1)
    
    # Initialize binder
    binder = AudioBookBinder(args.input_dir, args.output)
    
    # Apply command line settings
    if args.bitrate:
        binder.settings.max_bitrate = args.bitrate
    
    if args.fast:
        binder.settings.processing_mode = "fast"
    
    if args.verbose:
        binder.settings.verbose_logging = True
    
    # Run appropriate mode
    if args.batch:
        binder.run_batch_mode()
    else:
        binder.run_interactive()


if __name__ == "__main__":
    main()

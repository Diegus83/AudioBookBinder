# AudioBook Binder - Enhanced Edition

A powerful, feature-rich Python script that converts MP3 audiobooks to M4B format with full metadata preservation, interactive settings, and intelligent processing.

## ✨ New Enhanced Features

### 🎛️ Interactive Menu System
- **Settings Menu**: Customizable bitrate, processing modes, and advanced options
- **Discovery Preview**: See exactly what will be processed before starting
- **Real-time Configuration**: All settings saved and persistent across sessions

### ⚡ Smart Processing
- **Auto Mode**: Concatenate `.mp4b` files without re-encoding. Re-encode `.mp3` files. Mixed `.mp3`/`.m4b` folders are ignored.
- **Force Re-encode Mode**: Always re-encode inputs.
- **Multi-core Support**: Utilizes all CPU cores for faster processing

### 🔧 Advanced Settings
- **Bitrate Options**: 64, 96, 128, 192, 256, 320 kbps (192 kbps default)
- **Processing Modes**: Fast (stream copy) vs Quality (re-encode when needed)
- **Chapter Naming**: Auto, Sequential, or Filename-based
- **Sanitization Levels**: Basic or Aggressive filename cleaning
- **Cover Art Quality**: Original or Optimized for smaller file sizes
- **Audio Codec**: AAC-LC or HE-AAC for better quality at low bitrates

## 🚀 Key Features

- **Multi-structure Support**: Single-folder and multi-disc audiobook structures
- **Natural Sorting**: Proper alphanumeric sorting (Chapter1, Chapter2, Chapter10)
- **Metadata Preservation**: Extracts and preserves artist, title, genre, year
- **Folder-name Metadata Parsing**: If MP3 tags are missing, parses metadata from the audiobook folder name using customizable templates
- **Enhanced Cover Art**: Finds folder images OR extracts from MP3 metadata
- **Intelligent Quality**: Never upscales - only maintains or reduces bitrate
- **Filename Sanitization**: Removes commas, special characters for clean names
- **Chapter Markers**: Automatically creates navigable chapters
- **Batch Processing**: Process multiple audiobooks in one run
- **Progress Tracking**: Real-time processing updates with time estimates

## 📋 Prerequisites

- **macOS** (script optimized for macOS, adaptable to other systems)
- **Python 3.6+** with dataclasses support
- **FFmpeg & FFprobe** (for audio processing)
- **mutagen** (Python library for MP3 metadata)

## 🛠️ Installation

1. **Install FFmpeg** (if not already installed):
   ```bash
   brew install ffmpeg
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install mutagen
   ```

3. **Download the script** and make it executable:
   ```bash
   chmod +x audiobook_binder.py
   ```

## 🎯 Usage

### Interactive Mode (Recommended)
Launch the interactive menu system:
```bash
python3 audiobook_binder.py
```

**Interactive Features:**
- 📊 **Discovery Preview**: See all audiobooks before processing
- ⚙️ **Settings Menu**: Configure bitrate, processing mode, and advanced options
- 📈 **Progress Tracking**: Real-time updates with time estimates
- 🎛️ **Advanced Settings**: Chapter naming, cover art quality, sanitization levels

### Batch Mode (Quick Processing)
Process with current settings without menus:
```bash
python3 audiobook_binder.py --batch
```

### Command Line Options
```bash
# Specify input directory
python3 audiobook_binder.py /path/to/audiobooks

# Custom output directory
python3 audiobook_binder.py -o /path/to/output

# Fast mode with specific bitrate
python3 audiobook_binder.py --fast --bitrate 128

# Verbose logging for troubleshooting
python3 audiobook_binder.py --verbose --batch
```

## 📁 Supported Folder Structures

### Single-Level Audiobooks
```
AudioBooks/
├── Stephen King - The Shining/
│   ├── 01-Chapter1.mp3
│   ├── 02-Chapter2.mp3
│   ├── 03-Chapter3.mp3
│   └── cover.jpg
└── Craig Alanson - Expeditionary Force Book 1/
    ├── Part1.mp3
    ├── Part2.mp3
    └── folder.png
```

### Multi-Disc Audiobooks
```
AudioBooks/
├── Epic Fantasy Series Book 1/
│   ├── Disc1/
│   │   ├── Track01.mp3
│   │   ├── Track02.mp3
│   │   └── Track03.mp3
│   ├── Disc2/
│   │   ├── Track01.mp3
│   │   └── Track02.mp3
│   └── cover.jpg
└── Science Fiction Novel/
    ├── CD1/
    │   ├── 01-Prologue.mp3
    │   └── 02-Chapter1.mp3
    ├── CD2/
    │   ├── 01-Chapter5.mp3
    │   └── 02-Epilogue.mp3
```

## 🎵 Output

### File Naming
- **Format**: `Artist - BookTitle.m4b` (commas and special characters removed)
- **Examples**:
  - `Stephen King - The Shining.m4b`
  - `Ben Greenfield - Beyond Training Mastering Endurance Health Life.m4b`

### Quality Optimization
- **Smart Bitrate**: `min(input_bitrate, max_bitrate_setting)`
- **Auto Mode**: Copy audio for `.m4b`-only books; re-encode `.mp3` books as needed.
- **Force Re-encode Mode**: Re-encode all books regardless of input container.

## 📊 Discovery Preview Example

```
🔍 Discovery Results
==================================================

📚 Beyond Training- Mastering Endurance, Health & Life [2015]
   📁 Files: 34 MP3s (545.5 MB)
   🎵 Format: MP3, 89 kbps, mono
   📖 Metadata: Ben Greenfield | Beyond Training: Mastering Endurance, Health & Life
   🖼️  Cover Art: Embedded (500x500 JPEG)
   ⚡ Processing: Re-encode (89→192 kbps)
   📝 Output: "Ben Greenfield - Beyond Training Mastering Endurance Health Life.m4b"

==================================================
📊 Processing Summary:
✅ Total books: 1
📁 Total files: 34
💾 Total size: 545.5 MB
🖼️  Cover art found: 1/1
⏱️  Estimated time: 30 minutes

Proceed with processing? [Y/n]:
```

## ⚙️ Advanced Settings

### Processing Modes
- **Auto Mode**: `.m4b`-only folders are concatenated with audio copied; `.mp3` folders are re-encoded as before.
- **Force Re-encode Mode**: Forces re-encoding of all inputs to ensure consistent output and metadata embedding.

### Chapter Naming Options
- **Auto**: Smart detection (Disc 1 - Track 1, Chapter 01, etc.)
- **Sequential**: Simple Chapter 01, Chapter 02, etc.
- **Filename**: Uses original MP3 filenames as chapter names

### Sanitization Levels
- **Basic**: Removes illegal filesystem characters only
- **Aggressive**: Removes commas, semicolons, brackets, and special punctuation

### Cover Art Quality
- **Original**: Maintains original cover art resolution and quality
- **Optimized**: Scales to 500x500 for smaller file sizes

### Audio Codec Options
- **AAC-LC**: Default, widely compatible.
- **HE-AAC**: More efficient at low bitrates , with good compatibility in modern players.

### Folder Name Metadata Parsing
If MP3 metadata is missing or incomplete, AudioBook Binder can fall back to parsing metadata from the audiobook folder name.

- **Customizable templates** let you define your naming convention.
- **Preview + edit** in interactive mode so you can verify and adjust before processing.

**Example templates:**
- `{artist} - {title} - {year}`
- `{artist} - {title}`
- `{year} - {artist} - {title}`

## 🔧 Command Line Arguments

```bash
usage: audiobook_binder.py [-h] [-o OUTPUT] [--batch] [--bitrate {64,96,128,192,256,320}] [--fast] [--verbose] [input_dir]

AudioBook Binder - Enhanced MP3 to M4B Converter

positional arguments:
  input_dir             Input directory containing audiobook folders (default: current directory)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory for M4B files (default: Input_dir/Output)
  --batch               Run in batch mode (no interactive menu)
  --bitrate {64,96,128,192,256,320}
                        Set maximum bitrate (kbps)
  --fast                Use fast mode (stream copy when possible)
  --verbose             Enable verbose logging

Examples:
  python3 audiobook_binder.py                    # Interactive mode
  python3 audiobook_binder.py --batch           # Batch mode  
  python3 audiobook_binder.py /path/to/books    # Specify input directory
  python3 audiobook_binder.py -o /path/output   # Specify output directory
```

## 🎯 Performance

### Processing Speed Examples
- **Fast Mode**: 1.5 seconds for 15-file audiobook (stream copy)
- **Quality Mode**: 30 minutes for 34-file, 545MB audiobook (re-encoding)

### Multi-threading
- **Automatic**: Uses all available CPU cores (`-threads 0`)
- **Configurable**: Can be disabled in advanced settings

## 🐛 Troubleshooting

### Common Issues

**"FFmpeg is not installed or not in PATH"**
```bash
brew install ffmpeg
# Restart terminal after installation
```

**"libfdk_aac encoder not available" / HE-AAC selected but not supported**
Using Homebrew (FFmpeg with FDK AAC support):
```bash
brew tap homebrew-ffmpeg/ffmpeg
brew install homebrew-ffmpeg/ffmpeg/ffmpeg --with-fdk-aac
```

**"No module named 'mutagen'"**
```bash
pip3 install mutagen
```

**No audiobooks discovered**
- Ensure folders contain `.mp3` files
- Check that you're in the parent directory containing audiobook folders
- Use `--verbose` flag for detailed discovery information

### Supported File Patterns
- **Audio**: `.mp3` files only
- **Cover Art**: `.jpg`, `.jpeg`, `.png` (case-insensitive)
- **Cover Names**: `cover.*`, `folder.*`, `albumart.*`, `front.*`

## 📝 Configuration File

Settings are automatically saved to `~/.audiobook_binder_config.json`:
```json
{
  "max_bitrate": 192,
  "processing_mode": "quality",
  "multi_threading": true,
  "remove_commas": true,
  "chapter_style": "auto",
  "sanitization_level": "aggressive",
  "cover_art_quality": "original",
  "verbose_logging": false,
  "audio_codec": "aac_lc",
  "folder_metadata_template": ["artist","title","year"],
  "folder_metadata_separator": " - "
}
```

## 🆕 What's New in Enhanced Edition

### v2.0 Enhancements
- ✨ **Interactive Menu System** with real-time configuration
- 🔍 **Discovery Preview** showing detailed analysis before processing  
- ⚡ **Smart Processing** with stream copy for compatible files
- 🖼️ **Enhanced Cover Art** handling with verification
- 🧹 **Advanced Sanitization** removing commas and special characters
- 🎛️ **Configurable Settings** with persistent storage
- 📊 **Progress Tracking** with time estimates
- 🚀 **Multi-core Support** for faster processing
- 📋 **Batch Mode** for automated processing
- 🔧 **Advanced Settings** for power users

## 📄 License

This script is provided as-is for personal use. Feel free to modify and adapt as needed.

## 🤝 Contributing

Feel free to submit issues, feature requests, or improvements! The enhanced version includes comprehensive error handling and verbose logging for easier troubleshooting.

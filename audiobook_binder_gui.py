#!/usr/bin/env python3
"""
AudioBook Binder GUI - Modern Interface for MP3 to M4B Conversion

A graphical user interface for the AudioBook Binder that provides:
- Drag & drop folder selection
- Visual settings management
- Real-time progress tracking
- Professional user experience
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Callable
import time

# Import the core AudioBook Binder functionality
from audiobook_binder import AudioBookBinder, AudioBookInfo, ProcessingSettings

class ProgressCallback:
    """Callback interface for progress updates from the processing thread"""
    def __init__(self, update_queue: queue.Queue):
        self.update_queue = update_queue
    
    def update_status(self, message: str):
        """Update status message"""
        self.update_queue.put(('status', message))
    
    def update_progress(self, percentage: float, current_book: int = 0, total_books: int = 0):
        """Update progress bar"""
        self.update_queue.put(('progress', percentage, current_book, total_books))
    
    def update_log(self, message: str):
        """Add message to log"""
        self.update_queue.put(('log', message))
    
    def processing_complete(self, successful: int, failed: int):
        """Signal processing completion"""
        self.update_queue.put(('complete', successful, failed))

class BookProgressTracker:
    """Tracks progress for individual book processing"""
    def __init__(self, progress_callback: ProgressCallback, current_book: int, total_books: int, base_progress: float):
        self.progress_callback = progress_callback
        self.current_book = current_book
        self.total_books = total_books
        self.base_progress = base_progress
        self.book_weight = 100.0 / total_books  # Each book is worth this much of total progress
    
    def update_book_progress(self, book_percentage: float):
        """Update progress for current book (0-100)"""
        # Convert book progress to overall progress
        book_contribution = (book_percentage / 100.0) * self.book_weight
        overall_progress = self.base_progress + book_contribution
        
        self.progress_callback.update_progress(
            min(overall_progress, 100.0), 
            self.current_book, 
            self.total_books
        )

class GUIProgressHandler:
    """Custom progress handler that intercepts AudioBookBinder progress updates"""
    def __init__(self, progress_callback: ProgressCallback, current_book: int, total_books: int):
        self.progress_callback = progress_callback
        self.current_book = current_book
        self.total_books = total_books
        self.base_progress = ((current_book - 1) / total_books) * 100
        self.book_weight = 100.0 / total_books
        
    def display_progress(self, progress_info, thread_name=None):
        """Called by AudioBookBinder during FFmpeg processing"""
        if hasattr(progress_info, 'percentage') and progress_info.percentage > 0:
            # Convert book progress to overall progress
            book_contribution = (progress_info.percentage / 100.0) * self.book_weight
            overall_progress = self.base_progress + book_contribution
            
            self.progress_callback.update_progress(
                min(overall_progress, 100.0), 
                self.current_book, 
                self.total_books
            )

class AudioBookBinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AudioBook Binder - GUI")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Initialize variables
        self.source_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.binder = None
        self.discovered_books = []
        self.processing_thread = None
        self.update_queue = queue.Queue()
        
        # Create main interface
        self.create_widgets()
        self.setup_bindings()
        
        # Start GUI update loop
        self.root.after(100, self.process_queue)
        
        # Center window on screen
        self.center_window()

    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def get_system_text_color(self):
        """Get system-appropriate text color based on light/dark mode"""
        try:
            # Get the system's background color to determine if it's light or dark mode
            bg_color = self.root.cget('bg')
            
            # Try to get the actual color values
            try:
                # Convert color name/hex to RGB values
                rgb = self.root.winfo_rgb(bg_color)
                # Calculate luminance (perceived brightness)
                # RGB values are 0-65535, so convert to 0-255 range
                r, g, b = [x/256 for x in rgb]
                # Calculate luminance using standard formula
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                
                # If luminance is low (dark background), use light text
                # If luminance is high (light background), use dark text
                if luminance < 0.5:
                    return "white"  # Dark mode - use light text
                else:
                    return "black"  # Light mode - use dark text
            except:
                # Fallback: check if bg_color suggests dark mode
                if bg_color in ['#1e1e1e', '#2d2d30', '#252526', '#3c3c3c'] or 'dark' in bg_color.lower():
                    return "white"
                else:
                    return "black"
        except:
            # Ultimate fallback - return system default
            return "SystemWindowText"

    def create_widgets(self):
        """Create the main GUI layout"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="wens")
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 AudioBook Binder", font=('TkDefaultFont', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Source folder selection
        ttk.Label(main_frame, text="Source Folder:", font=('TkDefaultFont', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        source_frame = ttk.Frame(main_frame)
        source_frame.grid(row=1, column=1, columnspan=2, sticky="we", pady=5)
        source_frame.columnconfigure(0, weight=1)
        
        self.source_entry = ttk.Entry(source_frame, textvariable=self.source_folder, font=('TkDefaultFont', 10))
        self.source_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        
        self.source_browse_btn = ttk.Button(source_frame, text="Browse...", command=self.browse_source_folder)
        self.source_browse_btn.grid(row=0, column=1)
        
        # Output folder selection
        ttk.Label(main_frame, text="Output Folder:", font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_folder, font=('TkDefaultFont', 10))
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.output_browse_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output_folder)
        self.output_browse_btn.grid(row=0, column=1)
        
        # Settings panel
        self.create_settings_panel(main_frame)
        
        # Discovered books panel
        self.create_books_panel(main_frame)
        
        # Progress and control panel
        self.create_progress_panel(main_frame)
        
        # Set default values
        self.source_folder.set(str(Path.cwd()))
        self.output_folder.set(str(Path.cwd() / "Output"))

    def create_settings_panel(self, parent):
        """Create the settings configuration panel"""
        settings_frame = ttk.LabelFrame(parent, text="🔧 Settings", padding="15")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        settings_frame.columnconfigure(1, weight=1)
        
        # Bitrate setting
        ttk.Label(settings_frame, text="Max Bitrate:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.bitrate_var = tk.StringVar(value="192")
        bitrate_combo = ttk.Combobox(settings_frame, textvariable=self.bitrate_var, 
                                   values=["64", "96", "128", "192", "256", "320"], 
                                   width=8, state="readonly")
        bitrate_combo.grid(row=0, column=1, sticky=tk.W)
        ttk.Label(settings_frame, text="kbps").grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # Processing mode
        ttk.Label(settings_frame, text="Processing Mode:").grid(row=0, column=3, sticky=tk.W, padx=(20, 10))
        self.mode_var = tk.StringVar(value="fast")
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.grid(row=0, column=4, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Fast", variable=self.mode_var, value="fast").grid(row=0, column=0, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="Quality", variable=self.mode_var, value="quality").grid(row=0, column=1)
        
        # Advanced settings (second row)
        self.parallel_books_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Parallel processing", variable=self.parallel_books_var).grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        self.remove_commas_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Remove commas", variable=self.remove_commas_var).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))

    def create_books_panel(self, parent):
        """Create the discovered books display panel"""
        books_frame = ttk.LabelFrame(parent, text="📚 Discovered Audiobooks", padding="15")
        books_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        books_frame.columnconfigure(0, weight=1)
        books_frame.rowconfigure(0, weight=1)
        
        # Create treeview for books
        columns = ('Name', 'Files', 'Size', 'Format', 'Processing')
        self.books_tree = ttk.Treeview(books_frame, columns=columns, show='tree headings', height=8)
        
        # Configure columns
        self.books_tree.heading('#0', text='✓')
        self.books_tree.column('#0', width=30, anchor=tk.CENTER)
        
        for col in columns:
            self.books_tree.heading(col, text=col)
            if col == 'Name':
                self.books_tree.column(col, width=200)
            elif col == 'Files':
                self.books_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == 'Size':
                self.books_tree.column(col, width=80, anchor=tk.E)
            elif col == 'Format':
                self.books_tree.column(col, width=120)
            elif col == 'Processing':
                self.books_tree.column(col, width=150)
        
        # Scrollbar for treeview
        books_scrollbar = ttk.Scrollbar(books_frame, orient=tk.VERTICAL, command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=books_scrollbar.set)
        
        self.books_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        books_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def create_progress_panel(self, parent):
        """Create the progress and control panel"""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        progress_frame.columnconfigure(1, weight=1)
        
        # Control buttons
        button_frame = ttk.Frame(progress_frame)
        button_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        self.discover_btn = ttk.Button(button_frame, text="🔍 Discover Books", command=self.discover_books)
        self.discover_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.process_btn = ttk.Button(button_frame, text="🚀 Start Processing", command=self.start_processing, style="Accent.TButton")
        self.process_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2)
        
        # Progress bar
        ttk.Label(progress_frame, text="Progress:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=1, column=2)
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Select a source folder to begin", foreground="gray")
        self.status_label.grid(row=2, column=0, columnspan=3, pady=(5, 0))

    def setup_bindings(self):
        """Set up event bindings"""
        self.source_folder.trace_add('write', self.on_source_folder_change)
        self.output_folder.trace_add('write', self.on_output_folder_change)

    def on_source_folder_change(self, *args):
        """Handle source folder changes"""
        if self.source_folder.get():
            # Auto-set output folder if not manually set
            source_path = Path(self.source_folder.get())
            if source_path.exists() and source_path.is_dir():
                suggested_output = source_path / "Output"
                if not self.output_folder.get() or self.output_folder.get() == str(Path.cwd() / "Output"):
                    self.output_folder.set(str(suggested_output))
                
                self.status_label.config(text="Click 'Discover Books' to scan for audiobooks", foreground="blue")
                self.discover_btn.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="Please select a valid source folder", foreground="red")
                self.discover_btn.config(state=tk.DISABLED)

    def on_output_folder_change(self, *args):
        """Handle output folder changes"""
        pass

    def browse_source_folder(self):
        """Open folder browser for source directory"""
        folder = filedialog.askdirectory(
            title="Select Source Folder (containing audiobook folders)",
            initialdir=self.source_folder.get() or str(Path.cwd())
        )
        if folder:
            self.source_folder.set(folder)

    def browse_output_folder(self):
        """Open folder browser for output directory"""
        folder = filedialog.askdirectory(
            title="Select Output Folder (where M4B files will be saved)",
            initialdir=self.output_folder.get() or str(Path.cwd())
        )
        if folder:
            self.output_folder.set(folder)

    def get_current_settings(self) -> ProcessingSettings:
        """Create ProcessingSettings from current GUI values"""
        return ProcessingSettings(
            max_bitrate=int(self.bitrate_var.get()),
            processing_mode=self.mode_var.get(),
            parallel_books=self.parallel_books_var.get(),
            remove_commas=self.remove_commas_var.get(),
            show_progress=False,  # We handle progress in GUI
            progress_style="off"  # Disable console progress
        )

    def discover_books(self):
        """Discover audiobooks in the source folder"""
        if not self.source_folder.get():
            messagebox.showerror("Error", "Please select a source folder first")
            return
        
        source_path = Path(self.source_folder.get())
        if not source_path.exists() or not source_path.is_dir():
            messagebox.showerror("Error", "Source folder does not exist or is not a directory")
            return
        
        self.status_label.config(text="Discovering audiobooks...", foreground="blue")
        self.discover_btn.config(state=tk.DISABLED)
        self.root.update()
        
        try:
            # Create binder with current settings
            output_path = self.output_folder.get() or str(source_path / "Output")
            self.binder = AudioBookBinder(str(source_path), output_path)
            self.binder.settings = self.get_current_settings()
            
            # Discover books
            self.discovered_books = self.binder.discover_audiobooks()
            
            # Update the treeview
            self.update_books_display()
            
            if self.discovered_books:
                self.status_label.config(text=f"Found {len(self.discovered_books)} audiobook(s) ready to process", foreground="green")
                self.process_btn.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="No audiobooks found in the selected folder", foreground="orange")
                self.process_btn.config(state=tk.DISABLED)
                
        except Exception as e:
            messagebox.showerror("Discovery Error", f"Error discovering audiobooks:\n{str(e)}")
            self.status_label.config(text="Discovery failed", foreground="red")
        finally:
            self.discover_btn.config(state=tk.NORMAL)

    def update_books_display(self):
        """Update the books treeview with discovered audiobooks"""
        # Clear existing items
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        # Add discovered books
        for book in self.discovered_books:
            # Format file size
            size_mb = book.total_size / (1024 * 1024)
            if size_mb < 1024:
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = f"{size_mb/1024:.1f} GB"
            
            # Format audio info
            format_str = f"{book.format_info['codec'].upper()}, {book.format_info['bitrate']} kbps"
            
            self.books_tree.insert('', tk.END, text='✓', values=(
                book.name,
                f"{book.file_count} files",
                size_str,
                format_str,
                book.estimated_processing
            ))

    def start_processing(self):
        """Start processing audiobooks in a background thread"""
        if not self.discovered_books:
            messagebox.showerror("Error", "No audiobooks to process. Run discovery first.")
            return
        
        # Check for FFmpeg
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            result = messagebox.askyesno(
                "FFmpeg Not Found", 
                "FFmpeg is required but not found in your system PATH.\n\n"
                "Please install FFmpeg first:\n"
                "• macOS: brew install ffmpeg\n"
                "• Windows: Download from ffmpeg.org\n"
                "• Linux: apt install ffmpeg\n\n"
                "Do you want to continue anyway?"
            )
            if not result:
                return
        
        # PIL/Pillow is now bundled with the app, no runtime check needed
        
        # Update UI for processing state
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.discover_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="Starting processing...", foreground="blue")
        
        # Create progress callback
        progress_callback = ProgressCallback(self.update_queue)
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self.process_books_thread,
            args=(progress_callback,),
            daemon=True
        )
        self.processing_thread.start()

    def process_books_thread(self, progress_callback: ProgressCallback):
        """Background thread for processing audiobooks"""
        try:
            progress_callback.update_status("Initializing processing...")
            
            # Update binder settings (with null check)
            if self.binder is not None:
                self.binder.settings = self.get_current_settings()
                # Disable console progress to avoid conflicts
                self.binder.settings.show_progress = False
                self.binder.settings.progress_style = "off"
                
                # Set up progress callback for real-time FFmpeg progress
                def ffmpeg_progress_callback(ffmpeg_progress):
                    """Convert CLI ConversionProgress to GUI progress updates"""
                    # Calculate overall progress considering current book
                    current_book = ffmpeg_progress.current_book or 1
                    total_books = ffmpeg_progress.total_books or 1
                    
                    # Base progress for completed books
                    base_progress = ((current_book - 1) / total_books) * 100
                    
                    # Add progress for current book
                    book_contribution = (ffmpeg_progress.percentage / total_books)
                    overall_progress = base_progress + book_contribution
                    
                    # Send to GUI thread
                    progress_callback.update_progress(min(overall_progress, 100.0), current_book, total_books)
                
                # Set the callback on the binder instance
                self.binder._progress_callback = ffmpeg_progress_callback
                
            else:
                progress_callback.update_log("❌ Error: No binder instance available")
                progress_callback.processing_complete(0, len(self.discovered_books))
                return
            
            successful = 0
            failed = 0
            total_books = len(self.discovered_books)
            
            for i, book_info in enumerate(self.discovered_books, 1):
                progress_callback.update_status(f"Processing book {i} of {total_books}: {book_info.name}")
                
                # Update progress at start of book
                base_progress = ((i - 1) / total_books) * 100
                progress_callback.update_progress(base_progress, i, total_books)
                
                try:
                    # Process the book (now with real-time progress updates)
                    result = self.binder.create_m4b(book_info, current_book=i, total_books=total_books)
                    
                    if result:
                        successful += 1
                        progress_callback.update_status(f"✅ Completed: {book_info.output_filename}")
                    else:
                        failed += 1
                        progress_callback.update_status(f"❌ Failed: {book_info.name}")
                        
                except Exception as e:
                    failed += 1
                    progress_callback.update_status(f"❌ Error processing {book_info.name}: {str(e)}")
                
                # Update progress at end of book (ensures 100% for completed books)
                end_progress = (i / total_books) * 100
                progress_callback.update_progress(end_progress, i, total_books)
            
            # Clean up progress callback
            if hasattr(self.binder, '_progress_callback'):
                delattr(self.binder, '_progress_callback')
            
            progress_callback.processing_complete(successful, failed)
            
        except Exception as e:
            progress_callback.update_status(f"❌ Processing error: {str(e)}")
            # Clean up progress callback on error
            if hasattr(self.binder, '_progress_callback'):
                delattr(self.binder, '_progress_callback')
            progress_callback.processing_complete(0, len(self.discovered_books))

    def stop_processing(self):
        """Stop the current processing immediately"""
        # Update UI immediately to show stopping
        self.stop_btn.config(state=tk.DISABLED, text="Stopping...")
        self.status_label.config(text="Cancelling processing...", foreground="orange")
        
        # Cancel processing immediately
        if self.binder:
            self.binder.cancel_processing()
        
        # Reset UI after a brief delay to show the cancellation
        self.root.after(1000, self.finalize_cancellation)
    
    def finalize_cancellation(self):
        """Finalize the cancellation and reset UI"""
        self.progress_var.set(0)
        self.progress_label.config(text="Cancelled")
        self.status_label.config(text="Processing cancelled by user", foreground="red")
        self.stop_btn.config(text="⏹ Stop")  # Reset button text
        self.reset_ui_state()
        
        # Show cancellation message
        messagebox.showinfo("Processing Cancelled", "Processing has been stopped immediately.\nAny partial files have been cleaned up.")

    def reset_ui_state(self):
        """Reset UI to ready state"""
        self.process_btn.config(state=tk.NORMAL if self.discovered_books else tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.discover_btn.config(state=tk.NORMAL)

    def process_queue(self):
        """Process updates from the background thread"""
        try:
            while True:
                try:
                    update = self.update_queue.get_nowait()
                except queue.Empty:
                    break
                
                update_type = update[0]
                
                if update_type == 'status':
                    # Use system-appropriate color instead of hardcoded blue
                    system_color = self.get_system_text_color()
                    self.status_label.config(text=update[1], foreground=system_color)
                    
                elif update_type == 'progress':
                    progress = update[1]
                    self.progress_var.set(progress)
                    if len(update) > 3:
                        current_book, total_books = update[2], update[3]
                        self.progress_label.config(text=f"{progress:.1f}% ({current_book}/{total_books})")
                    else:
                        self.progress_label.config(text=f"{progress:.1f}%")
                        
                elif update_type == 'log':
                    # For now, we'll just update the status. Could add a log window later.
                    pass
                    
                elif update_type == 'complete':
                    successful, failed = update[1], update[2]
                    self.progress_var.set(100)
                    self.progress_label.config(text="Complete!")
                    
                    if failed == 0:
                        self.status_label.config(text=f"✅ All {successful} audiobook(s) processed successfully!", foreground="green")
                        messagebox.showinfo("Processing Complete", f"Successfully processed {successful} audiobook(s)!")
                    else:
                        self.status_label.config(text=f"⚠️ Processing complete: {successful} successful, {failed} failed", foreground="orange")
                        messagebox.showwarning("Processing Complete", f"Processing finished:\n✅ Successful: {successful}\n❌ Failed: {failed}")
                    
                    self.reset_ui_state()
                    
        except Exception as e:
            print(f"Error processing queue: {e}")
        
        # Schedule next update
        self.root.after(100, self.process_queue)

def main():
    """Main entry point for the GUI application"""
    # Create the main window
    root = tk.Tk()
    
    # Set up ttk styling
    style = ttk.Style()
    
    # Try to use a modern theme
    available_themes = style.theme_names()
    if 'aqua' in available_themes:  # macOS
        style.theme_use('aqua')
    elif 'vista' in available_themes:  # Windows
        style.theme_use('vista')
    elif 'clam' in available_themes:  # Cross-platform
        style.theme_use('clam')
    
    # Configure custom styles
    style.configure('Accent.TButton', foreground='white')
    if 'aqua' not in available_themes:  # Only set background if not on macOS
        style.configure('Accent.TButton', background='#007AFF')
    
    # Create the application
    app = AudioBookBinderGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.processing_thread and app.processing_thread.is_alive():
            if messagebox.askokcancel("Quit", "Processing is still running. Do you want to quit?"):
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()

# AudioBook Binder - Enhanced Edition

A powerful, feature-rich Python script that converts MP3 audiobooks to M4B format with full metadata preservation, interactive settings, and intelligent processing.

## ✨ New Enhanced Features

### 🎛️ Interactive Menu System
- **Settings Menu**: Customizable bitrate, processing modes, and advanced options
- **Discovery Preview**: See exactly what will be processed before starting
- **Real-time Configuration**: All settings saved and persistent across sessions

### ⚡ Smart Processing
- **Fast Mode**: Stream copy when possible (no re-encoding for compatible files)
- **Quality Mode**: Ensures optimal audio quality with intelligent bitrate handling
- **Multi-core Support**: Utilizes all CPU cores for faster processing

### 🔧 Advanced Settings
- **Bitrate Options**: 64, 96, 128, 192, 256, 320 kbps (192 kbps default)
- **Processing Modes**: Fast (stream copy) vs Quality (re-encode when needed)
- **Chapter Naming**: Auto, Sequential, or Filename-based
- **Sanitization Levels**: Basic or Aggressive filename cleaning
- **Cover Art Quality**: Original or Optimized for smaller file sizes

## 🚀 Key Features

- **Multi-structure Support**: Single-folder and multi-disc audiobook structures
- **Natural Sorting**: Proper alphanumeric sorting (Chapter1, Chapter2, Chapter10)
- **Metadata Preservation**: Extracts and preserves artist, title, genre, year
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
└── J.K. Rowling - Harry Potter Book 1/
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
- **Fast Mode**: Stream copy when input ≤ target bitrate (no quality loss)
- **Quality Mode**: Re-encode only when necessary

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
- **Fast Mode**: Stream copy when possible, minimal processing time
- **Quality Mode**: Ensures consistent quality, comprehensive metadata handling

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
  "verbose_logging": false
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

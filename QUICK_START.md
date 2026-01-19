# Quick Start Guide - Enhanced Edition

## 🚀 TL;DR - Get Started in 3 Steps

1. **Put your audiobooks in folders:**
   ```
   AudioBooks/
   ├── Author Name - Book 1/
   │   ├── chapter01.mp3
   │   ├── chapter02.mp3
   │   └── cover.jpg
   └── Another Author - Book 2/
       ├── 01-intro.mp3
       └── 02-story.mp3
   ```

2. **Run the script (Interactive Mode):**
   ```bash
   cd AudioBooks
   python3 /path/to/audiobook_binder.py
   ```

3. **Follow the interactive menu:**
   - 📊 **Preview Discovery**: See what will be processed
   - ⚙️ **Adjust Settings**: Bitrate, processing mode, etc.
   - 🚀 **Start Processing**: Convert to M4B with one click

## 🎯 Interactive Menu Features

### Main Settings Menu
```
📚 AudioBook Binder - Settings
==================================================
Current Settings:
  Max Bitrate: 192 kbps
  Processing Mode: Quality Mode
  Parallel book processing: Enabled
  Remove Commas: Yes
  Sanitization: Aggressive

Options:
1. Change max bitrate (64-320 kbps)
2. Toggle processing mode (Fast/Quality)  
3. Advanced settings
4. Preview discovery results
5. Preview discovery results ← SEE BEFORE PROCESSING!
6. Start processing
7. Exit
```

### Discovery Preview Example
```
🔍 Discovery Results
==================================================

📚 Ben Greenfield - Beyond Training
   📁 Files: 34 MP3s (545.5 MB)
   🎵 Format: MP3, 89 kbps, mono
   📖 Metadata: Ben Greenfield | Beyond Training...
   🖼️  Cover Art: Embedded
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

## ⚡ Quick Batch Mode

For power users who want to skip menus:

```bash
# Fast processing (stream copy when possible)
python3 audiobook_binder.py --batch --fast

# Quality processing with specific bitrate
python3 audiobook_binder.py --batch --bitrate 128

# Process specific directory
python3 audiobook_binder.py /path/to/audiobooks --batch
```

## 💡 Smart Processing Modes

### 🏃‍♂️ Fast Mode
- **Stream copy** when input quality is acceptable
- **No re-encoding** = lightning fast processing
- **Example**: 15-file audiobook processed in 1.5 seconds!

### 🎯 Quality Mode  
- **Intelligent re-encoding** only when needed
- **Never upscales** quality (smart bitrate handling)
- **Comprehensive metadata** preservation

## 📁 Multi-Disc Support

The script automatically handles complex structures:

```
AudioBooks/
└── Epic Series Book 1/
    ├── Disc1/
    │   ├── track01.mp3
    │   └── track02.mp3
    ├── Disc2/
    │   ├── track01.mp3
    │   └── track02.mp3
    └── cover.jpg
    
→ Creates: "Author Name - Epic Series Book 1.m4b"
   With chapters: "Disc 1 - track01", "Disc 1 - track02", etc.
```

## 🎨 Enhanced Features

### ✨ What's New
- **🎛️ Interactive Menus** - Visual settings and discovery preview
- **⚡ Fast Mode** - Stream copy for compatible files (seconds vs minutes!)
- **🖼️ Cover Art Verification** - Confirms artwork was properly embedded
- **🧹 Smart Sanitization** - Removes commas, special chars from filenames
- **🚀 Parallel book processing** - Multiple books processed concurrently for faster batch runs
- **📊 Progress Tracking** - Real-time updates with time estimates
- **⚙️ Persistent Settings** - Your preferences saved between sessions

### 📝 Clean Filenames
Input: `"Author, Name - Book: Part 1 (Special Edition)"`
Output: `"Author Name - Book Part 1 Special Edition.m4b"`

### 🎯 Perfect Quality
- **192 kbps max** (perfect for audiobooks)
- **Never upscales** (maintains original quality when lower)
- **Smart encoding** (AAC for M4B compatibility)

## 🔧 Troubleshooting

### Quick Fixes
```bash
# Install dependencies
brew install ffmpeg
pip3 install mutagen

# Test the script
python3 audiobook_binder.py --help

# Verbose mode for debugging
python3 audiobook_binder.py --verbose
```

## 🎉 That's It!

Your audiobooks are now professional M4B files with:
- ✅ **All chapters combined** into single files
- ✅ **Perfect metadata** (artist as album artist too!)
- ✅ **Cover art embedded** and verified
- ✅ **Smart chapter markers** for easy navigation
- ✅ **Optimized quality** (never unnecessarily large)
- ✅ **Clean filenames** (no problematic characters)

Perfect for any audiobook player! 🎧

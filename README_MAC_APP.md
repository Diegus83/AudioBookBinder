# AudioBook Binder - Standalone Mac App

🎉 **Your AudioBook Binder is now available as a standalone Mac application!**

## 📱 What You Get

- **AudioBookBinder.app** - A complete standalone Mac application (41.2 MB)
- **No Python installation required** - All dependencies are bundled
- **Double-click to run** - Works like any other Mac app
- **Terminal-based interface** - Familiar command-line experience in Terminal

## 🚀 Quick Start

1. **Locate the app**: `dist/AudioBookBinder.app`
2. **Double-click** the app to launch
3. **Terminal will open** with the AudioBook Binder interface
4. **Follow the on-screen menu** to process your audiobooks

## ⚠️ Prerequisites

The app requires **FFmpeg** to be installed on the target Mac:

```bash
# Install FFmpeg via Homebrew (recommended)
brew install ffmpeg

# Or via MacPorts
sudo port install ffmpeg
```

**The app will check for FFmpeg and provide clear instructions if it's missing.**

## 📋 How It Works

### For End Users:
1. **Double-click** `AudioBookBinder.app`
2. **Terminal opens** automatically with the application
3. **Interactive menu** appears with options:
   - Press **Enter** to start processing (default)
   - Choose numbered options for settings
4. **Select your audiobook folder** when prompted
5. **Processing begins** automatically
6. **M4B files** are saved to the Output folder

### For Developers/Advanced Users:
- The original `audiobook_binder.py` script remains unchanged
- You can still use the Python script directly
- The app is just a packaged version of the same functionality

## 📁 Distribution

### Single User:
- Copy `AudioBookBinder.app` to Applications folder
- Right-click → Open (first time only for unsigned apps)

### Multiple Users:
- Create a disk image (DMG) for easy distribution:
```bash
# Create a DMG (optional)
hdiutil create -volname "AudioBook Binder" -srcfolder dist/AudioBookBinder.app -ov -format UDZO AudioBookBinder.dmg
```

## 🔧 Technical Details

| Aspect | Details |
|--------|---------|
| **Size** | 41.2 MB (includes Python runtime + all dependencies) |
| **Python Version** | Bundled (users don't need Python installed) |
| **Dependencies** | All included (mutagen, PIL, etc.) |
| **macOS Version** | Requires macOS 10.13+ (High Sierra or newer) |
| **Architecture** | Universal (Intel + Apple Silicon) |
| **Interface** | Terminal-based (opens Terminal window) |

## 🛠️ Rebuilding the App

To rebuild the app after making changes to the Python script:

```bash
# 1. Activate virtual environment
source audiobook_env/bin/activate

# 2. Run the build script
python3 build_app.py

# 3. New app will be in dist/AudioBookBinder.app
```

## 🔒 Security Notes

- The app is **unsigned** (requires right-click → Open first time)
- For wider distribution, consider:
  - Apple Developer Account for code signing
  - Notarization for Gatekeeper approval
  - App Store distribution (requires additional setup)

## 🆚 App vs. Script Comparison

| Feature | Mac App | Python Script |
|---------|---------|---------------|
| **Ease of Use** | Double-click to run | Requires terminal commands |
| **Python Required** | ❌ No | ✅ Yes |
| **Dependencies** | ❌ Bundled | ✅ Must install separately |
| **File Size** | 41.2 MB | ~50 KB |
| **Functionality** | 100% identical | 100% identical |
| **Updates** | Rebuild required | Edit script directly |

## 🐛 Troubleshooting

### App Won't Open
```
"AudioBookBinder.app" cannot be opened because the developer cannot be verified.
```
**Solution**: Right-click the app → "Open" → "Open" (first time only)

### FFmpeg Not Found
```
❌ Error: FFmpeg is not installed or not in PATH
```
**Solution**: Install FFmpeg via Homebrew: `brew install ffmpeg`

### Terminal Closes Immediately
- Check Console.app for error messages
- Ensure the app has proper permissions
- Try running from a different location

### Permission Issues
```
Operation not permitted
```
**Solution**: Grant Terminal "Full Disk Access" in System Preferences → Security & Privacy

## 📞 Support

- **Original Script Issues**: Use the Python script directly for debugging
- **App-Specific Issues**: Check the build logs in `build_app.py`
- **FFmpeg Issues**: Verify FFmpeg installation with `ffmpeg -version`

## 🎯 Perfect For

- **End users** who want a simple double-click experience
- **Distribution** to users without technical knowledge
- **Backup solution** that doesn't require Python environment
- **Production environments** where Python isn't available

---

**The original Python script remains fully functional and unchanged!**  
This Mac app is simply a convenient packaged version. ✨

#!/usr/bin/env python3
"""
AudioBook Binder - Mac App Builder

This script builds a standalone Mac application using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_command(cmd):
    """Check if a command is available in PATH"""
    try:
        subprocess.run([cmd, '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{colors.get(status, '')}{status}: {message}{colors['RESET']}")

def main():
    print("🚀 AudioBook Binder - Mac App Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("audiobook_binder.py").exists():
        print_status("audiobook_binder.py not found! Please run this from the project directory.", "ERROR")
        sys.exit(1)
    
    if not Path("audiobook_binder.spec").exists():
        print_status("audiobook_binder.spec not found! Please ensure the spec file exists.", "ERROR")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status("Virtual environment not detected. Please activate audiobook_env first:", "WARNING")
        print("    source audiobook_env/bin/activate")
        sys.exit(1)
    
    # Check dependencies
    print_status("Checking dependencies...")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print_status(f"PyInstaller {PyInstaller.__version__} found", "SUCCESS")
    except ImportError:
        print_status("PyInstaller not found. Installing...", "WARNING")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Check FFmpeg
    if check_command("ffmpeg"):
        print_status("FFmpeg found in system PATH", "SUCCESS")
    else:
        print_status("FFmpeg not found in PATH", "WARNING")
        print("  The app will check for FFmpeg at runtime and provide installation instructions.")
        print("  Users will need to install FFmpeg separately (e.g., via Homebrew).")
    
    # Check FFprobe
    if check_command("ffprobe"):
        print_status("FFprobe found in system PATH", "SUCCESS")
    else:
        print_status("FFprobe not found in PATH", "WARNING")
    
    # Clean previous builds
    print_status("Cleaning previous builds...")
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print_status(f"Removed {dir_name}/", "INFO")
    
    # Build the application
    print_status("Building Mac application...", "INFO")
    try:
        # Use PyInstaller with our spec file
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",  # Clean PyInstaller cache
            "audiobook_binder.spec"
        ], check=True, capture_output=True, text=True)
        
        print_status("Build completed successfully!", "SUCCESS")
        
        # Check if app was created
        app_path = Path("dist/AudioBookBinder.app")
        if app_path.exists():
            print_status(f"Application created: {app_path}", "SUCCESS")
            
            # Get app size
            def get_size(path):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                return total_size
            
            app_size_mb = get_size(app_path) / (1024 * 1024)
            print_status(f"App size: {app_size_mb:.1f} MB", "INFO")
            
        else:
            print_status("App was not created in expected location", "ERROR")
            return False
            
    except subprocess.CalledProcessError as e:
        print_status("Build failed!", "ERROR")
        print(f"Error output:\n{e.stderr}")
        return False
    
    # Success message
    print("\n" + "=" * 50)
    print_status("🎉 Mac App Build Complete!", "SUCCESS")
    print("\n📱 Your application is ready:")
    print(f"   Location: dist/AudioBookBinder.app")
    print(f"   Size: {app_size_mb:.1f} MB")
    
    print("\n📋 Next Steps:")
    print("   1. Test the app by double-clicking AudioBookBinder.app")
    print("   2. The app will open Terminal and run the audiobook binder")
    print("   3. Users will need FFmpeg installed (brew install ffmpeg)")
    print("   4. You can distribute the .app file to other Mac users")
    
    print("\n💡 Tips:")
    print("   • The app includes all Python dependencies")
    print("   • FFmpeg must be installed separately by users")
    print("   • The app will provide clear error messages if FFmpeg is missing")
    print("   • The original Python script remains unchanged")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

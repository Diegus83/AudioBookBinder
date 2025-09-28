# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Get the current directory
current_dir = Path.cwd()

a = Analysis(
    ['audiobook_binder.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('QUICK_START.md', '.'),
    ],
    hiddenimports=[
        'mutagen',
        'mutagen.mp3',
        'mutagen.id3',
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'PIL.ImageEnhance',
        'pathlib',
        'concurrent.futures',
        'threading',
        'tempfile',
        'uuid',
        'random'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AudioBookBinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for terminal-based interface
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AudioBookBinder',
)

app = BUNDLE(
    coll,
    name='AudioBookBinder.app',
    icon=None,  # We can add an icon later
    bundle_identifier='com.audiobookbinder.app',
    version='2.2.0',
    info_plist={
        'CFBundleName': 'AudioBook Binder',
        'CFBundleDisplayName': 'AudioBook Binder',
        'CFBundleVersion': '2.2.0',
        'CFBundleShortVersionString': '2.2.0',
        'CFBundleIdentifier': 'com.audiobookbinder.app',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleExecutable': 'AudioBookBinder',
        'CFBundlePackageType': 'APPL',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.utilities',
        'LSBackgroundOnly': False,  # Explicitly disable background-only mode
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Folder',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.folder'],
                'LSHandlerRank': 'Alternate'
            }
        ]
    },
)

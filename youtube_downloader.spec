# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['youtube_downloader.py'],  # Nome do arquivo principal (ajuste se necessário)
    pathex=[],
    binaries=[
        ('yt-dlp.exe', '.'),     # inclui yt-dlp na mesma pasta
        ('ffmpeg.exe', '.'),     # inclui ffmpeg na mesma pasta
    ],
    datas=[],
    hiddenimports=collect_submodules('tkinter'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='YouTube Downloader',  # Nome do executável
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # esconde o cmd
    icon='icon.ico' if os.path.exists('icon.ico') else None  # opcional: ícone .ico
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='YouTube Downloader'  # Nome da pasta da aplicação
)
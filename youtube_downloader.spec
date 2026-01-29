# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['youtube_downloader.py'],  # certifique-se que o nome do arquivo está correto aqui
    pathex=[],
    binaries=[
        ('yt-dlp.exe', '.'),     # Motor de download
        ('ffmpeg.exe', '.'),     # Motor de conversão/fusão de áudio e vídeo
        ('deno.exe', '.'),       # NOVO: Motor JS para contornar o Erro 403 (SABR)
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
    name='YouTube Downloader',  # Nome do arquivo .exe final
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Mantido False para não abrir o terminal preto
    icon='icon.ico' if os.path.exists('icon.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='YouTube Downloader Pro'  # Nome da pasta que será gerada em /dist
)

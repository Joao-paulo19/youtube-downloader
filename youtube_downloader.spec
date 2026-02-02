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
        ('deno.exe', '.'),       # Motor JS para PoToken (Camada 1 - Anonimato)
    ],
    datas=[],
    hiddenimports=[
        # Tkinter (interface gráfica)
        *collect_submodules('tkinter'),
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        
        # Requests (ESSENCIAL - busca de proxies)
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        
        # Urllib (backup para busca de proxies)
        'urllib',
        'urllib.request',
        'urllib.error',
        'urllib.parse',
        
        # Threading e multiprocessing
        'threading',
        'queue',
        
        # JSON para parsing de tokens
        'json',
        
        # Subprocess para executar comandos
        'subprocess',
        
        # Sistema operacional
        'os',
        'sys',
        'pathlib',
        
        # Datetime
        'datetime',
        'time',
        
        # Regex
        're',
        
        # Random
        'random',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Excluir módulos pesados não utilizados
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ],
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
    name='YouTube Downloader'  # Nome da pasta que será gerada em /dist
)

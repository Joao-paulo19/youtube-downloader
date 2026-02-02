# SOLUÇÃO: Instalar dependências no Python 3.13 (que o PyInstaller está usando)

import subprocess
import sys

print("=" * 70)
print("INSTALANDO NO PYTHON CORRETO (3.13)")
print("=" * 70)
print(f"\nPython atual: {sys.version}")
print(f"Executável: {sys.executable}")

# Usar o python.exe do Python313 explicitamente
python_correto = r"C:\Python313\python.exe"

dependencias = [
    'requests',
    'urllib3',
    'certifi',
    'charset-normalizer',
    'idna',
]

print(f"\n{'='*70}")
print("INSTALANDO DEPENDÊNCIAS...")
print(f"{'='*70}\n")

for dep in dependencias:
    print(f"[{dependencias.index(dep) + 1}/{len(dependencias)}] Instalando {dep} no Python 3.13...")
    try:
        subprocess.check_call([python_correto, '-m', 'pip', 'install', dep])
        print(f"✓ {dep} instalado!")
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao instalar {dep}: {e}")

print(f"\n{'='*70}")
print("VERIFICANDO INSTALAÇÃO...")
print(f"{'='*70}\n")

for dep in dependencias:
    try:
        subprocess.check_call([python_correto, '-m', 'pip', 'show', dep],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        print(f"✓ {dep} está instalado corretamente no Python 3.13")
    except subprocess.CalledProcessError:
        print(f"✗ {dep} NÃO está instalado no Python 3.13")

print(f"\n{'='*70}")
print("CONCLUÍDO!")
print(f"{'='*70}")
print("\nAgora execute:")
print("1. pyinstaller youtube_downloader.spec")

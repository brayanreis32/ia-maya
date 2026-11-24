"""Baixa os modelos offline: Vosk (palavra de ativação) e a voz do Piper em português."""

import os
import subprocess
import sys
import urllib.request
import zipfile

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelos")
VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
VOSK_PASTA = os.path.join(PASTA, "vosk-model-small-pt-0.3")
VOZ = "pt_BR-faber-medium"

os.makedirs(PASTA, exist_ok=True)

if os.path.isdir(VOSK_PASTA):
    print("Vosk já está baixado.")
else:
    print("Baixando o Vosk em português (~30 MB)...")
    arquivo_zip = os.path.join(PASTA, "vosk.zip")
    urllib.request.urlretrieve(VOSK_URL, arquivo_zip)
    with zipfile.ZipFile(arquivo_zip) as z:
        z.extractall(PASTA)
    os.remove(arquivo_zip)
    print("Vosk pronto.")

if os.path.exists(os.path.join(PASTA, VOZ + ".onnx")):
    print("Voz do Piper já está baixada.")
else:
    print(f"Baixando a voz {VOZ} (~60 MB)...")
    subprocess.check_call([sys.executable, "-m", "piper.download_voices", VOZ, "--download-dir", PASTA])
    print("Voz pronta.")

print("\nTudo certo! O Whisper é baixado sozinho na primeira vez que a Maya ouvir você.")

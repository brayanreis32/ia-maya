"""
Liga o app da Maya no iPhone usando o Tailscale (rede privada e gratuita entre os seus aparelhos).

Antes: instale o Tailscale no PC (https://tailscale.com/download/windows) e no iPhone (App Store),
e entre com a MESMA conta nos dois.

    python configurar_celular.py
"""

import json
import os
import shutil
import subprocess
import sys

import config

PORTA = getattr(config, "PORTA_CELULAR", 8765)


def achar_tailscale():
    caminho = shutil.which("tailscale")
    if caminho:
        return caminho
    padrao = r"C:\Program Files\Tailscale\tailscale.exe"
    return padrao if os.path.exists(padrao) else None


def rodar(*args):
    return subprocess.run([TAILSCALE, *args], capture_output=True, text=True, timeout=60)


TAILSCALE = achar_tailscale()
if not TAILSCALE:
    sys.exit("Não achei o Tailscale. Instale em https://tailscale.com/download/windows e rode de novo.")

status = rodar("status", "--json")
if status.returncode != 0:
    sys.exit("O Tailscale não está conectado. Abra o Tailscale (ícone perto do relógio) e faça login.")
nome = json.loads(status.stdout).get("Self", {}).get("DNSName", "").rstrip(".")
if not nome:
    sys.exit("Não consegui descobrir o nome deste PC no Tailscale. Ele está logado?")

print("Ligando o acesso seguro (HTTPS) do celular até a Maya...")
print("Se aparecer um link abaixo, abra-o no navegador e ative o HTTPS. Depois volte aqui e espere.\n")
# Sem capturar a saída: assim o link para ativar o HTTPS aparece na tela
servir = subprocess.run([TAILSCALE, "serve", "--bg", str(PORTA)])
if servir.returncode != 0:
    sys.exit("\nNão deu certo. Ative o HTTPS pelo link acima (se apareceu) e rode este script de novo.")

endereco = f"https://{nome}"
print(f"\nPronto! O app da Maya está em:\n\n    {endereco}\n")
print("No iPhone (com o Tailscale ligado), abra esse endereço no Safari.")
print("Depois toque em Compartilhar > 'Adicionar à Tela de Início' para instalar o app.")
print("Isso só precisa ser feito uma vez: o endereço continua valendo mesmo depois de reiniciar o PC.")

try:
    import qrcode

    arquivo = os.path.abspath("qrcode_celular.png")
    qrcode.make(endereco).save(arquivo)
    print("\nAbrindo um QR code: aponte a câmera do iPhone para ele.")
    os.startfile(arquivo)
except Exception:
    pass

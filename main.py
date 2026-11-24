"""
Maya - assistente de voz.

    python main.py            modo voz: diga "Maya" e depois o seu pedido
    python main.py --texto    modo texto: digite os pedidos (bom para testar sem microfone)
"""

import os
import sys

# Roda sempre a partir da pasta do projeto (importante quando inicia junto com o Windows)
PASTA = os.path.dirname(os.path.abspath(__file__))
os.chdir(PASTA)
sys.path.insert(0, PASTA)

# Em segundo plano (pythonw) não existe janela: as mensagens vão para maya.log
if sys.stdout is None or sys.stderr is None:
    log = open(os.path.join(PASTA, "maya.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(PASTA, ".env"))

import config  # noqa: E402
from maya.cerebro import Cerebro  # noqa: E402
from maya.falar import bipe, falar  # noqa: E402


def modo_texto(cerebro):
    print("Modo texto. Digite um pedido (ou 'sair').")
    while True:
        try:
            pedido = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pedido.lower() in ("sair", "exit", "quit"):
            break
        if pedido:
            falar(cerebro.responder(pedido))


def modo_voz(cerebro):
    from maya.ouvir import esperar_palavra_ativacao, gravar_pedido, transcrever

    falar("Oi, eu sou a Maya. É só me chamar.")
    while True:
        print(f"\n[ouvindo... diga '{config.PALAVRAS_ATIVACAO[0]}']")
        esperar_palavra_ativacao()
        bipe()
        print("[pode falar]")
        audio = gravar_pedido()
        if audio is None:
            print("[não ouvi nada]")
            continue
        pedido = transcrever(audio)
        if not pedido:
            falar("Não entendi, pode repetir?")
            continue
        print(f"Você: {pedido}")
        falar(cerebro.responder(pedido))


def main():
    print(f"Maya iniciando (cérebro: {config.CEREBRO})")
    cerebro = Cerebro()
    try:
        if "--texto" in sys.argv:
            modo_texto(cerebro)
        else:
            modo_voz(cerebro)
    except KeyboardInterrupt:
        pass
    print("Até mais!")


if __name__ == "__main__":
    main()

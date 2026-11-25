"""
Maya - assistente de voz.

    python main.py            modo voz: diga "Maya" e depois o seu pedido
    python main.py --texto    modo texto: digite os pedidos (bom para testar sem microfone)

Para rodar escondida (sem a tela preta), use "pythonw main.py" ou o atalho
criado por instalar_inicializacao.py. Para fechar: ícone da Maya perto do relógio > Sair.
"""

import os
import socket
import sys
import threading
import traceback

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
from maya import estado, ferramentas, lembretes  # noqa: E402
from maya.cerebro import Cerebro  # noqa: E402
from maya.falar import bipe, falar  # noqa: E402


def sair():
    print("Até mais!")
    os._exit(0)  # encerra tudo de uma vez (microfone, animação, ícone)


def ja_esta_aberta():
    """Impede que duas Mayas fiquem ouvindo ao mesmo tempo."""
    global _trava_instancia
    _trava_instancia = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _trava_instancia.bind(("127.0.0.1", 47811))
        return False
    except OSError:
        return True


def icone_bandeja():
    """Ícone perto do relógio, com a opção de fechar a Maya."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        return
    imagem = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(imagem)
    desenho.ellipse((4, 4, 60, 60), fill=(29, 78, 216))
    desenho.ellipse((16, 12, 44, 40), fill=(147, 197, 253))
    menu = pystray.Menu(
        pystray.MenuItem(f"Maya ativa (cérebro: {config.CEREBRO})", None, enabled=False),
        pystray.MenuItem("Sair", lambda icone, item: (icone.stop(), sair())),
    )
    icone = pystray.Icon("maya", imagem, "Maya - diga \"Maya\" para chamar", menu)
    threading.Thread(target=icone.run, daemon=True).start()


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
            estado.mudar("pensando", pedido)
            resposta = cerebro.responder(pedido)
            falar(resposta)
            estado.mudar("oculto")
            if ferramentas.pedido_para_fechar:
                break
    sair()


def modo_voz(cerebro):
    from maya.ouvir import esperar_palavra_ativacao, gravar_pedido, transcrever

    conversa_continua = getattr(config, "CONVERSA_CONTINUA", True)
    falar("Oi, eu sou a Maya. É só me chamar.")
    continuar = False  # depois de responder, ouve mais um pouco sem precisar dizer "Maya"
    while True:
        try:
            if not continuar:
                estado.mudar("oculto")
                print(f"\n[ouvindo... diga '{config.PALAVRAS_ATIVACAO[0]}']")
                esperar_palavra_ativacao()
                estado.mudar("ouvindo", "")
                bipe()
                print("[pode falar]")
                audio = gravar_pedido()
            else:
                estado.mudar("ouvindo", "")
                print("[continuo ouvindo...]")
                audio = gravar_pedido(espera_inicial=4)
            continuar = False
            if audio is None:
                print("[não ouvi nada]")
                continue

            estado.mudar("pensando", "")
            pedido = transcrever(audio)
            if not pedido:
                falar("Não entendi, pode repetir?")
                continue
            print(f"Você: {pedido}")
            estado.mudar("pensando", pedido)
            falar(cerebro.responder(pedido))
            if ferramentas.pedido_para_fechar:
                sair()
            continuar = conversa_continua
        except Exception:
            traceback.print_exc()
            falar("Ops, tive um problema. Tente de novo.")


def main():
    if ja_esta_aberta():
        print("A Maya já está aberta (veja o ícone perto do relógio).")
        return
    print(f"Maya iniciando (cérebro: {config.CEREBRO})")
    cerebro = Cerebro("pc")
    assistente = modo_texto if "--texto" in sys.argv else modo_voz
    icone_bandeja()

    # Lembretes salvos em arquivo: na hora certa, ela fala no PC (e avisa o celular, se ligado)
    lembretes.ao_disparar(lambda texto: falar(f"Lembrete: {texto}"))
    lembretes.iniciar()

    # App do celular (conversa separada da do PC, mas com a mesma memória e lembretes)
    if getattr(config, "APP_CELULAR", True):
        try:
            from maya import servidor

            servidor.iniciar(Cerebro("celular"))
        except Exception as erro:
            print(f"[aviso] App do celular desligado: {erro}")

    try:
        estilo = getattr(config, "ANIMACAO", "avatar")
        if estilo == "nenhuma":
            raise RuntimeError("desligada no config.py")
        if estilo == "bolha":
            from maya.animacao import Animacao
        else:
            from maya.avatar import Avatar as Animacao

        animacao = Animacao()
    except Exception as erro:  # sem tela (ou sem tkinter): funciona sem animação
        print(f"[aviso] Animação desligada: {erro}")
        try:
            assistente(cerebro)
        except KeyboardInterrupt:
            sair()
        return

    # A animação precisa da thread principal; o assistente roda numa thread separada
    threading.Thread(target=assistente, args=(cerebro,), daemon=True).start()
    try:
        animacao.rodar()
    except KeyboardInterrupt:
        pass
    sair()


if __name__ == "__main__":
    main()

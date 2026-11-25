"""Estado atual da Maya, compartilhado entre o assistente e a animação na tela."""

import time

# "oculto" | "ouvindo" | "pensando" | "falando"
atual = "oculto"
texto = ""
nivel = 0.0  # volume de 0 a 1 (microfone ao ouvir, voz dela ao falar)
operando = False  # True enquanto ela mexe no mouse/teclado (a animação se esconde)

# Envelope de volume da fala, para a bolha pulsar junto com a voz
_envelope = None
_envelope_passo = 0.03
_envelope_inicio = 0.0


def mudar(novo, novo_texto=None):
    global atual, texto, nivel
    atual = novo
    nivel = 0.0
    if novo_texto is not None:
        texto = novo_texto


def comecar_fala(envelope, passo):
    global _envelope, _envelope_passo, _envelope_inicio
    _envelope, _envelope_passo, _envelope_inicio = envelope, passo, time.time()


def terminar_fala():
    global _envelope
    _envelope = None


def nivel_atual():
    """Volume para desenhar agora. Ao falar, segue o áudio que está tocando."""
    if atual == "falando":
        if _envelope is None:  # voz do Windows: não sabemos o volume, então pulsa sozinha
            return 0.35 + 0.25 * abs(((time.time() * 4) % 2) - 1)
        i = int((time.time() - _envelope_inicio) / _envelope_passo)
        return float(_envelope[i]) if 0 <= i < len(_envelope) else 0.0
    return nivel

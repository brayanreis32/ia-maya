"""Microfone: espera a palavra de ativação (Vosk) e transcreve o pedido (faster-whisper)."""

import json
import queue
import threading
import time

import numpy as np
import sounddevice as sd

import config
from maya import estado

TAXA = 16000  # Vosk e Whisper trabalham com 16 kHz mono
PASTA_VOSK = "modelos/vosk-model-small-pt-0.3"

_whisper = None
_modelo_vosk = None
_trava_whisper = threading.Lock()


def esperar_palavra_ativacao():
    """Fica ouvindo até alguém dizer "Maya". Usa pouquíssima CPU e funciona offline."""
    global _modelo_vosk
    from vosk import KaldiRecognizer, Model, SetLogLevel

    if _modelo_vosk is None:
        SetLogLevel(-1)
        _modelo_vosk = Model(PASTA_VOSK)
    modelo = _modelo_vosk
    # Gramática restrita: o reconhecedor só tenta achar as palavras de ativação.
    gramatica = json.dumps(config.PALAVRAS_ATIVACAO + ["[unk]"])
    reconhecedor = KaldiRecognizer(modelo, TAXA, gramatica)

    fila = queue.Queue()

    def callback(dados, frames, tempo, status):
        fila.put(bytes(dados))

    with sd.RawInputStream(samplerate=TAXA, blocksize=4000, dtype="int16", channels=1, callback=callback):
        while True:
            bloco = fila.get()
            if reconhecedor.AcceptWaveform(bloco):
                texto = json.loads(reconhecedor.Result()).get("text", "")
            else:
                texto = json.loads(reconhecedor.PartialResult()).get("partial", "")
            if any(p in texto.split() for p in config.PALAVRAS_ATIVACAO):
                return


def gravar_pedido(espera_inicial=5):
    """Grava até você ficar em silêncio. Devolve o áudio como array float32,
    ou None se ninguém falar nada nos primeiros `espera_inicial` segundos."""
    blocos = []
    duracao_bloco = 0.1
    tamanho = int(TAXA * duracao_bloco)
    silencio = 0.0
    falou = False
    inicio = time.time()

    with sd.InputStream(samplerate=TAXA, channels=1, dtype="int16") as stream:
        while time.time() - inicio < config.TEMPO_MAXIMO_FALA:
            bloco, _ = stream.read(tamanho)
            blocos.append(bloco.copy())
            volume = np.sqrt(np.mean(bloco.astype(np.float32) ** 2))
            estado.nivel = min(1.0, volume / 3000)  # faz a bolha crescer com a sua voz
            if volume > config.LIMIAR_SILENCIO:
                falou = True
                silencio = 0.0
            else:
                silencio += duracao_bloco
            # Para quando você falou e depois ficou em silêncio,
            # ou se não disse nada no começo.
            if (falou and silencio >= config.SILENCIO_PARA_PARAR) or (not falou and silencio >= espera_inicial):
                break

    if not falou:
        return None
    audio = np.concatenate(blocos).flatten().astype(np.float32) / 32768.0
    return audio


def transcrever(audio):
    """Transforma o áudio em texto com o Whisper (roda no próprio notebook).
    Aceita o áudio do microfone (array) ou um arquivo de áudio (ex.: gravado no iPhone)."""
    global _whisper
    with _trava_whisper:  # PC e celular podem pedir ao mesmo tempo
        if _whisper is None:
            from faster_whisper import WhisperModel

            print("[carregando o Whisper, só demora na primeira vez...]")
            _whisper = WhisperModel(config.MODELO_WHISPER, device="cpu", compute_type="int8")
        segmentos, _ = _whisper.transcribe(audio, language="pt", beam_size=1, vad_filter=True)
        return " ".join(s.text for s in segmentos).strip()

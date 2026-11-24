"""Texto para voz: Piper (offline, voz pt-BR). Se o Piper falhar, usa a voz do Windows."""

import os
import tempfile
import threading
import wave

import config
from maya import estado

_voz_piper = None
_motor_windows = None
_trava = threading.Lock()  # evita duas falas ao mesmo tempo (ex.: lembrete + resposta)


def _carregar_piper():
    global _voz_piper
    if _voz_piper is None and os.path.exists(config.VOZ_PIPER):
        from piper import PiperVoice

        _voz_piper = PiperVoice.load(config.VOZ_PIPER)
    return _voz_piper


def _tocar_wav(caminho):
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    dados, taxa = sf.read(caminho, dtype="float32")
    if dados.ndim > 1:
        dados = dados.mean(axis=1)
    # Volume a cada 30 ms, para a animação pulsar junto com a voz
    passo = int(taxa * 0.03)
    blocos = len(dados) // passo
    if blocos:
        rms = np.sqrt(np.mean(dados[: blocos * passo].reshape(blocos, passo) ** 2, axis=1))
        estado.comecar_fala(np.clip(rms / (rms.max() + 1e-6) * 1.1, 0, 1), 0.03)
    sd.play(dados, taxa)
    sd.wait()
    estado.terminar_fala()


def _falar_windows(texto):
    global _motor_windows
    import pyttsx3

    if _motor_windows is None:
        try:  # a voz do Windows precisa disso quando roda fora da thread principal
            import pythoncom

            pythoncom.CoInitialize()
        except ImportError:
            pass
        _motor_windows = pyttsx3.init()
        for voz in _motor_windows.getProperty("voices"):
            if "portug" in voz.name.lower() or "brazil" in voz.name.lower() or "maria" in voz.name.lower():
                _motor_windows.setProperty("voice", voz.id)
                break
    _motor_windows.say(texto)
    _motor_windows.runAndWait()


def falar(texto):
    """Fala o texto em voz alta (e mostra na tela)."""
    texto = (texto or "").strip()
    if not texto:
        return
    print(f"Maya: {texto}")
    with _trava:
        anterior = estado.atual
        estado.mudar("falando", texto)
        try:
            _falar(texto)
        finally:
            estado.terminar_fala()
            estado.mudar(anterior)


def bipe():
    """Som curto avisando que a Maya acordou e está ouvindo."""
    import numpy as np
    import sounddevice as sd

    t = np.linspace(0, 0.15, int(22050 * 0.15), False)
    sd.play(0.3 * np.sin(2 * np.pi * 880 * t).astype("float32"), 22050)
    sd.wait()


def _falar_edge(texto):
    """Voz neural feminina da Microsoft (a mesma do Edge). Grátis, mas precisa de internet."""
    import edge_tts

    arquivo = os.path.join(tempfile.gettempdir(), "maya_fala.mp3")
    voz = getattr(config, "VOZ_EDGE", "pt-BR-FranciscaNeural")
    velocidade = getattr(config, "VELOCIDADE_VOZ", "+5%")
    edge_tts.Communicate(texto, voz, rate=velocidade).save_sync(arquivo)
    _tocar_wav(arquivo)


def _falar(texto):
    if getattr(config, "MOTOR_VOZ", "edge") == "edge":
        try:
            _falar_edge(texto)
            return
        except Exception as erro:
            print(f"[aviso] Voz online falhou ({erro}); usando a voz offline.")
    try:
        voz = _carregar_piper()
        if voz is not None:
            arquivo = os.path.join(tempfile.gettempdir(), "maya_fala.wav")
            with wave.open(arquivo, "wb") as wav:
                voz.synthesize_wav(texto, wav)
            _tocar_wav(arquivo)
            return
    except Exception as erro:
        print(f"[aviso] Piper falhou ({erro}); usando a voz do Windows.")
    try:
        _falar_windows(texto)
    except Exception as erro:
        print(f"[aviso] Não consegui falar: {erro}")

"""Texto para voz: Piper (offline, voz pt-BR). Se o Piper falhar, usa a voz do Windows."""

import os
import tempfile
import threading
import wave

import config

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
    import sounddevice as sd
    import soundfile as sf

    dados, taxa = sf.read(caminho, dtype="float32")
    sd.play(dados, taxa)
    sd.wait()


def _falar_windows(texto):
    global _motor_windows
    import pyttsx3

    if _motor_windows is None:
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
        _falar(texto)


def bipe():
    """Som curto avisando que a Maya acordou e está ouvindo."""
    import numpy as np
    import sounddevice as sd

    t = np.linspace(0, 0.15, int(22050 * 0.15), False)
    sd.play(0.3 * np.sin(2 * np.pi * 880 * t).astype("float32"), 22050)
    sd.wait()


def _falar(texto):
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

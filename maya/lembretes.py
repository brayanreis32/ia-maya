"""
Lembretes salvos em arquivo: continuam valendo mesmo se a Maya ou o PC reiniciarem.
Quando chega a hora, avisa em todos os lugares registrados (voz no PC, notificação no celular).
"""

import datetime
import json
import os
import threading
import time
import uuid

ARQUIVO = "lembretes.json"
_trava = threading.Lock()
_avisos = []  # funções chamadas com o texto do lembrete


def ao_disparar(funcao):
    """Registra um jeito de avisar (ex.: falar no PC, notificar o celular)."""
    _avisos.append(funcao)


def _ler():
    if not os.path.exists(ARQUIVO):
        return []
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _gravar(lista):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def criar(mensagem, minutos=None, data_hora=None):
    if data_hora:
        try:
            quando = datetime.datetime.strptime(data_hora.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            return "Data inválida. Use o formato AAAA-MM-DD HH:MM."
    elif minutos is not None:
        quando = datetime.datetime.now() + datetime.timedelta(minutes=float(minutos))
    else:
        return "Diga daqui a quantos minutos ou em que data e hora."
    if quando < datetime.datetime.now():
        return "Esse horário já passou."
    with _trava:
        lista = _ler()
        lista.append({"id": uuid.uuid4().hex[:6], "quando": quando.timestamp(), "mensagem": mensagem})
        _gravar(lista)
    return f"Lembrete criado para {quando:%d/%m às %H:%M}: {mensagem}."


def listar():
    with _trava:
        lista = sorted(_ler(), key=lambda l: l["quando"])
    return [
        {
            "id": l["id"],
            "quando": datetime.datetime.fromtimestamp(l["quando"]).strftime("%d/%m %H:%M"),
            "mensagem": l["mensagem"],
        }
        for l in lista
    ]


def listar_texto():
    lista = listar()
    if not lista:
        return "Não há lembretes."
    return "; ".join(f"[{l['id']}] {l['quando']}: {l['mensagem']}" for l in lista)


def cancelar(id_ou_texto):
    alvo = id_ou_texto.lower().strip()
    with _trava:
        lista = _ler()
        restantes = [l for l in lista if l["id"] != alvo and alvo not in l["mensagem"].lower()]
        _gravar(restantes)
    apagados = len(lista) - len(restantes)
    return f"Cancelei {apagados} lembrete(s)." if apagados else "Não achei esse lembrete."


def _vigiar():
    while True:
        agora = time.time()
        with _trava:
            lista = _ler()
            vencidos = [l for l in lista if l["quando"] <= agora]
            if vencidos:
                _gravar([l for l in lista if l["quando"] > agora])
        for lembrete in vencidos:
            for avisar in _avisos:
                try:
                    avisar(lembrete["mensagem"])
                except Exception as erro:
                    print(f"[aviso] Falha ao avisar lembrete: {erro}")
        time.sleep(5)


def iniciar():
    threading.Thread(target=_vigiar, daemon=True).start()

"""Memória de longo prazo: coisas sobre você que a Maya guarda num arquivo e não esquece."""

import json
import os
import threading

ARQUIVO = "memoria.json"
_trava = threading.Lock()


def _ler():
    if not os.path.exists(ARQUIVO):
        return []
    try:
        with open(ARQUIVO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _gravar(fatos):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(fatos, f, ensure_ascii=False, indent=2)


def todos():
    with _trava:
        return _ler()


def guardar(fato):
    fato = fato.strip()
    with _trava:
        fatos = _ler()
        if fato and fato not in fatos:
            fatos.append(fato)
            _gravar(fatos)
    return f"Guardei na memória: {fato}"


def esquecer(trecho):
    trecho = trecho.lower().strip()
    with _trava:
        fatos = _ler()
        restantes = [f for f in fatos if trecho not in f.lower()]
        apagados = len(fatos) - len(restantes)
        _gravar(restantes)
    return f"Apaguei {apagados} lembrança(s)." if apagados else "Não achei nada parecido na memória."


def como_texto():
    fatos = todos()
    if not fatos:
        return "Você ainda não guardou nada sobre o usuário."
    return "O que você sabe sobre o usuário (memória de longo prazo):\n" + "\n".join(f"- {f}" for f in fatos)

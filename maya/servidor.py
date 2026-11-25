"""
Servidor do app da Maya no celular.

Ele só escuta em 127.0.0.1 (o próprio PC). Quem leva o app até o iPhone, com HTTPS e de qualquer
lugar, é o Tailscale ("tailscale serve"), então só os SEUS aparelhos conseguem acessar.
"""

import asyncio
import base64
import io
import json
import os
import threading
import time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response

import config
from maya import lembretes

PASTA_APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
ARQUIVO_CHAVE = "vapid_privada.pem"
ARQUIVO_ASSINATURAS = "assinaturas_push.json"
_trava_push = threading.Lock()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
_cerebro = None
_cerebro_siri = None
_avisos_pendentes = []  # lembretes que o app mostra ao abrir (além da notificação)


# ---------------------------------------------------------------------------- notificações (Web Push)
def _chave_vapid():
    from py_vapid import Vapid01

    if not os.path.exists(ARQUIVO_CHAVE):
        chave = Vapid01()
        chave.generate_keys()
        chave.save_key(ARQUIVO_CHAVE)
    return Vapid01.from_file(ARQUIVO_CHAVE)


def _chave_publica():
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    bruto = _chave_vapid().public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(bruto).decode().rstrip("=")


def _assinaturas():
    if not os.path.exists(ARQUIVO_ASSINATURAS):
        return []
    with open(ARQUIVO_ASSINATURAS, encoding="utf-8") as f:
        return json.load(f)


def _salvar_assinaturas(lista):
    with open(ARQUIVO_ASSINATURAS, "w", encoding="utf-8") as f:
        json.dump(lista, f)


def notificar_celular(texto):
    """Manda uma notificação para o iPhone (precisa ter tocado em 'Ativar notificações' no app)."""
    from pywebpush import WebPushException, webpush

    _avisos_pendentes.append({"texto": texto, "hora": time.time()})
    with _trava_push:
        assinaturas = _assinaturas()
        validas = []
        for assinatura in assinaturas:
            try:
                webpush(
                    assinatura,
                    json.dumps({"titulo": "Maya", "texto": texto}),
                    vapid_private_key=ARQUIVO_CHAVE,
                    vapid_claims={"sub": "mailto:maya@example.com"},
                    ttl=3600,
                )
                validas.append(assinatura)
            except WebPushException as erro:
                codigo = getattr(erro.response, "status_code", None)
                if codigo not in (404, 410):  # 404/410 = o celular cancelou a assinatura
                    validas.append(assinatura)
                print(f"[aviso] Notificação falhou: {erro}")
            except Exception as erro:  # assinatura com defeito: descarta
                print(f"[aviso] Assinatura de notificação inválida: {erro}")
        if validas != assinaturas:
            _salvar_assinaturas(validas)


# ---------------------------------------------------------------------------- páginas do app
@app.get("/")
def pagina():
    return FileResponse(os.path.join(PASTA_APP, "index.html"), headers={"Cache-Control": "no-cache"})


@app.get("/sw.js")
def service_worker():
    return FileResponse(os.path.join(PASTA_APP, "sw.js"), media_type="application/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/app/{nome}")
def arquivo_app(nome: str):
    caminho = os.path.join(PASTA_APP, os.path.basename(nome))
    if not os.path.isfile(caminho):
        return Response(status_code=404)
    return FileResponse(caminho)


# ---------------------------------------------------------------------------- API
@app.post("/api/mensagem")
async def mensagem(request: Request):
    dados = await request.json()
    texto = (dados.get("texto") or "").strip()[:2000]
    if not texto:
        return JSONResponse({"erro": "Mensagem vazia."}, status_code=400)
    resposta = await asyncio.to_thread(_cerebro.responder, texto)
    return {"pedido": texto, "resposta": resposta}


@app.post("/api/siri")
async def siri(request: Request):
    """Usado pelo Atalho "Maya" do iPhone: recebe o que você ditou para a Siri e devolve
    só o texto da resposta, para a Siri ler em voz alta."""
    try:
        dados = await request.json()
        texto = (dados.get("texto") or "").strip()[:2000]
    except ValueError:
        texto = (await request.body()).decode("utf-8", "ignore").strip()[:2000]
    if not texto:
        return PlainTextResponse("Não ouvi nada. Pode repetir?")
    resposta = await asyncio.to_thread(_cerebro_siri.responder, texto)
    return PlainTextResponse(resposta)


@app.post("/api/siri/voz")
async def siri_voz(request: Request):
    """Igual ao /api/siri, mas devolve a resposta já falada com a voz da Maya (mp3),
    para o Atalho tocar com a ação "Reproduzir Som"."""
    try:
        dados = await request.json()
        texto = (dados.get("texto") or "").strip()[:2000]
    except ValueError:
        texto = (await request.body()).decode("utf-8", "ignore").strip()[:2000]
    resposta = "Não ouvi nada. Pode repetir?"
    if texto:
        resposta = await asyncio.to_thread(_cerebro_siri.responder, texto)
    audio = await _gerar_voz(resposta)
    if audio is None:  # sem a voz online: devolve o texto, para pelo menos aparecer na tela
        return PlainTextResponse(resposta)
    return Response(audio, media_type="audio/mpeg", headers={"Content-Disposition": 'inline; filename="maya.mp3"'})


@app.post("/api/audio")
async def audio(request: Request):
    """Recebe a gravação do iPhone, transcreve com o Whisper e responde."""
    from maya.ouvir import transcrever

    corpo = await request.body()
    if not corpo or len(corpo) > 15_000_000:
        return JSONResponse({"erro": "Áudio vazio ou grande demais."}, status_code=400)
    pedido = await asyncio.to_thread(transcrever, io.BytesIO(corpo))
    if not pedido:
        return {"pedido": "", "resposta": "Não entendi, pode repetir?"}
    resposta = await asyncio.to_thread(_cerebro.responder, pedido)
    return {"pedido": pedido, "resposta": resposta}


async def _gerar_voz(texto):
    """Transforma o texto na voz feminina da Maya (mp3). Devolve None se falhar."""
    import edge_tts

    comunicacao = edge_tts.Communicate(
        texto,
        getattr(config, "VOZ_EDGE", "pt-BR-FranciscaNeural"),
        rate=getattr(config, "VELOCIDADE_VOZ", "+5%"),
    )
    partes = []
    try:
        async for pedaco in comunicacao.stream():
            if pedaco["type"] == "audio":
                partes.append(pedaco["data"])
    except Exception as erro:
        print(f"[aviso] Voz para o celular falhou: {erro}")
        return None
    return b"".join(partes) or None


@app.post("/api/voz")
async def voz(request: Request):
    """Gera a fala da resposta (voz feminina) para tocar no celular."""
    texto = ((await request.json()).get("texto") or "").strip()[:1500]
    if not texto:
        return Response(status_code=400)
    audio = await _gerar_voz(texto)
    if audio is None:
        return Response(status_code=502)
    return Response(audio, media_type="audio/mpeg")


@app.get("/api/lembretes")
def ver_lembretes():
    return {"lembretes": lembretes.listar()}


@app.delete("/api/lembretes/{id_lembrete}")
def apagar_lembrete(id_lembrete: str):
    return {"resultado": lembretes.cancelar(id_lembrete)}


@app.get("/api/avisos")
def avisos(desde: float = 0):
    """Lembretes que dispararam recentemente (o app mostra na conversa)."""
    return {"avisos": [a for a in _avisos_pendentes[-20:] if a["hora"] > desde], "agora": time.time()}


@app.get("/api/push/chave")
def chave_push():
    return {"chave": _chave_publica()}


@app.post("/api/push/assinar")
async def assinar_push(request: Request):
    assinatura = await request.json()
    if not isinstance(assinatura, dict) or "endpoint" not in assinatura:
        return JSONResponse({"erro": "Assinatura inválida."}, status_code=400)
    with _trava_push:
        lista = [a for a in _assinaturas() if a.get("endpoint") != assinatura["endpoint"]]
        lista.append(assinatura)
        _salvar_assinaturas(lista)
    return {"ok": True}


@app.post("/api/push/teste")
async def teste_push():
    await asyncio.to_thread(notificar_celular, "As notificações da Maya estão funcionando!")
    return {"ok": True}


# ---------------------------------------------------------------------------- iniciar
def iniciar(cerebro):
    """Liga o servidor numa thread separada, só para o próprio PC (o Tailscale leva até o celular)."""
    global _cerebro, _cerebro_siri
    import uvicorn

    from maya.cerebro import Cerebro

    _cerebro = cerebro
    _cerebro_siri = Cerebro("siri")  # conversa própria, com respostas feitas para ouvir
    _chave_vapid()  # cria a chave das notificações na primeira vez
    lembretes.ao_disparar(lambda texto: notificar_celular(f"Lembrete: {texto}"))
    porta = getattr(config, "PORTA_CELULAR", 8765)
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning"))
    threading.Thread(target=servidor.run, daemon=True).start()
    print(f"[app do celular em http://127.0.0.1:{porta}]")

"""
Ações que a Maya pode executar. Para criar uma ação nova:
  1. escreva uma função que recebe os parâmetros e devolve um texto com o resultado;
  2. adicione a descrição dela na lista FERRAMENTAS (é isso que a IA lê para decidir);
  3. registre a função no dicionário FUNCOES.
"""

import ctypes
import datetime
import re
import subprocess
import threading
import urllib.parse
import webbrowser

import requests

import config

# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------


def ver_hora():
    agora = datetime.datetime.now()
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
    return f"Agora são {agora:%H:%M} de {dias[agora.weekday()]}, {agora:%d/%m/%Y}."


def abrir_programa(nome):
    nome = nome.lower().strip()
    comando = config.PROGRAMAS.get(nome)
    if comando is None:  # tenta achar por parte do nome ("bloco" -> "bloco de notas")
        for chave, valor in config.PROGRAMAS.items():
            if nome in chave or chave in nome:
                comando = valor
                break
    if comando is None:
        conhecidos = ", ".join(config.PROGRAMAS)
        return f"Não conheço o programa '{nome}'. Programas que sei abrir: {conhecidos}."
    subprocess.Popen(comando, shell=True)
    return f"Abri {nome}."


def abrir_site(endereco):
    if not endereco.startswith(("http://", "https://")):
        endereco = "https://" + endereco
    webbrowser.open(endereco)
    return f"Abri {endereco}."


def pesquisar_google(busca):
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(busca))
    return f"Pesquisei '{busca}' no Google."


def tocar_youtube(busca):
    url_busca = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(busca)
    try:
        pagina = requests.get(url_busca, timeout=8, headers={"Accept-Language": "pt-BR"}).text
        video = re.search(r'"videoId":"([\w-]{11})"', pagina)
        if video:
            webbrowser.open("https://www.youtube.com/watch?v=" + video.group(1))
            return f"Tocando '{busca}' no YouTube."
    except requests.RequestException:
        pass
    webbrowser.open(url_busca)
    return f"Abri a busca por '{busca}' no YouTube."


def tocar_spotify(busca):
    subprocess.Popen(f'start "" "spotify:search:{urllib.parse.quote(busca)}"', shell=True)
    return f"Abri a busca por '{busca}' no Spotify. Aperte play no primeiro resultado."


# Teclas de volume do Windows (cada toque muda cerca de 2%)
_VOLUME_MAIS, _VOLUME_MENOS, _MUDO = 0xAF, 0xAE, 0xAD


def _apertar_tecla(tecla, vezes=1):
    for _ in range(vezes):
        ctypes.windll.user32.keybd_event(tecla, 0, 0, 0)
        ctypes.windll.user32.keybd_event(tecla, 0, 2, 0)


def ajustar_volume(acao, valor=None):
    if acao == "mudo":
        _apertar_tecla(_MUDO)
        return "Liguei ou desliguei o mudo."
    if acao == "definir" and valor is not None:
        valor = max(0, min(100, int(valor)))
        _apertar_tecla(_VOLUME_MENOS, 50)  # zera
        _apertar_tecla(_VOLUME_MAIS, round(valor / 2))
        return f"Volume em {valor}%."
    passos = round((valor or 10) / 2)
    if acao == "aumentar":
        _apertar_tecla(_VOLUME_MAIS, passos)
        return "Aumentei o volume."
    if acao == "diminuir":
        _apertar_tecla(_VOLUME_MENOS, passos)
        return "Diminuí o volume."
    return "Ação de volume inválida."


_CLIMA = {
    0: "céu limpo", 1: "quase limpo", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina", 51: "garoa fraca", 53: "garoa", 55: "garoa forte",
    61: "chuva fraca", 63: "chuva", 65: "chuva forte", 80: "pancadas de chuva fracas",
    81: "pancadas de chuva", 82: "pancadas de chuva fortes", 95: "trovoadas",
    96: "trovoadas com granizo", 99: "trovoadas com granizo",
}


def ver_clima(cidade=None):
    cidade = cidade or config.CIDADE_PADRAO
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": cidade, "count": 1, "language": "pt"},
            timeout=8,
        ).json()
        if not geo.get("results"):
            return f"Não achei a cidade {cidade}."
        lugar = geo["results"][0]
        dados = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lugar["latitude"],
                "longitude": lugar["longitude"],
                "current": "temperature_2m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=8,
        ).json()
    except requests.RequestException:
        return "Não consegui consultar o clima. Verifique a internet."
    atual, dia = dados["current"], dados["daily"]
    descricao = _CLIMA.get(atual["weather_code"], "tempo variável")
    return (
        f"Em {lugar['name']}: {atual['temperature_2m']:.0f} graus, {descricao}. "
        f"Hoje, mínima de {dia['temperature_2m_min'][0]:.0f} e máxima de {dia['temperature_2m_max'][0]:.0f} graus, "
        f"{dia['precipitation_probability_max'][0]}% de chance de chuva."
    )


def criar_lembrete(minutos, mensagem):
    from maya.falar import falar

    def avisar():
        falar(f"Lembrete: {mensagem}")

    timer = threading.Timer(float(minutos) * 60, avisar)
    timer.daemon = True
    timer.start()
    hora = datetime.datetime.now() + datetime.timedelta(minutes=float(minutos))
    return f"Lembrete criado para as {hora:%H:%M}: {mensagem}. (Ele é perdido se a Maya for fechada.)"


def desligar_computador(acao):
    comandos = {
        "desligar": ("shutdown /s /t 60", "O computador vai desligar em 1 minuto. Diga 'cancelar desligamento' para impedir."),
        "reiniciar": ("shutdown /r /t 60", "O computador vai reiniciar em 1 minuto. Diga 'cancelar desligamento' para impedir."),
        "cancelar": ("shutdown /a", "Desligamento cancelado."),
        "bloquear": ("rundll32.exe user32.dll,LockWorkStation", "Tela bloqueada."),
    }
    if acao not in comandos:
        return "Ação inválida."
    comando, resposta = comandos[acao]
    subprocess.Popen(comando, shell=True)
    return resposta


# ---------------------------------------------------------------------------
# Descrições para a IA (formato JSON Schema)
# ---------------------------------------------------------------------------

FERRAMENTAS = [
    {
        "name": "ver_hora",
        "description": "Informa a hora e a data atuais.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "abrir_programa",
        "description": "Abre um programa no computador. Programas conhecidos: " + ", ".join(config.PROGRAMAS) + ".",
        "input_schema": {
            "type": "object",
            "properties": {"nome": {"type": "string", "description": "Nome do programa, ex.: calculadora"}},
            "required": ["nome"],
        },
    },
    {
        "name": "abrir_site",
        "description": "Abre um site no navegador.",
        "input_schema": {
            "type": "object",
            "properties": {"endereco": {"type": "string", "description": "Endereço, ex.: g1.globo.com"}},
            "required": ["endereco"],
        },
    },
    {
        "name": "pesquisar_google",
        "description": "Pesquisa algo no Google e mostra os resultados no navegador.",
        "input_schema": {
            "type": "object",
            "properties": {"busca": {"type": "string"}},
            "required": ["busca"],
        },
    },
    {
        "name": "tocar_youtube",
        "description": "Toca uma música ou vídeo no YouTube.",
        "input_schema": {
            "type": "object",
            "properties": {"busca": {"type": "string", "description": "Nome da música, artista ou vídeo"}},
            "required": ["busca"],
        },
    },
    {
        "name": "tocar_spotify",
        "description": "Procura uma música, artista ou playlist no Spotify.",
        "input_schema": {
            "type": "object",
            "properties": {"busca": {"type": "string"}},
            "required": ["busca"],
        },
    },
    {
        "name": "ajustar_volume",
        "description": "Muda o volume do computador.",
        "input_schema": {
            "type": "object",
            "properties": {
                "acao": {"type": "string", "enum": ["aumentar", "diminuir", "definir", "mudo"]},
                "valor": {"type": "integer", "description": "Porcentagem (0 a 100). Para aumentar/diminuir é o quanto mudar."},
            },
            "required": ["acao"],
        },
    },
    {
        "name": "ver_clima",
        "description": "Consulta o clima atual e a previsão de hoje de uma cidade.",
        "input_schema": {
            "type": "object",
            "properties": {"cidade": {"type": "string", "description": "Nome da cidade. Opcional."}},
            "required": [],
        },
    },
    {
        "name": "criar_lembrete",
        "description": "Cria um lembrete que a Maya fala em voz alta depois de alguns minutos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "minutos": {"type": "number", "description": "Daqui a quantos minutos"},
                "mensagem": {"type": "string", "description": "O que lembrar"},
            },
            "required": ["minutos", "mensagem"],
        },
    },
    {
        "name": "desligar_computador",
        "description": "Desliga, reinicia ou bloqueia o computador, ou cancela um desligamento. "
        "Use só quando o usuário pedir isso claramente.",
        "input_schema": {
            "type": "object",
            "properties": {"acao": {"type": "string", "enum": ["desligar", "reiniciar", "cancelar", "bloquear"]}},
            "required": ["acao"],
        },
    },
]

FUNCOES = {
    "ver_hora": ver_hora,
    "abrir_programa": abrir_programa,
    "abrir_site": abrir_site,
    "pesquisar_google": pesquisar_google,
    "tocar_youtube": tocar_youtube,
    "tocar_spotify": tocar_spotify,
    "ajustar_volume": ajustar_volume,
    "ver_clima": ver_clima,
    "criar_lembrete": criar_lembrete,
    "desligar_computador": desligar_computador,
}


def executar(nome, argumentos):
    """Executa a ferramenta pedida pela IA e devolve (texto, deu_erro)."""
    print(f"[ação] {nome} {argumentos or ''}")
    funcao = FUNCOES.get(nome)
    if funcao is None:
        return f"Ferramenta desconhecida: {nome}", True
    try:
        return funcao(**(argumentos or {})), False
    except Exception as erro:
        return f"Erro ao executar {nome}: {erro}", True

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
import urllib.parse
import webbrowser

import requests

import config
from maya import lembretes, memoria

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
        return _abrir_pelo_menu_iniciar(nome)
    subprocess.Popen(comando, shell=True)
    return f"Abri {nome}."


def _abrir_pelo_menu_iniciar(nome):
    """Abre qualquer app instalado: aperta a tecla Windows, digita o nome e dá Enter."""
    import time

    import pyautogui
    import pyperclip

    pyautogui.press("win")
    time.sleep(0.9)
    pyperclip.copy(nome)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.2)
    pyautogui.press("enter")
    return f"Procurei '{nome}' no menu Iniciar e abri o primeiro resultado."


def enviar_whatsapp(numero, mensagem):
    """Abre a conversa no WhatsApp do PC com a mensagem pronta e envia."""
    import os
    import time

    import pyautogui

    digitos = "".join(c for c in numero if c.isdigit())
    if len(digitos) <= 11:  # número brasileiro sem o código do país
        digitos = "55" + digitos
    os.startfile(f"whatsapp://send?phone={digitos}&text={urllib.parse.quote(mensagem)}")
    time.sleep(7)  # tempo para o WhatsApp abrir a conversa
    pyautogui.press("enter")
    return f"Enviei pelo WhatsApp para {numero}: {mensagem}"


def fazer_ligacao(numero):
    """Liga pelo app 'Vincular ao Celular' (Phone Link) do Windows, conectado ao iPhone."""
    import os

    digitos = "".join(c for c in numero if c.isdigit() or c == "+")
    os.startfile(f"tel:{digitos}")
    return f"Abri a ligação para {numero} no app Vincular ao Celular. Se ele pedir, confirme no PC."


def usar_computador(tarefa):
    from maya import operador

    return operador.usar_computador(tarefa)


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


def criar_lembrete(mensagem, minutos=None, data_hora=None):
    return lembretes.criar(mensagem, minutos, data_hora)


def listar_lembretes():
    return lembretes.listar_texto()


def cancelar_lembrete(qual):
    return lembretes.cancelar(qual)


def guardar_memoria(fato):
    return memoria.guardar(fato)


def esquecer_memoria(trecho):
    return memoria.esquecer(trecho)


def ver_tela():
    """Tira um print da tela do PC e devolve como imagem para a IA analisar."""
    import base64
    import io

    from PIL import ImageGrab

    imagem = ImageGrab.grab(all_screens=True).convert("RGB")
    imagem.thumbnail((1568, 1568))  # tamanho bom para a IA, sem gastar à toa
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=80)
    dados = base64.standard_b64encode(buffer.getvalue()).decode()
    return [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": dados}},
        {"type": "text", "text": "Print da tela do PC agora."},
    ]


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


pedido_para_fechar = False


def fechar_maya():
    global pedido_para_fechar
    pedido_para_fechar = True  # o main.py fecha a Maya depois que ela se despedir
    return "A Maya vai fechar depois de se despedir."


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
        "description": "Abre qualquer programa ou app instalado no computador (pelo nome). Atalhos conhecidos: "
        + ", ".join(config.PROGRAMAS) + ".",
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
        "description": "Cria um lembrete. Na hora, a Maya avisa em voz alta no PC e manda notificação no celular. "
        "Use 'minutos' para daqui a X minutos, ou 'data_hora' para um dia e horário (veja a hora atual com ver_hora).",
        "input_schema": {
            "type": "object",
            "properties": {
                "mensagem": {"type": "string", "description": "O que lembrar"},
                "minutos": {"type": "number", "description": "Daqui a quantos minutos"},
                "data_hora": {"type": "string", "description": "Formato AAAA-MM-DD HH:MM"},
            },
            "required": ["mensagem"],
        },
    },
    {
        "name": "listar_lembretes",
        "description": "Lista os lembretes marcados.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cancelar_lembrete",
        "description": "Cancela um lembrete pelo código (ex.: a1b2c3) ou por uma parte do texto.",
        "input_schema": {
            "type": "object",
            "properties": {"qual": {"type": "string"}},
            "required": ["qual"],
        },
    },
    {
        "name": "guardar_memoria",
        "description": "Guarda para sempre algo importante sobre o usuário: nome, gostos, pessoas, rotina, "
        "ou qualquer coisa que ele pedir para você lembrar. Escreva como uma frase curta.",
        "input_schema": {
            "type": "object",
            "properties": {"fato": {"type": "string", "description": "Ex.: O usuário se chama Brayan"}},
            "required": ["fato"],
        },
    },
    {
        "name": "esquecer_memoria",
        "description": "Apaga da memória de longo prazo as lembranças que contêm esse trecho.",
        "input_schema": {
            "type": "object",
            "properties": {"trecho": {"type": "string"}},
            "required": ["trecho"],
        },
    },
    {
        "name": "ver_tela",
        "description": "Tira um print da tela do PC para você ver o que está aberto, ler um erro, "
        "ajudar com o que o usuário está fazendo etc.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
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

FERRAMENTAS += [
    {
        "name": "usar_computador",
        "description": "Usa o computador como uma pessoa (vê a tela, clica, digita) para fazer qualquer tarefa "
        "que as outras ferramentas não fazem: entrar em apps e sites, procurar um contato e mandar mensagem, "
        "preencher campos, mexer em configurações etc. Descreva a tarefa completa e detalhada. Se a tarefa "
        "envia, publica, liga, compra ou apaga algo, pergunte antes ao usuário e só chame depois que ele confirmar, "
        "escrevendo na tarefa 'o usuário confirmou'. Demora de alguns segundos a alguns minutos.",
        "input_schema": {
            "type": "object",
            "properties": {"tarefa": {"type": "string"}},
            "required": ["tarefa"],
        },
    },
    {
        "name": "enviar_whatsapp",
        "description": "Envia uma mensagem de WhatsApp pelo PC para um número de telefone (com DDD). "
        "Se o usuário disser só o nome, procure o número na memória; se não houver, use usar_computador. "
        "SEMPRE confirme com o usuário o destinatário e o texto antes de enviar.",
        "input_schema": {
            "type": "object",
            "properties": {"numero": {"type": "string"}, "mensagem": {"type": "string"}},
            "required": ["numero", "mensagem"],
        },
    },
    {
        "name": "fazer_ligacao",
        "description": "Faz uma ligação telefônica pelo PC (app Vincular ao Celular ligado ao iPhone). "
        "Confirme o número com o usuário antes.",
        "input_schema": {
            "type": "object",
            "properties": {"numero": {"type": "string"}},
            "required": ["numero"],
        },
    },
]

FERRAMENTAS.append(
    {
        "name": "fechar_maya",
        "description": "Fecha a própria Maya (o assistente). Use quando o usuário pedir para sair, "
        "fechar, encerrar ou desligar a Maya, ou se despedir dizendo tchau.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    }
)

FUNCOES = {
    "fechar_maya": fechar_maya,
    "usar_computador": usar_computador,
    "enviar_whatsapp": enviar_whatsapp,
    "fazer_ligacao": fazer_ligacao,
    "listar_lembretes": listar_lembretes,
    "cancelar_lembrete": cancelar_lembrete,
    "guardar_memoria": guardar_memoria,
    "esquecer_memoria": esquecer_memoria,
    "ver_tela": ver_tela,
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
    """Executa a ferramenta pedida pela IA e devolve (resultado, deu_erro).
    O resultado é um texto, ou uma lista de blocos (ex.: imagem do ver_tela)."""
    print(f"[ação] {nome} {argumentos or ''}")
    funcao = FUNCOES.get(nome)
    if funcao is None:
        return f"Ferramenta desconhecida: {nome}", True
    try:
        return funcao(**(argumentos or {})), False
    except Exception as erro:
        return f"Erro ao executar {nome}: {erro}", True

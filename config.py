"""
Configurações da Maya. Edite este arquivo para mudar o comportamento dela.
"""

# ---------------------------------------------------------------------------
# Cérebro (a IA)
# ---------------------------------------------------------------------------
# "ollama" = roda no seu notebook, grátis e offline (mais lento com 8 GB de RAM)
# "claude" = roda na nuvem pela API da Anthropic (mais inteligente, custo pequeno por uso)
#            Precisa da chave ANTHROPIC_API_KEY no arquivo .env
CEREBRO = "ollama"

# Modelo local do Ollama. Com 8 GB de RAM, use um modelo pequeno que suporte ferramentas:
#   "qwen2.5:3b"  (recomendado, ~2 GB)   |   "llama3.2:3b"   |   "qwen2.5:1.5b" (mais rápido, mais burro)
MODELO_OLLAMA = "qwen2.5:3b"

# Modelo do Claude. "claude-opus-5-5" é o mais capaz.
# Para gastar bem menos, troque por "claude-haiku-5-5".
MODELO_CLAUDE = "claude-opus-5-5"

# ---------------------------------------------------------------------------
# Palavra de ativação
# ---------------------------------------------------------------------------
# Palavras que acordam a Maya (em minúsculas, como o reconhecedor escreve).
PALAVRAS_ATIVACAO = ["maya", "maia"]

# ---------------------------------------------------------------------------
# Voz para texto (Whisper)
# ---------------------------------------------------------------------------
# "base" = rápido | "small" = entende melhor (recomendado) | "medium" = pesado para 8 GB
MODELO_WHISPER = "small"

# Segundos de silêncio que indicam que você terminou de falar
SILENCIO_PARA_PARAR = 1.2
# Tempo máximo de uma frase (segundos)
TEMPO_MAXIMO_FALA = 15
# Sensibilidade ao silêncio. Aumente se ela nunca parar de gravar (ambiente barulhento).
LIMIAR_SILENCIO = 500

# ---------------------------------------------------------------------------
# Texto para voz (Piper)
# ---------------------------------------------------------------------------
VOZ_PIPER = "modelos/pt_BR-faber-medium.onnx"

# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------
# Cidade padrão para a previsão do tempo
CIDADE_PADRAO = "São Paulo"

# Programas que a Maya sabe abrir. Nome falado -> comando do Windows.
# Adicione os seus! Exemplo: "discord": r"C:\Users\SEU_USUARIO\AppData\Local\Discord\Update.exe --processStart Discord.exe"
PROGRAMAS = {
    "bloco de notas": "notepad",
    "calculadora": "calc",
    "explorador de arquivos": "explorer",
    "paint": "mspaint",
    "navegador": "start https://www.google.com",
    "chrome": "start chrome",
    "edge": "start msedge",
    "spotify": "start spotify:",
    "configurações": "start ms-settings:",
    "gerenciador de tarefas": "taskmgr",
    "word": "start winword",
    "excel": "start excel",
    "prompt de comando": "start cmd",
}

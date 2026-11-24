# Maya — assistente de voz para Windows

A Maya fica escutando em segundo plano. Quando você diz **"Maya"**, ela apita, ouve o seu pedido, responde em voz alta e executa a tarefa.

Ao ser chamada, a **personagem da Maya** aparece no canto inferior direito da tela, de headset, atrás de um notebook. Ela olha para você e mostra ondas de som enquanto ouve (azul), digita no notebook enquanto pensa (roxo) e mexe a boca junto com a voz quando fala (ciano). Depois ela desce e some. Para trocar pela bolha animada, use `ANIMACAO = "bolha"` no `config.py`. Para fechar a Maya, clique com o botão direito no ícone azul perto do relógio e escolha **Sair**.

A voz é feminina e neural (Francisca, a mesma do Microsoft Edge), gratuita, mas precisa de internet. Sem internet, ela usa a voz offline do Piper.

| Peça | Ferramenta | Funciona offline? |
|---|---|---|
| Palavra de ativação | Vosk (modelo pequeno em português) | Sim |
| Voz para texto | faster-whisper | Sim |
| Cérebro | Ollama (local) **ou** Claude (nuvem) | Ollama sim, Claude não |
| Texto para voz | Voz feminina "Francisca" (edge-tts); sem internet, usa o Piper | Francisca não, Piper sim |
| Ações | `maya/ferramentas.py` | Quase todas |

**O que ela já sabe fazer:** dizer a hora e a data, abrir programas e sites, pesquisar no Google, tocar música no YouTube, buscar no Spotify, mudar o volume, ver o clima, criar lembretes e desligar, reiniciar ou bloquear o PC.

Exemplos: *"Maya… que horas são?"*, *"Maya… abre a calculadora"*, *"Maya… toca Legião Urbana no YouTube"*, *"Maya… aumenta o volume"*, *"Maya… me lembra de tirar o bolo do forno em 20 minutos"*, *"Maya… vai chover hoje no Rio?"*

---

## Instalação passo a passo (Windows)

### 1. Instale o Python
Baixe o **Python 3.12** em https://www.python.org/downloads/ . Na primeira tela do instalador, **marque "Add python.exe to PATH"**.

### 2. Baixe o projeto
No GitHub, clique em **Code → Download ZIP** e extraia, por exemplo, em `C:\maya`. (Ou use `git clone`.)

### 3. Instale as dependências
Abra o **Prompt de Comando** dentro da pasta (digite `cmd` na barra de endereço do Explorer e aperte Enter) e rode:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python baixar_modelos.py
```

### 4. Escolha o cérebro
Abra o `config.py` no Bloco de Notas e mude `CEREBRO`:

**Opção A: Ollama (grátis e offline)**
1. Instale o Ollama: https://ollama.com/download
2. No Prompt de Comando: `ollama pull qwen2.5:3b`
3. Deixe `CEREBRO = "ollama"`.

> Com 8 GB de RAM, use só modelos pequenos (3B). Cada resposta pode levar de 5 a 20 segundos, e um modelo pequeno às vezes erra a ferramenta. Feche o navegador e outros programas pesados para ajudar.

**Opção B: Claude (nuvem, mais inteligente e rápido no seu notebook)**
1. Crie uma conta e uma chave em https://console.anthropic.com/settings/keys (você paga pelo uso; um pedido de voz custa frações de centavo).
2. Copie `.env.exemplo` para `.env` e cole a chave nele.
3. Mude para `CEREBRO = "claude"`.

> O padrão é `claude-opus-5-5`, o mais capaz. Para gastar bem menos, troque `MODELO_CLAUDE` por `"claude-haiku-5-5"`.

**Recomendação para 8 GB:** comece com o Claude, porque o notebook fica livre e as respostas saem melhores. Use o Ollama quando quiser privacidade total ou estiver sem internet.

### 5. Teste
Primeiro sem microfone, digitando:
```bat
iniciar_maya.bat --texto
```
Depois com voz:
```bat
iniciar_maya.bat
```
Diga **"Maya"**, espere o apito e fale o pedido. Na primeira vez, o Whisper baixa sozinho (cerca de 500 MB).

### 6. Rodar sem a tela preta e iniciar com o Windows
Com o ambiente ativado (`.venv\Scripts\activate`):
```bat
python instalar_inicializacao.py
```
Isso cria o atalho **Maya** na Área de Trabalho, faz ela iniciar sozinha quando o Windows ligar e já abre a Maya escondida. As mensagens vão para `maya.log`. Para desfazer: `python instalar_inicializacao.py remover`.

---

## Personalizando

- **Programas:** adicione os seus no dicionário `PROGRAMAS` do `config.py` (nome falado → comando).
- **Cidade do clima:** `CIDADE_PADRAO` no `config.py`.
- **Nome da assistente:** mude `PALAVRAS_ATIVACAO`. Use palavras que existem em português, porque o Vosk só reconhece palavras do vocabulário dele.
- **Nova ação:** em `maya/ferramentas.py`, escreva a função, descreva-a em `FERRAMENTAS` e registre-a em `FUNCOES`. A IA passa a usá-la sozinha.

## Problemas comuns

| Problema | Solução |
|---|---|
| Ela não acorda quando chamo | Fale "Maya" claramente e perto do microfone. Confira o microfone padrão em Configurações → Som. |
| Ela nunca para de gravar | Aumente `LIMIAR_SILENCIO` no `config.py` (ex.: 800). |
| Ela corta a minha frase | Aumente `SILENCIO_PARA_PARAR` (ex.: 2). |
| Respostas lentas no Ollama | Use `qwen2.5:1.5b` ou mude para o Claude. |
| Erro ao instalar `piper-tts` | A Maya funciona mesmo assim, com a voz do Windows. Para uma voz em português, instale "Português (Brasil)" em Configurações → Hora e idioma → Fala. |
| "O Ollama não está aberto" | Abra o aplicativo Ollama (ícone perto do relógio). |

## Limitações
- Ela só faz o que estiver em `maya/ferramentas.py`. Não tem casa inteligente nem compras.
- Os lembretes ficam na memória: somem se a Maya for fechada.
- O Spotify abre a busca, mas você precisa apertar o play (tocar direto exige a API paga do Spotify).

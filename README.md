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

**O que ela já sabe fazer:** dizer a hora e a data, abrir programas e sites, pesquisar no Google, tocar música no YouTube, buscar no Spotify, mudar o volume, ver o clima, criar lembretes e desligar, reiniciar ou bloquear o PC. Com o cérebro Claude, ela também:
- **pesquisa na internet** em tempo real (notícias, jogos, preços);
- **lembra de você**: nome, gostos e o que você pedir para guardar (arquivo `memoria.json`);
- **vê a sua tela**: *"Maya, o que é esse erro na minha tela?"*;
- **continua ouvindo** alguns segundos depois de responder, sem você precisar dizer "Maya" de novo.

Os lembretes ficam salvos (`lembretes.json`), sobrevivem a reinícios e avisam no PC e no celular.

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

### 7. App no iPhone (opcional)
O iPhone conversa com a Maya do PC por uma rede privada e gratuita, o **Tailscale**. Funciona de qualquer lugar (4G, outra casa), sem deixar o seu PC aberto para a internet. O PC precisa estar ligado e com a Maya rodando.

1. Instale o Tailscale **no PC** (https://tailscale.com/download/windows) e **no iPhone** (App Store) e entre com a **mesma conta** nos dois.
2. No PC, com a Maya rodando e o ambiente ativado:
   ```bat
   python configurar_celular.py
   ```
   Ele mostra um endereço (`https://...ts.net`) e abre um QR code. Se aparecer um link pedindo para ativar o HTTPS, abra-o, ative e rode o comando de novo.
3. No iPhone, com o Tailscale ligado, aponte a câmera para o QR code (ou abra o endereço no **Safari**).
4. Toque em **Compartilhar** → **Adicionar à Tela de Início**. Agora a Maya é um app no seu iPhone.
5. Abra o app pelo ícone, toque em ⏰ → **Ativar notificações** para receber os lembretes.

No app: toque no microfone para falar (e de novo para terminar) ou escreva. As ações (tocar música, abrir programas, ver a tela, desligar) acontecem **no PC**, então dá para controlar o computador de longe.

### 8. Falar com a Maya pela Siri (mesmo com o iPhone bloqueado)
O iPhone só deixa a Siri ouvir com a tela bloqueada, então a Siri vira a "porta de entrada": você diz **"E aí Siri, Maya"**, fala o pedido, e a Maya responde em voz alta.

1. No iPhone, abra o app **Atalhos** → **+** (novo atalho).
2. Adicione a ação **Ditar Texto** (idioma: Português (Brasil); Parar de Ouvir: Após Pausa).
3. Adicione **Obter Conteúdo do URL**:
   - URL: `https://SEU-PC.SUA-REDE.ts.net/api/siri` (o endereço que o `configurar_celular.py` mostrou, com `/api/siri` no fim)
   - Método: **POST** · Corpo da Solicitação: **JSON** · adicione um campo de **Texto** com a chave `texto` e o valor **Texto Ditado**.
4. Adicione **Falar Texto** com **Conteúdo do URL**.
5. Renomeie o atalho para **Maya**.
6. No app do Tailscale, ative **VPN On Demand** (ou deixe sempre conectado), para a Siri achar o PC mesmo com o celular bloqueado.
7. Em Ajustes → Siri, ative **Permitir Siri Quando Bloqueado**.

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
- O Spotify abre a busca, mas você precisa apertar o play (tocar direto exige a API paga do Spotify).
- O app do celular só funciona com o PC ligado e a Maya aberta.
- A pesquisa na internet, a memória inteligente e a visão da tela precisam do cérebro Claude.

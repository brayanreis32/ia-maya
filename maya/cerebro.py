"""O cérebro da Maya: recebe o texto, decide quais ferramentas usar e devolve a resposta."""

import time

import config
from maya import ferramentas

INSTRUCOES = """Você é a Maya, uma assistente de voz que roda no computador Windows do usuário.
Responda sempre em português do Brasil, de forma curta e natural, como numa conversa falada:
uma ou duas frases, sem listas, sem markdown, sem emojis e sem links.
Quando o pedido puder ser feito por uma ferramenta, use a ferramenta em vez de explicar como fazer.
Para saber a hora ou a data, use a ferramenta ver_hora.
Se não houver ferramenta para o pedido, diga com honestidade que ainda não sabe fazer isso."""

# A conversa recomeça depois de alguns minutos sem falar com a Maya
MINUTOS_PARA_ESQUECER = 5


class Cerebro:
    def __init__(self):
        self.historico = []
        self.ultima_vez = 0.0
        if config.CEREBRO == "claude":
            import anthropic

            self.cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente / .env
        elif config.CEREBRO == "ollama":
            import ollama

            self.cliente = ollama
        else:
            raise ValueError("CEREBRO no config.py deve ser 'ollama' ou 'claude'.")

    def responder(self, texto):
        if time.time() - self.ultima_vez > MINUTOS_PARA_ESQUECER * 60:
            self.historico = []
        self.ultima_vez = time.time()
        if config.CEREBRO == "claude":
            return self._responder_claude(texto)
        return self._responder_ollama(texto)

    # ------------------------------------------------------------------ Claude
    def _responder_claude(self, texto):
        import anthropic

        self.historico.append({"role": "user", "content": texto})
        extras = {}
        # Se o modelo recusar um pedido, a API tenta de novo com outro modelo automaticamente.
        # (Os modelos Haiku não têm esse recurso.)
        if "haiku" not in config.MODELO_CLAUDE:
            extras = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}

        for _ in range(8):  # limite de rodadas de ferramentas por pedido
            try:
                resposta = self.cliente.beta.messages.create(
                    model=config.MODELO_CLAUDE,
                    max_tokens=16000,
                    system=INSTRUCOES,
                    tools=ferramentas.FERRAMENTAS,
                    messages=self.historico,
                    output_config={"effort": "low"},  # respostas rápidas para conversa por voz
                    **extras,
                )
            except anthropic.AuthenticationError:
                self.historico.pop()
                return "Minha chave da API do Claude está errada ou faltando. Confira o arquivo ponto env."
            except anthropic.RateLimitError:
                self.historico.pop()
                return "Estou recebendo pedidos demais agora. Tente de novo em alguns segundos."
            except anthropic.APIConnectionError:
                self.historico.pop()
                return "Não consegui me conectar à internet."
            except anthropic.APIStatusError as erro:
                self.historico.pop()
                print(f"[erro da API] {erro}")
                return "Tive um problema ao falar com o Claude."

            # Guarda a resposta inteira (inclusive blocos internos) para a conversa continuar certa
            self.historico.append({"role": "assistant", "content": resposta.content})

            if resposta.stop_reason == "refusal":
                return "Desculpe, não posso ajudar com isso."
            if resposta.stop_reason == "pause_turn":
                continue
            if resposta.stop_reason != "tool_use":
                return " ".join(b.text for b in resposta.content if b.type == "text").strip()

            resultados = []
            for bloco in resposta.content:
                if bloco.type == "tool_use":
                    saida, erro = ferramentas.executar(bloco.name, bloco.input)
                    resultados.append(
                        {"type": "tool_result", "tool_use_id": bloco.id, "content": saida, "is_error": erro}
                    )
            self.historico.append({"role": "user", "content": resultados})

        return "Esse pedido ficou complicado demais, pode repetir de outro jeito?"

    # ------------------------------------------------------------------ Ollama
    def _responder_ollama(self, texto):
        import ollama

        ferramentas_ollama = [
            {
                "type": "function",
                "function": {"name": f["name"], "description": f["description"], "parameters": f["input_schema"]},
            }
            for f in ferramentas.FERRAMENTAS
        ]
        self.historico.append({"role": "user", "content": texto})

        for _ in range(5):
            try:
                resposta = self.cliente.chat(
                    model=config.MODELO_OLLAMA,
                    messages=[{"role": "system", "content": INSTRUCOES}] + self.historico,
                    tools=ferramentas_ollama,
                    options={"temperature": 0.3},
                )
            except ollama.ResponseError as erro:
                self.historico.pop()
                if erro.status_code == 404:
                    return f"O modelo {config.MODELO_OLLAMA} não está instalado. Rode: ollama pull {config.MODELO_OLLAMA}"
                return f"O Ollama deu um erro: {erro.error}"
            except ConnectionError:
                self.historico.pop()
                return "O Ollama não está aberto. Abra o programa Ollama e tente de novo."

            mensagem = resposta.message
            self.historico.append(mensagem)
            if not mensagem.tool_calls:
                return (mensagem.content or "").strip()

            for chamada in mensagem.tool_calls:
                saida, _ = ferramentas.executar(chamada.function.name, dict(chamada.function.arguments or {}))
                self.historico.append({"role": "tool", "content": saida, "tool_name": chamada.function.name})

        return "Esse pedido ficou complicado demais, pode repetir de outro jeito?"

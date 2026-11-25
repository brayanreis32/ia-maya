"""
Bolha animada que aparece na parte de baixo da tela quando a Maya é chamada.
  azul  = ouvindo (cresce com a sua voz)
  roxo  = pensando
  ciano = falando (pulsa com a voz dela)
"""

import math
import sys
import time
import tkinter as tk

from maya import estado

LARGURA, ALTURA = 380, 300
COR_FUNDO = "#010203"  # cor "chave": vira transparente no Windows
RAIO_BASE = 58
ANEIS = 28

CORES = {  # (borda, centro) do degradê
    "ouvindo": ((29, 78, 216), (191, 219, 254)),
    "pensando": ((109, 40, 217), (221, 214, 254)),
    "falando": ((8, 145, 178), (207, 250, 254)),
    "oculto": ((29, 78, 216), (191, 219, 254)),
}
LEGENDAS = {"ouvindo": "Estou ouvindo…", "pensando": "Pensando…", "falando": ""}


def _misturar(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c)


class Animacao:
    def __init__(self):
        self.raiz = tk.Tk()
        self.raiz.title("Maya")
        self.raiz.overrideredirect(True)  # sem bordas nem barra de título
        self.raiz.attributes("-topmost", True)  # sempre por cima das outras janelas
        self.raiz.configure(bg=COR_FUNDO)
        if sys.platform == "win32":
            self.raiz.attributes("-transparentcolor", COR_FUNDO)

        x = (self.raiz.winfo_screenwidth() - LARGURA) // 2
        y = self.raiz.winfo_screenheight() - ALTURA - 60  # um pouco acima da barra de tarefas
        self.raiz.geometry(f"{LARGURA}x{ALTURA}+{x}+{y}")

        self.tela = tk.Canvas(self.raiz, width=LARGURA, height=ALTURA, bg=COR_FUNDO, highlightthickness=0)
        self.tela.pack()
        self.aneis = [self.tela.create_oval(0, 0, 0, 0, outline="", fill="") for _ in range(ANEIS)]
        self.pontos = [self.tela.create_oval(0, 0, 0, 0, outline="", fill="") for _ in range(3)]
        self.caixa = self.tela.create_polygon(0, 0, 0, 0, smooth=True, fill="#18181b", outline="")
        self.legenda = self.tela.create_text(
            LARGURA / 2, 0, text="", fill="#fafafa", font=("Segoe UI", 11), width=LARGURA - 50, justify="center"
        )

        self.borda, self.centro = CORES["ouvindo"]
        self.nivel = 0.0
        self.opacidade = 0.0
        self.visivel = False
        self.raiz.attributes("-alpha", 0.0)
        self.raiz.withdraw()

    # ------------------------------------------------------------------ desenho
    def _caixa_arredondada(self, x1, y1, x2, y2, r):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.tela.coords(self.caixa, *pts)

    def _quadro(self):
        agora = time.time()
        modo = estado.atual

        # Aparece / some suavemente
        alvo_opacidade = 0.0 if modo == "oculto" or estado.operando else 1.0
        self.opacidade += (alvo_opacidade - self.opacidade) * 0.2
        if alvo_opacidade > 0 and not self.visivel:
            self.raiz.deiconify()
            self.raiz.attributes("-topmost", True)
            self.visivel = True
        if self.visivel and self.opacidade < 0.02 and alvo_opacidade == 0:
            self.raiz.withdraw()
            self.visivel = False
        if self.visivel:
            self.raiz.attributes("-alpha", self.opacidade)
            self._desenhar(agora, modo)

        self.raiz.after(30, self._quadro)  # ~33 quadros por segundo

    def _desenhar(self, agora, modo):
        # Cores mudam aos poucos de um estado para o outro
        borda_alvo, centro_alvo = CORES.get(modo, CORES["ouvindo"])
        self.borda = _misturar(self.borda, borda_alvo, 0.12)
        self.centro = _misturar(self.centro, centro_alvo, 0.12)

        self.nivel += (min(1.0, estado.nivel_atual()) - self.nivel) * 0.35
        respiracao = math.sin(agora * 2.2) * 3
        if modo == "pensando":
            raio = RAIO_BASE * 0.85 + math.sin(agora * 5) * 4
        else:
            raio = RAIO_BASE + respiracao + self.nivel * 26

        cx, cy = LARGURA / 2, 110
        # Ponto de brilho que gira devagar: dá o efeito de "líquido" se mexendo
        angulo = agora * (2.5 if modo == "pensando" else 1.2)
        bx = math.cos(angulo) * raio * 0.35
        by = math.sin(angulo) * raio * 0.35 - raio * 0.15

        for i, anel in enumerate(self.aneis):
            t = i / (ANEIS - 1)  # 0 = borda, 1 = centro
            r = raio * (1 - t * 0.92)
            ox, oy = bx * t, by * t
            self.tela.coords(anel, cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r)
            self.tela.itemconfigure(anel, fill=_hex(_misturar(self.borda, self.centro, t ** 1.4)))

        # Três pontinhos girando enquanto pensa
        for i, ponto in enumerate(self.pontos):
            if modo == "pensando":
                a = agora * 3 + i * 2 * math.pi / 3
                px, py = cx + math.cos(a) * (raio + 18), cy + math.sin(a) * (raio + 18)
                self.tela.coords(ponto, px - 5, py - 5, px + 5, py + 5)
                self.tela.itemconfigure(ponto, fill=_hex(self.centro))
            else:
                self.tela.itemconfigure(ponto, fill="")

        # Legenda: o que você disse ou o que ela está respondendo
        texto = estado.texto if modo != "ouvindo" else LEGENDAS["ouvindo"]
        if modo == "pensando" and not texto:
            texto = LEGENDAS["pensando"]
        if len(texto) > 140:
            texto = texto[:137] + "…"
        self.tela.itemconfigure(self.legenda, text=texto)
        if texto:
            self.tela.coords(self.legenda, cx, 0)
            x1, y1, x2, y2 = self.tela.bbox(self.legenda)
            altura = y2 - y1
            topo = 205
            self.tela.coords(self.legenda, cx, topo + 12 + altura / 2)
            self._caixa_arredondada(min(x1, cx - 60) - 16, topo, max(x2, cx + 60) + 16, topo + altura + 24, 14)
            self.tela.itemconfigure(self.caixa, fill="#18181b")
        else:
            self.tela.itemconfigure(self.caixa, fill="")

    def rodar(self):
        self._quadro()
        self.raiz.mainloop()

    def fechar(self):
        self.raiz.after(0, self.raiz.destroy)

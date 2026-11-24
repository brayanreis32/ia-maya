"""
Avatar da Maya: uma personagem de headset atrás de um notebook, no canto da tela.
  ouvindo  -> olha para você, o headset acende em azul e aparecem ondas de som
  pensando -> olha para o notebook e digita, com códigos subindo da tela (roxo)
  falando  -> olha para você e mexe a boca junto com a voz (ciano)

Desenhado com Pillow em tamanho dobrado e reduzido, para as bordas ficarem lisas.
"""

import math
import random
import sys
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

from maya import estado

L, A = 280, 260  # área do desenho
ALTURA_LEGENDA = 80
ESCALA = 2  # desenha em 2x e reduz (antisserrilhado)
CHAVE = (1, 2, 3)  # cor que vira transparente no Windows
COR_CHAVE = "#010203"

CONTORNO = (42, 31, 61)
PELE = (248, 214, 190)
CABELO = (74, 52, 112)
CABELO_BRILHO = (104, 80, 150)
MOLETOM = (79, 70, 229)
HEADSET = (39, 39, 42)
NOTEBOOK = (212, 212, 216)
NOTEBOOK_BASE = (161, 161, 170)
BOCHECHA = (244, 166, 166)
IRIS = (76, 59, 143)

CORES_ESTADO = {
    "ouvindo": (59, 130, 246),
    "pensando": (139, 92, 246),
    "falando": (34, 211, 238),
    "oculto": (59, 130, 246),
}
SIMBOLOS = ["</>", "{ }", "01", "#", "( )", ";"]


def _misturar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Avatar:
    def __init__(self):
        self.raiz = tk.Tk()
        self.raiz.title("Maya")
        self.raiz.overrideredirect(True)
        self.raiz.attributes("-topmost", True)
        self.raiz.configure(bg=COR_CHAVE)
        if sys.platform == "win32":
            self.raiz.attributes("-transparentcolor", COR_CHAVE)

        largura, altura = L, A + ALTURA_LEGENDA
        x = self.raiz.winfo_screenwidth() - largura - 20  # canto inferior direito
        y = self.raiz.winfo_screenheight() - altura - 50
        self.raiz.geometry(f"{largura}x{altura}+{x}+{y}")

        self.tela = tk.Canvas(self.raiz, width=largura, height=altura, bg=COR_CHAVE, highlightthickness=0)
        self.tela.pack()
        self.item_imagem = self.tela.create_image(0, 0, anchor="nw")
        self.caixa = self.tela.create_polygon(0, 0, 0, 0, smooth=True, fill="", outline="")
        self.legenda = self.tela.create_text(
            L / 2, 0, text="", fill="#fafafa", font=("Segoe UI", 10), width=L - 30, justify="center"
        )
        self.foto = None

        try:
            self.fonte = ImageFont.truetype("consola.ttf", 13 * ESCALA)
        except OSError:
            try:
                self.fonte = ImageFont.load_default(size=13 * ESCALA)
            except TypeError:
                self.fonte = ImageFont.load_default()

        self.cor = CORES_ESTADO["ouvindo"]
        self.nivel = 0.0
        self.opacidade = 0.0
        self.entrada = 1.0  # 1 = escondida embaixo, 0 = no lugar
        self.visivel = False
        self.proxima_piscada = time.time() + 2
        self.olhar_y = 0.0
        self.simbolos = []  # [x, y, idade, texto]
        self.raiz.attributes("-alpha", 0.0)
        self.raiz.withdraw()

    # ------------------------------------------------------------------ laço
    def _quadro(self):
        agora = time.time()
        modo = estado.atual
        alvo = 0.0 if modo == "oculto" else 1.0
        self.opacidade += (alvo - self.opacidade) * 0.18
        self.entrada += ((1 - alvo) - self.entrada) * 0.18

        if alvo > 0 and not self.visivel:
            self.raiz.deiconify()
            self.raiz.attributes("-topmost", True)
            self.visivel = True
        if self.visivel and alvo == 0 and self.opacidade < 0.02:
            self.raiz.withdraw()
            self.visivel = False
        if self.visivel:
            self.raiz.attributes("-alpha", self.opacidade)
            self._atualizar(agora, modo)
        self.raiz.after(40, self._quadro)  # 25 quadros por segundo

    def _atualizar(self, agora, modo):
        self.cor = _misturar(self.cor, CORES_ESTADO.get(modo, self.cor), 0.15)
        self.nivel += (min(1.0, estado.nivel_atual()) - self.nivel) * 0.45
        self.olhar_y += ((5.0 if modo == "pensando" else 0.0) - self.olhar_y) * 0.2

        if modo == "pensando" and random.random() < 0.18:
            x = random.choice((random.uniform(52, 92), random.uniform(188, 228)))  # dos lados, longe do rosto
            self.simbolos.append([x, 190.0, 0, random.choice(SIMBOLOS)])
        for s in self.simbolos:
            s[1] -= 1.6
            s[2] += 1
        self.simbolos = [s for s in self.simbolos if s[2] < 28]

        imagem = self._desenhar(agora, modo)
        self.foto = ImageTk.PhotoImage(imagem)
        self.tela.itemconfigure(self.item_imagem, image=self.foto)
        self._legenda(modo)

    # ------------------------------------------------------------------ desenho
    def _desenhar(self, agora, modo):
        img = Image.new("RGB", (L * ESCALA, A * ESCALA), CHAVE)
        d = ImageDraw.Draw(img)
        s = ESCALA

        def elipse(cx, cy, rx, ry, cor, contorno=CONTORNO, largura=2):
            d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=cor,
                      outline=contorno, width=largura * s if contorno else 0)

        def retangulo(x1, y1, x2, y2, r, cor, contorno=CONTORNO, largura=2):
            d.rounded_rectangle([x1 * s, y1 * s, x2 * s, y2 * s], radius=r * s, fill=cor,
                                outline=contorno, width=largura * s if contorno else 0)

        desce = self.entrada * 60  # entra deslizando de baixo
        respira = math.sin(agora * 2.0) * 1.5
        fala = self.nivel if modo == "falando" else 0.0
        digitando = modo == "pensando"
        oy = desce + respira + (2.5 if digitando else 0) - fala * 2
        cx, cy = 140, 100 + oy

        # Ombros (balançam alternados quando digita)
        balanco = math.sin(agora * 14) * 2 if digitando else 0
        d.polygon([((cx - 70) * s, (232 + desce) * s), ((cx - 52) * s, (168 + oy + balanco) * s),
                   ((cx + 52) * s, (168 + oy - balanco) * s), ((cx + 70) * s, (232 + desce) * s)],
                  fill=MOLETOM, outline=CONTORNO, width=2 * s)
        elipse(cx, 166 + oy, 14, 7, PELE)  # pescoço

        # Cabelo de trás
        elipse(cx, cy - 4, 66, 64, CABELO)
        retangulo(cx - 66, cy - 4, cx + 66, cy + 52, 22, CABELO)

        # Rosto (com um leve brilho da tela do notebook quando digita)
        pele = _misturar(PELE, (200, 205, 255), 0.18) if digitando else PELE
        elipse(cx, cy + 8, 52, 50, pele)

        # Franja
        d.chord([(cx - 56) * s, (cy - 58) * s, (cx + 56) * s, (cy + 42) * s], 180, 360, fill=CABELO)
        for bx in (-34, -12, 12, 34):
            elipse(cx + bx, cy - 9, 14, 11, CABELO, contorno=None)
        d.arc([(cx - 56) * s, (cy - 58) * s, (cx + 56) * s, (cy + 42) * s], 200, 340, fill=CONTORNO, width=2 * s)
        d.arc([(cx - 30) * s, (cy - 50) * s, (cx + 10) * s, (cy - 20) * s], 200, 300, fill=CABELO_BRILHO, width=3 * s)

        # Olhos (piscam de vez em quando)
        if agora > self.proxima_piscada + 0.13:
            self.proxima_piscada = agora + random.uniform(2.5, 5.5)
        piscando = agora > self.proxima_piscada
        for ex in (-20, 20):
            x, y = cx + ex, cy + 14
            if piscando:
                d.arc([(x - 9) * s, (y - 4) * s, (x + 9) * s, (y + 6) * s], 200, 340, fill=CONTORNO, width=2 * s)
                continue
            elipse(x, y, 9, 11, (255, 255, 255))
            py = y + self.olhar_y
            elipse(x, py + 1, 6.5, 7.5, IRIS, contorno=None)
            elipse(x, py + 2, 3.5, 4, CONTORNO, contorno=None)
            elipse(x - 2.5, py - 2.5, 2.2, 2.2, (255, 255, 255), contorno=None)
            d.arc([(x - 10) * s, (y - 24) * s, (x + 10) * s, (y - 8) * s], 220, 320, fill=CONTORNO, width=2 * s)

        # Bochechas
        elipse(cx - 32, cy + 30, 7, 4, BOCHECHA, contorno=None)
        elipse(cx + 32, cy + 30, 7, 4, BOCHECHA, contorno=None)

        # Boca: sorriso fechado ou aberta conforme o volume da voz
        my = cy + 36
        if fala > 0.08:
            abertura = 2 + fala * 9
            elipse(cx, my, 6 + fala * 2, abertura, (122, 46, 59))
            if abertura > 5:
                elipse(cx, my + abertura * 0.45, 4, abertura * 0.35, (232, 120, 130), contorno=None)
        else:
            d.arc([(cx - 8) * s, (my - 6) * s, (cx + 8) * s, (my + 4) * s], 20, 160, fill=CONTORNO, width=2 * s)

        # Headset: arco, conchas que acendem com a cor do estado e microfone
        d.arc([(cx - 60) * s, (cy - 62) * s, (cx + 60) * s, (cy + 50) * s], 190, 350, fill=HEADSET, width=6 * s)
        brilho = 0.5 + 0.5 * math.sin(agora * 4) if modo != "oculto" else 0
        luz = _misturar(self.cor, (255, 255, 255), 0.25 * brilho)
        for lado in (-1, 1):
            retangulo(cx + lado * 58 - 9, cy - 4, cx + lado * 58 + 9, cy + 30, 8, HEADSET)
            retangulo(cx + lado * 58 - 4, cy + 3, cx + lado * 58 + 4, cy + 23, 4, luz, contorno=None)
        d.line([(cx - 56) * s, (cy + 26) * s, (cx - 40) * s, (cy + 40) * s, (cx - 20) * s, (cy + 42) * s],
               fill=HEADSET, width=3 * s, joint="curve")
        elipse(cx - 18, cy + 42, 4, 4, luz, contorno=HEADSET)

        # Ondas de som ao ouvir
        if modo == "ouvindo":
            for i in range(3):
                forca = max(0.0, min(1.0, self.nivel * 1.6 - i * 0.3))
                if forca <= 0:
                    continue
                r = 12 + i * 9
                cor = _misturar(CHAVE, self.cor, 0.4 + 0.6 * forca)
                d.arc([(cx + 72 - r) * s, (cy + 13 - r) * s, (cx + 72 + r) * s, (cy + 13 + r) * s],
                      -45, 45, fill=cor, width=3 * s)

        # Códigos subindo da tela enquanto pensa
        for x, y, idade, texto in self.simbolos:
            t = idade / 28
            cor = _misturar(self.cor, (240, 240, 255), 0.3 + 0.4 * t)
            d.text((x * s, (y + desce) * s), texto, fill=cor, font=self.fonte, anchor="mm")

        # Notebook (tampa vista por trás, com o logo que brilha)
        topo = 178 + desce
        retangulo(62, topo, 218, topo + 66, 8, NOTEBOOK)
        d.rectangle([66 * s, (topo + 4) * s, 214 * s, (topo + 8) * s], fill=(228, 228, 231))
        pulso = 0.6 + 0.4 * math.sin(agora * (8 if digitando else 3))
        elipse(140, topo + 33, 11, 11, _misturar(NOTEBOOK, self.cor, pulso), contorno=None)
        d.text((140 * s, (topo + 33) * s), "M", fill=(255, 255, 255), font=self.fonte, anchor="mm")
        retangulo(44, topo + 64, 236, topo + 74, 4, NOTEBOOK_BASE)

        return img.reduce(ESCALA)

    def _legenda(self, modo):
        texto = estado.texto if modo != "ouvindo" else "Estou ouvindo…"
        if modo == "pensando" and not texto:
            texto = "Pensando…"
        if len(texto) > 120:
            texto = texto[:117] + "…"
        self.tela.itemconfigure(self.legenda, text=texto)
        if not texto:
            self.tela.itemconfigure(self.caixa, fill="")
            return
        cx = L / 2
        self.tela.coords(self.legenda, cx, 0)
        x1, y1, x2, y2 = self.tela.bbox(self.legenda)
        topo = A + 4 + self.entrada * 60
        altura = y2 - y1
        self.tela.coords(self.legenda, cx, topo + 10 + altura / 2)
        x1, x2, y2 = min(x1, cx - 50) - 12, max(x2, cx + 50) + 12, topo + altura + 20
        r = 12
        pts = [x1 + r, topo, x2 - r, topo, x2, topo, x2, topo + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, topo + r, x1, topo]
        self.tela.coords(self.caixa, *pts)
        self.tela.itemconfigure(self.caixa, fill="#18181b")

    def rodar(self):
        self._quadro()
        self.raiz.mainloop()

    def fechar(self):
        self.raiz.after(0, self.raiz.destroy)

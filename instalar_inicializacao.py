"""
Faz a Maya rodar escondida (sem a tela preta):
  - cria o atalho "Maya" na Área de Trabalho (dois cliques para abrir);
  - faz ela iniciar sozinha quando o Windows liga;
  - já abre a Maya agora.

    python instalar_inicializacao.py           instala
    python instalar_inicializacao.py remover   desfaz
"""

import os
import subprocess
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
INICIALIZAR = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")


def pasta_area_de_trabalho():
    """Pasta real da Área de Trabalho (pode estar dentro do OneDrive)."""
    import ctypes

    caminho = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, caminho)
    return caminho.value or os.path.join(os.environ["USERPROFILE"], "Desktop")


AREA_DE_TRABALHO = pasta_area_de_trabalho()
ATALHOS = [os.path.join(INICIALIZAR, "Maya.vbs"), os.path.join(AREA_DE_TRABALHO, "Maya.vbs")]

if len(sys.argv) > 1 and sys.argv[1] == "remover":
    for atalho in ATALHOS:
        if os.path.exists(atalho):
            os.remove(atalho)
    print("Atalhos removidos. A Maya não vai mais iniciar com o Windows.")
    sys.exit()

# pythonw.exe roda sem abrir a janela preta
pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(pythonw):
    sys.exit("Não achei o pythonw.exe. Ative o ambiente antes: .venv\\Scripts\\activate")
main = os.path.join(PASTA, "main.py")
conteudo = f'CreateObject("WScript.Shell").Run """{pythonw}"" ""{main}""", 0, False\n'

for atalho in ATALHOS:
    if os.path.isdir(os.path.dirname(atalho)):
        with open(atalho, "w", encoding="utf-8") as f:
            f.write(conteudo)

print("Pronto!")
print(" - A Maya vai iniciar sozinha quando o Windows ligar.")
print(" - Também criei o atalho 'Maya' na Área de Trabalho.")
print(" - Para fechar: clique com o botão direito no ícone azul perto do relógio > Sair.")
print("Abrindo a Maya agora...")
subprocess.Popen(["wscript", ATALHOS[0]])

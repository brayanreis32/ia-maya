"""
Faz a Maya iniciar sozinha, em segundo plano, quando o Windows liga.
    python instalar_inicializacao.py           ativa
    python instalar_inicializacao.py remover   desativa
"""

import os
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))
INICIALIZAR = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
ATALHO = os.path.join(INICIALIZAR, "maya.vbs")

if len(sys.argv) > 1 and sys.argv[1] == "remover":
    if os.path.exists(ATALHO):
        os.remove(ATALHO)
    print("A Maya não vai mais iniciar com o Windows.")
    sys.exit()

# pythonw.exe roda sem abrir janela preta
pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
main = os.path.join(PASTA, "main.py")
with open(ATALHO, "w", encoding="utf-8") as f:
    f.write(f'CreateObject("WScript.Shell").Run """{pythonw}"" ""{main}""", 0, False\n')

print(f"Pronto! A Maya vai iniciar com o Windows. (Atalho criado em {ATALHO})")
print("Para parar a Maya agora: Gerenciador de Tarefas > Detalhes > finalizar 'pythonw.exe'.")

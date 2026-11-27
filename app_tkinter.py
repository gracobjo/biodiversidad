import sys
from pathlib import Path

ruta_src = Path(__file__).resolve().parent / "src"
if str(ruta_src) not in sys.path:
    sys.path.insert(0, str(ruta_src))

from gui_tk import lanzar_gui

if __name__ == "__main__":
    lanzar_gui()
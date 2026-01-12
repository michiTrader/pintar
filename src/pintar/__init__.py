from .core import dye, Brush, Stencil, pstr, print
from .colors import RGB, HSL, HEX
from .ansi import FORE, BACK, STYLE

__version__ = "0.7.1"
__author__ = "michiTrader"
__description__ = "librería Python para colorear texto en terminal con códigos ANSI"

__all__ =["dye", "Brush", "Stencil", "RGB", "HSL", "HEX", "pstr", "print", "FORE", "BACK", "STYLE"]

# TODO: Se llama demasiado al caracter ansi \033 o \x1b: el sistema puede funcionar sin tanto caracter
# TODO: ..
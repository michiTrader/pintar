from .core import dye, Brush, Stencil
from .colors import RGB, HSL, HEX

__version__ = "0.6.1"
__author__ = "michiTrader"
__description__ = "librería Python para colorear texto en terminal con códigos ANSI"

__all__ =["dye", "Brush", "Stencil", "RGB", "HSL", "HEX"]

# TODO: Se llama demasiado al caracter ansi \033 o \x1b: el sistema puede funcionar sin tanto caracter
# TODO: ..
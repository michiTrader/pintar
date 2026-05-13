# modulo ansi.py



CSI = '\033['
OSC = '\033]'
BEL = '\a'

def code_to_chars(code):
    return CSI + str(code) + 'm'

def set_title(title):
    return OSC + '2;' + title + BEL 

def clear_screen(mode=2):
    return CSI + str(mode) + 'J'

def clear_line(mode=2):
    return CSI + str(mode) + 'K'

class AnsiCodes(object):
    def __init__(self):
        """ Lo convierte al caracter Ansi usando el token del color o estilo"""
        for name in dir(self):
            if not name.startswith('_'):
                value = getattr(self, name)
                setattr(self, name, code_to_chars(value))

    def __iter__(self):
        """ Iterar sobre los nombres de los colores y estilos """
        for name in dir(self):
            if not name.startswith('_'):
                yield name

    # def __iter__(cls):
    #     """ Iterar sobre los nombres de los colores y estilos """
    #     return iter(
    #         v for k, v in cls.__dict__.items()
    #         if not k.startswith("_") and not callable(v)
    #     )

class AnsiFore(AnsiCodes):
    BLACK           = 30
    RED             = 31
    GREEN           = 32
    YELLOW          = 33
    BLUE            = 34
    MAGENTA         = 35
    CYAN            = 36
    WHITE           = 37
    RESET           = 39

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 90
    LIGHTRED_EX     = 91
    LIGHTGREEN_EX   = 92
    LIGHTYELLOW_EX  = 93
    LIGHTBLUE_EX    = 94
    LIGHTMAGENTA_EX = 95
    LIGHTCYAN_EX    = 96
    LIGHTWHITE_EX   = 97

class AnsiBack(AnsiCodes):
    BLACK           = 40
    RED             = 41
    GREEN           = 42
    YELLOW          = 43
    BLUE            = 44
    MAGENTA         = 45
    CYAN            = 46
    WHITE           = 47
    RESET           = 49

    # These are fairly well supported, but not part of the standard.
    LIGHTBLACK_EX   = 100
    LIGHTRED_EX     = 101
    LIGHTGREEN_EX   = 102
    LIGHTYELLOW_EX  = 103
    LIGHTBLUE_EX    = 104
    LIGHTMAGENTA_EX = 105
    LIGHTCYAN_EX    = 106
    LIGHTWHITE_EX   = 107

class AnsiStyle(AnsiCodes):
    RESET_ALL = 0
    BOLD      = 1
    DIM       = 2
    ITALIC    = 3
    UNDERLINE = 4
    BLINK     = 5
    BLINK2    = 6
    REVERSE   = 7
    CONCEAL   = 8
    STRIKE    = 9
    
    UNDERLINE2 = 21
    NORMAL    = 22
    NOT_BOLD = 22
    NOT_DIM = 22
    NOT_ITALIC = 23
    NOT_UNDERLINE = 24
    NOT_BLINK = 25
    NOT_BLINK2 = 26
    NOT_REVERSE = 27
    NOT_CONCEAL = 28
    NOT_STRIKE = 29

    FRAME = 51
    ENCIRCLE = 52
    OVERLINE = 53
    NOT_FRAME_NOT_ENCIRCLE = 54
    NOT_OVERLINE = 55

class AnsiCursor(object):
    def UP(self, n=1):
        return CSI + str(n) + 'A'
    def DOWN(self, n=1):
        return CSI + str(n) + 'B'
    def FORWARD(self, n=1):
        return CSI + str(n) + 'C'
    def BACK(self, n=1):
        return CSI + str(n) + 'D'
    def POS(self, x=1, y=1):
        return CSI + str(y) + ';' + str(x) + 'H'

FORE = AnsiFore()
BACK = AnsiBack()
STYLE = AnsiStyle()


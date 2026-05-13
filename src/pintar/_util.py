# modulo _util.py



def dict_deep_update(d, u):
    if u is None:
        return d

    for k, v in u.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            dict_deep_update(d[k], v)
        else:
            d[k] = v
    return d

class AnsiTokens(type):
    def __iter__(cls):
        return iter(
            v for k, v in cls.__dict__.items()
            if not k.startswith("_") and not callable(v)
        )

class STYLES(metaclass=AnsiTokens):
    BOLD = "bold"
    UNDERLINE = "underline"
    ITALIC = "italic"
    STRIKETHROUGH = "strikethrough"
    NORMAL = "normal"

class COLORS(metaclass=AnsiTokens):
    BLACK = "#000000"
    WHITE = "#FFFFFF"
    GRAY = "#C4C4C4"
    DARK_GRAY = "#808080"
    
    RED = "#FE1616"
    GREEN = "#16FE16"
    BLUE = "#1616FE"
    YELLOW = "#FEEF16"
    CYAN = "#16FEEF"
    MAGENTA = "#FE16EF"
    
    LIGHT_RED = "#FF4D4D"
    LIGHT_GREEN = "#4DFF4D"
    LIGHT_BLUE = "#4D4DFF"
    LIGHT_YELLOW = "#FFFF4D"
    LIGHT_CYAN = "#4DFFFF"
    LIGHT_MAGENTA = "#FF4DFF"
    LIGHT_GRAY = "#D3D3D3"
    
    DARK_RED = "#800000"
    DARK_GREEN = "#008000"
    DARK_BLUE = "#000080"
    DARK_YELLOW = "#808000"
    DARK_CYAN = "#008080"
    DARK_MAGENTA = "#800080"



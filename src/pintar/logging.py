"""
tradear_logging.py  v1.0
========================
Logger con color para estrategias de trading.
Usa `pintar` (colors.py + ansi.py) para toda la generación de color.

COLORES SOPORTADOS en fore y bg
────────────────────────────────
    str hex    "#FF6B35", "#0ECB81", "#aaa"
    RGB obj    RGB(14, 203, 129)
    HEX obj    HEX("#0ECB81")
    HSL obj    HSL(152, 0.82, 0.43)
    tuple      (14, 203, 129)          ← se convierte a RGB automáticamente
    int        42                      ← índice ANSI 256-color
    None       sin color

ESTILOS en style
────────────────
    "bold", "italic", "underline", "dim", "strike", "reverse"
    o cualquier nombre definido en AnsiStyle (BOLD, ITALIC, …)

USO RÁPIDO
──────────
    from tradear_logging import get_logger
    log = get_logger("mi_modulo")
    log.info("backtest iniciado")
    log.warning("drawdown: %.2f%%", 12.5)

PERSONALIZACIÓN
───────────────
    from tradear_logging import get_logger, Theme
    from pintar.colors import RGB

    log = get_logger("bt", theme=Theme(overrides={
        "INFO":    {"message": ("#0ECB81", None, "bold")},
        "WARNING": {"message": ("#F59E0B", None, None)},
        "ERROR":   {"message": (RGB(246,70,93), None, "bold")},
        "CRITICAL":{"levelname": ("#fff", "#C0392B", "bold"),
                    "message":   ("#fff", "#C0392B", "bold")},
    }))

INTEGRACIÓN CON Strategy
─────────────────────────
Añadir en Strategy:

    @property
    def log(self) -> logging.Logger:
        if not hasattr(self, "_logger") or self._logger is None:
            from tradear_logging import get_logger
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

ARQUITECTURA
────────────
    _resolve_color(c, is_bg) → str ANSI
        Acepta hex str, RGB, HEX, HSL, tuple, int ANSI-256, None.
        Usa True Color (38;2;R;G;B) para todo excepto int (que usa 38;5;N).

    Theme
        Paleta plana: nivel → campo → (fore, bg, style).
        palette_for(nivel) fusiona DEFAULT ← nivel ← overrides ← fields en O(1).

    FieldDef
        Define un campo personalizado: valor fijo o dinámico (source=LogRecord attr)
        con su propia paleta por nivel. Se registra en Theme.fields y el sistema
        lo inyecta automáticamente en palette_for() y en PintarFormatter.format().

    get_logger / add_file_handler — API pública.
"""

from __future__ import annotations

import time
import logging
import sys
from dataclasses import dataclass, field

# ── Importar pintar ───────────────────────────────────────────────────────────
from pintar.colors import RGB, HEX, HSL, Color
from pintar.ansi import FORE, BACK, STYLE

_RESET: str = STYLE.RESET_ALL   # "\033[0m"

# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — RESOLUCIÓN DE COLOR (toda la lógica en un solo lugar)
# ──────────────────────────────────────────────────────────────────────────────

# Tipo aceptado en los campos fore / bg de la paleta
_ColorInput = str | tuple[int, int, int] | RGB | HEX | HSL | int | None


def _to_rgb(color: _ColorInput) -> "RGB | None":
    """
    Normaliza cualquier formato de color a RGB.

    Conversiones:
        None              → None
        RGB               → mismo objeto
        HEX / HSL         → .to_rgb()
        str "#..."        → RGB.from_hex_string()
        tuple (r, g, b)   → RGB(*tuple)
        int               → None  (los índices ANSI-256 se tratan aparte)
    """
    if color is None:
        return None
    if isinstance(color, RGB):
        return color
    if isinstance(color, (HEX, HSL)):
        return color.to_rgb()
    if isinstance(color, str):
        return RGB.from_hex_string(color)
    if isinstance(color, tuple):
        return RGB(*color)
    return None   # int → se maneja en _resolve_color


def _resolve_color(color: _ColorInput, is_bg: bool = False) -> str:
    """
    Convierte un color a su secuencia ANSI de escape completa.

    Estrategia:
        · RGB / hex / tuple → True Color 24-bit  \033[38;2;R;G;Bm  (fore)
                                                  \033[48;2;R;G;Bm  (bg)
        · int (0-255)       → ANSI 256-color      \033[38;5;Nm      (fore)
                                                   \033[48;5;Nm      (bg)
        · None              → ""  (sin color)
    """
    if color is None:
        return ""

    # Índice ANSI-256: usa 38;5 / 48;5
    if isinstance(color, int):
        plane = 48 if is_bg else 38
        return f"\033[{plane};5;{color}m"

    rgb = _to_rgb(color)
    if rgb is None:
        return ""

    plane = 48 if is_bg else 38
    return f"\033[{plane};2;{rgb.r};{rgb.g};{rgb.b}m"


def _resolve_style(style: str | None) -> str:
    """
    Convierte un nombre de estilo a su secuencia ANSI.

    Busca en AnsiStyle por nombre en mayúsculas: "bold" → STYLE.BOLD.
    Si no encuentra nada retorna "".
    """
    if not style:
        return ""
    attr = style.upper()
    code = getattr(STYLE, attr, None)
    return code or ""


def _colorize(text: str, fore: _ColorInput, bg: _ColorInput, style: str | None) -> str:
    """Aplica color y estilo ANSI a `text`. Si todo es None retorna `text` sin modificar."""
    code = _resolve_style(style) + _resolve_color(fore, False) + _resolve_color(bg, True)
    if not code:
        return text
    return f"{code}{text}{_RESET}"


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — PALETA POR DEFECTO
# ──────────────────────────────────────────────────────────────────────────────

# Estructura: nivel → campo → (fore, bg, style)
# fore y bg aceptan cualquier _ColorInput.
# Solo 2 niveles de acceso (nivel → campo).

_ColorSpec = tuple[_ColorInput, _ColorInput, str | None]

_DEFAULT_PALETTE: dict[str, dict[str, _ColorSpec]] = {
    "DEFAULT": {
        "asctime":   ("#4A5568", None, None),
        "bar":       ("#4A5568", None, None),
        "levelname": ("#CBD5E0", None, None),
        "name":      ("#63B3ED", None, None),
        "message":   ("#E2E8F0", None, None),
    },
    "DEBUG": {
        "asctime":   ("#4A5568", None, None),
        "bar":       ("#4A5568", None, None),
        "levelname": ("#718096", None, "dim"),
        "name":      ("#718096", None, None),
        "message":   ("#718096", None, None),
    },
    "INFO": {
        "asctime":   ("#4A5568", None, None),
        "bar":       ("#4A5568", None, None),
        "levelname": ("#0ECB81", None, "bold"),
        "name":      ("#63B3ED", None, None),
        "message":   ("#E2E8F0", None, None),
    },
    "WARNING": {
        "asctime":   ("#4A5568",  None, None),
        "bar":       ("#4A5568",  None, None),
        "levelname": ("#F59E0B",  None, "bold"),
        "name":      ("#F59E0B",  None, None),
        "message":   ("#FBD38D",  None, None),
    },
    "ERROR": {
        "asctime":   ("#4A5568", None, None),
        "bar":       ("#4A5568", None, None),
        "levelname": ("#F6465D", None, "bold"),
        "name":      ("#FC8181", None, None),
        "message":   ("#F6465D", None, None),
    },
    "CRITICAL": {
        "asctime":   ("#FFFFFF", "#9B2335", None),
        "bar":       ("#FFFFFF", "#9B2335", None),
        "levelname": ("#FFFFFF", "#9B2335", "bold"),
        "name":      ("#FFFFFF", "#9B2335", None),
        "message":   ("#FFFFFF", "#9B2335", "bold"),
    },
}

_MAX_LEVEL_LEN: int = max(len(k) for k in logging._nameToLevel)
_DEFAULT_FMT    = "{asctime} {bar} {levelname} {bar} {name} - {message}"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — FIELD DEF + THEME
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class FieldDef:
    """
    Define un campo personalizado inyectable en el fmt del logger.

    Parámetros
    ──────────
    value   : carácter o texto fijo que se mostrará. Ej: "→", "●", "▶".
              Si `source` está definido, `value` se usa solo como fallback.
    palette : colores por nivel. Acepta las claves "DEFAULT", "INFO", "WARNING",
              "ERROR", "CRITICAL", "DEBUG". Cada valor es (fore, bg, style).
              Si un nivel no tiene entrada, cae en "DEFAULT". Si tampoco hay
              "DEFAULT", el campo se muestra sin color.
    source  : nombre de un atributo de LogRecord para usar su valor dinámico.
              Ej: "threadName", "process", "filename", "lineno".
              Si es None, siempre se usa `value`.

    Ejemplo
    ───────
        FieldDef(
            value="→",
            palette={
                "DEFAULT":  ("#4A5568", None, None),
                "INFO":     ("#0ECB81", None, "bold"),
                "WARNING":  ("#F59E0B", None, None),
                "ERROR":    ("#F6465D", None, "bold"),
                "CRITICAL": ("#FFFFFF", "#9B2335", "bold"),
            }
        )

        # Campo dinámico — muestra el nombre del thread
        FieldDef(
            value="-",
            source="threadName",
            palette={"DEFAULT": ("#4A5568", None, "dim")},
        )
    """
    value: str
    palette: dict[str, _ColorSpec] = field(default_factory=dict)
    source: str | None = None

    def resolve_value(self, record: "logging.LogRecord") -> str:
        """Devuelve el valor del campo para este registro."""
        if self.source:
            return str(getattr(record, self.source, self.value))
        return self.value

    def spec_for(self, level_name: str) -> _ColorSpec:
        """Devuelve (fore, bg, style) para el nivel dado, con fallback a DEFAULT."""
        return (
            self.palette.get(level_name)
            or self.palette.get("DEFAULT")
            or (None, None, None)
        )


@dataclass
class Theme:
    """
    Paleta de color para el formatter del logger.

    Parámetros
    ──────────
    overrides : dict con el mismo esquema que _DEFAULT_PALETTE.
                Solo los niveles/campos a personalizar. Se fusiona encima de
                DEFAULT ← nivel ← overrides, por lo que siempre hay un fallback.

                Ejemplo — colores hex y RGB mezclados:
                    Theme(overrides={
                        "INFO":    {"message": ("#0ECB81", None, "bold")},
                        "WARNING": {"message": ((245,158,11), None, None)},
                        "ERROR":   {"message": (RGB(246,70,93), None, "bold")},
                    })

    fmt      : formato del mensaje (estilo '{').
               Campos disponibles: asctime, bar, levelname, name, message,
               más cualquier campo definido en `fields`.
    datefmt  : formato de la fecha para asctime.
    dye      : False → salida sin color ANSI (para handlers de archivo).
    fields   : dict de campos personalizados nombre → FieldDef.
               Cada campo se inyecta automáticamente en el fmt y en la paleta.

               Ejemplo:
                   Theme(
                       fmt="{asctime} {bar} {levelname} {arrow} {name} - {message}",
                       fields={
                           "arrow": FieldDef(
                               value="→",
                               palette={
                                   "DEFAULT":  ("#4A5568", None, None),
                                   "INFO":     ("#0ECB81", None, "bold"),
                                   "WARNING":  ("#F59E0B", None, None),
                                   "ERROR":    ("#F6465D", None, "bold"),
                                   "CRITICAL": ("#FFFFFF", "#9B2335", "bold"),
                               }
                           ),
                       }
                   )
    """
    overrides: dict[str, dict[str, _ColorSpec]] = field(default_factory=dict)
    fmt: str = _DEFAULT_FMT
    datefmt: str = _DEFAULT_DATEFMT
    dye: bool = True
    fields: dict[str, "FieldDef"] = field(default_factory=dict)

    def palette_for(self, level_name: str) -> dict[str, _ColorSpec]:
        """
        Devuelve campo→(fore,bg,style) para el nivel dado.
        Fusiona: DEFAULT ← nivel ← overrides ← fields del usuario.
        """
        base = dict(_DEFAULT_PALETTE.get("DEFAULT", {}))
        base.update(_DEFAULT_PALETTE.get(level_name, {}))
        base.update(self.overrides.get(level_name, {}))
        # Inyectar campos personalizados con su spec para este nivel
        for field_name, fdef in self.fields.items():
            base[field_name] = fdef.spec_for(level_name)
        return base

    def undyed(self) -> "Theme":
        """Copia sin color — para handlers de archivo."""
        return Theme(self.overrides, self.fmt, self.datefmt, dye=False, fields=self.fields)


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 4 — FORMATTER
# ──────────────────────────────────────────────────────────────────────────────

class PintarFormatter(logging.Formatter):
    """
    Formatter con color que:
    · Pre-compila los formatos por nivel en __init__ — no crea objetos en format().
    · Usa pintar (RGB, HEX, HSL, ANSI) para la resolución de color.
    · Soporta hex, RGB, HSL, tuple, int ANSI-256 y None en fore/bg.
    """

    def __init__(self, theme: Theme | None = None):
        self._theme = theme or Theme()
        super().__init__(
            fmt=self._theme.fmt,
            datefmt=self._theme.datefmt,
            style="{",
            validate=False,
        )
        # self.converter = time.datefmt
        self._level_fmts: dict[int, str] = self._build_level_fmts()

    def _build_level_fmts(self) -> dict[int, str]:
        """
        Genera el formato coloreado para cada nivel numérico de logging.
        Llamado una sola vez en __init__.
        """
        fmts: dict[int, str] = {}
        for name, num in logging._nameToLevel.items():
            palette = self._theme.palette_for(name)
            fmts[num] = self._apply_palette(self._theme.fmt, palette)
        return fmts

    def _apply_palette(self, fmt: str, palette: dict[str, _ColorSpec]) -> str:
        """
        Sustituye cada {campo} del formato por su versión coloreada.
        Si dye=False retorna el formato sin modificar.
        """
        if not self._theme.dye:
            return fmt

        result = fmt
        for field_name, (fore, bg, style) in palette.items():
            placeholder = "{" + field_name + "}"
            if placeholder in result:
                colored = _colorize(placeholder, fore, bg, style)
                result = result.replace(placeholder, colored)
        return result

    def format(self, record: logging.LogRecord) -> str:
        # Campos built-in extra
        if not hasattr(record, "bar"):
            record.bar = "│"   # U+2502 — más elegante que |

        # Poblar campos personalizados automáticamente desde FieldDef
        for field_name, fdef in self._theme.fields.items():
            setattr(record, field_name, fdef.resolve_value(record))

        record.levelname = record.levelname.ljust(_MAX_LEVEL_LEN)
        record.asctime   = self.formatTime(record, self.datefmt)
        record.message   = record.getMessage()

        fmt = self._level_fmts.get(record.levelno, self._level_fmts[logging.INFO])
        result = fmt.format_map(record.__dict__)

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            result = f"{result}\n{record.exc_text}"
        if record.stack_info:
            result = f"{result}\n{self.formatStack(record.stack_info)}"

        return result


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 5 — HANDLERS
# ──────────────────────────────────────────────────────────────────────────────

class PintarStreamHandler(logging.StreamHandler):
    """
    Handler de consola con color via pintar.

    Parámetros
    ──────────
    stream : stream de salida (default stdout)
    theme  : Theme o dict de overrides. Si es dict se wrappea en Theme(overrides=...).
    """
    def __init__(self, stream=None, theme: "Theme | dict | None" = None):
        super().__init__(stream or sys.stdout)
        if isinstance(theme, dict):
            theme = Theme(overrides=theme)
        elif theme is None:
            theme = Theme()
        self.setFormatter(PintarFormatter(theme))


class PintarFileHandler(logging.FileHandler):
    """
    Handler de archivo sin color ANSI.
    Fuerza dye=False independientemente del Theme recibido.
    """
    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: str | None = None,
        delay: bool = False,
        errors: str | None = None,
        theme: "Theme | dict | None" = None,
    ):
        super().__init__(filename, mode=mode, encoding=encoding, delay=delay, errors=errors)
        if isinstance(theme, dict):
            theme = Theme(overrides=theme, dye=False)
        elif isinstance(theme, Theme):
            theme = theme.undyed()
        else:
            theme = Theme(dye=False)
        self.setFormatter(PintarFormatter(theme))


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 6 — API PÚBLICA
# ──────────────────────────────────────────────────────────────────────────────

def get_logger(
    name: str,
    level: int = logging.DEBUG,
    theme: "Theme | dict | None" = None,
    stream=None,
) -> logging.Logger:
    """
    Crea o recupera un logger con PintarStreamHandler ya configurado.

    Si el logger `name` ya tiene handlers no añade nuevos (evita duplicados
    en llamadas repetidas o en código recargado en notebooks).

    Parámetros
    ──────────
    name   : nombre del logger. Dentro de Strategy usar self.__class__.__name__.
    level  : nivel mínimo (default DEBUG — Strategy puede filtrar con WARNING).
    theme  : Theme personalizado o dict de overrides parciales.
    stream : stream de salida (default stdout).

    Ejemplo
    ───────
    >>> log = get_logger("BtcStrategy")
    >>> log.info("señal LONG → precio=%.2f", 45230.5)
    >>> log.warning("drawdown: %.2f%%", 8.3)
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        return logger

    logger.setLevel(level)
    logger.propagate = False

    if isinstance(theme, dict):
        theme = Theme(overrides=theme)

    logger.addHandler(PintarStreamHandler(stream=stream, theme=theme))
    return logger


def add_file_handler(
    logger: logging.Logger,
    filename: str,
    level: int = logging.DEBUG,
    theme: "Theme | dict | None" = None,
) -> logging.FileHandler:
    """
    Añade un handler de archivo (sin color) al logger existente.

    Ejemplo
    ───────
    >>> log = get_logger("bt")
    >>> add_file_handler(log, "backtest.log")
    """
    handler = PintarFileHandler(filename, theme=theme)
    handler.setLevel(level)
    logger.addHandler(handler)
    return handler


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 7 — SNIPPET PARA STRATEGY
# ──────────────────────────────────────────────────────────────────────────────
#
#   En strategy.py — añadir a la clase Strategy:
#
#   @property
#   def log(self) -> logging.Logger:
#       """Logger con color listo para usar. Nombre = nombre de la clase."""
#       if not hasattr(self, "_logger") or self._logger is None:
#           from tradear_logging import get_logger
#           self._logger = get_logger(self.__class__.__name__)
#       return self._logger
#
# ──────────────────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────────────────
# SECCIÓN 8 — DEMO
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pintar.colors import RGB

    print("─── Tema por defecto ─────────────────────────────────────────")
    log = get_logger("BtcStrategy")
    log.debug("tick procesado: 44230.5")
    log.info("señal LONG detectada → precio=44230.5  size=0.01")
    log.warning("drawdown alto: 8.3%%")
    log.error("orden rechazada: fondos insuficientes")
    log.critical("broker desconectado — loop detenido")

    print("\n─── Colores hex personalizados ───────────────────────────────")
    hex_log = get_logger("HexDemo", theme=Theme(overrides={
        "INFO":    {"levelname": ("#0ECB81", None, "bold"),
                    "message":   ("#0ECB81", None, None)},
        "WARNING": {"levelname": ("#F59E0B", None, "bold"),
                    "message":   ("#F59E0B", None, None)},
        "ERROR":   {"levelname": ("#F6465D", None, "bold"),
                    "message":   ("#F6465D", None, "bold")},
    }))
    hex_log.info("orden ejecutada: BTCUSDT LONG 0.01")
    hex_log.warning("spread elevado: 8 pips")
    hex_log.error("timeout al enviar orden")

    print("\n─── Colores RGB (objeto pintar) ──────────────────────────────")
    rgb_log = get_logger("RgbDemo", theme=Theme(overrides={
        "INFO": {
            "levelname": (RGB(46, 204, 113), None, "bold"),
            "message":   (RGB(46, 204, 113), None, None),
        },
    }))
    rgb_log.info("señal confirmada con RGB de pintar")

    print("\n─── Tupla (r,g,b) ────────────────────────────────────────────")
    tuple_log = get_logger("TupleDemo", theme=Theme(overrides={
        "INFO": {"message": ((100, 200, 255), None, None)},
    }))
    tuple_log.info("mismo resultado con tupla")

    print("\n─── ANSI 256-color (int) ─────────────────────────────────────")
    ansi_log = get_logger("AnsiDemo", theme=Theme(overrides={
        "INFO": {"levelname": (82, None, "bold"),   # verde brillante 256
                 "message":   (220, None, None)},   # amarillo pálido 256
    }))
    ansi_log.info("usando índices ANSI de 8 bits")

    print("\n─── Fondo hex ────────────────────────────────────────────────")
    bg_log = get_logger("BgDemo", theme=Theme(overrides={
        "CRITICAL": {
            "levelname": ("#FFFFFF", "#9B2335", "bold"),
            "message":   ("#FFFFFF", "#9B2335", "bold"),
        },
    }))
    bg_log.critical("stop loss global activado")

    print("\n─── Sin color (para archivo) ─────────────────────────────────")
    plain_log = get_logger("PlainDemo", theme=Theme(dye=False))
    plain_log.info("sin secuencias ANSI — listo para archivo")

    print("\n─── Formato personalizado ────────────────────────────────────")
    short_log = get_logger("Short", theme=Theme(
        fmt="{levelname} {bar} {message}",
        overrides={"INFO": {"levelname": ("#0ECB81", None, "bold")}},
    ))
    short_log.info("formato compacto sin timestamp")

    print("\n─── Campos personalizados con FieldDef ───────────────────────")
    field_log = get_logger("FieldDemo", theme=Theme(
        fmt="{asctime} {bar} {levelname} {arrow} {name} - {message} {dot}",
        fields={
            "arrow": FieldDef(
                value="→",
                palette={
                    "DEFAULT":  ("#4A5568", None, None),
                    "DEBUG":    ("#718096", None, "dim"),
                    "INFO":     ("#0ECB81", None, "bold"),
                    "WARNING":  ("#F59E0B", None, None),
                    "ERROR":    ("#F6465D", None, "bold"),
                    "CRITICAL": ("#FFFFFF", "#9B2335", "bold"),
                }
            ),
            "dot": FieldDef(
                value="●",
                palette={
                    "DEFAULT":  ("#4A5568", None, "dim"),
                    "INFO":     ("#0ECB81", None, None),
                    "WARNING":  ("#F59E0B", None, None),
                    "ERROR":    ("#F6465D", None, None),
                    "CRITICAL": ("#FFFFFF", "#9B2335", None),
                }
            ),
        }
    ))
    field_log.debug("campo personalizado en debug")
    field_log.info("campo personalizado en info")
    field_log.warning("campo personalizado en warning")
    field_log.error("campo personalizado en error")
    field_log.critical("campo personalizado en critical")

    print("\n─── Campo dinámico (source=LogRecord attr) ───────────────────")
    dynamic_log = get_logger("DynDemo", theme=Theme(
        fmt="{asctime} {bar} {levelname} {bar} {name} - {message}  {thread}",
        fields={
            "thread": FieldDef(
                value="-",
                source="threadName",
                palette={"DEFAULT": ("#4A5568", None, "dim")},
            ),
        }
    ))
    dynamic_log.info("muestra el nombre del thread automáticamente")
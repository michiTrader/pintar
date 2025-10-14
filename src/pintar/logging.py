import sys
import logging
import json
import re
from pathlib import Path
from string import Template

from .core import Stencil
from .colors import HEX, RGB, HSL, Color
from ._util import dict_deep_update

# Load default theme configuration
CONFIG_PATH = Path(__file__).resolve().parent / 'config/pintar_custom_log_theme.json'
with open(CONFIG_PATH) as f:
    DEFAULT_COLOR_THEME = json.load(f)

DEFAULT_FORMAT = '{asctime} {bar} {levelname} {bar} {name} - {message}'

LOG_RECORD_KEYS: tuple = (
    "name", "levelno", "levelname",
    "pathname", "filename", "module",
    "lineno",  "funcName", "created",
    "asctime",  "msecs", "relativeCreated",
    "thread",  "threadName",  "taskName",
    "process",  "message",
)

class FormatStyle:
    """Enum-like class for format styles."""
    PERCENT = '%'
    BRACE = '{'
    DOLLAR = '$'
    
    PLACEHOLDERS = {
        PERCENT: '%({key})s',
        BRACE: '{{{key}}}',
        DOLLAR: '${key}'
    }
    
    REGEX_PATTERNS = {
        PERCENT: re.compile(r'%\((\w+)\)\w?'),
        BRACE: re.compile(r'\{(\w+)}'),
        DOLLAR: re.compile(r'\$(\w+)')
    }

class Theme:
    """
        Gestiona los temas de color y el formato para los mensajes de registro.
        
        Args:
            color_config: Configuración de color adicional para sobrescribir los valores predeterminados
            fmt: Cadena de formato de registro (por ejemplo, '{asctime} {bar} {levelname} - {message}')
            style: Estilo de formato ('%', '{' o '$')
            apply_colors: Si se deben aplicar colores a la salida
    """
    def __init__(self, color_config: dict = None, fmt: str = None, 
                 style: str = '{', dye: bool = True):
        self._color_config = color_config or {}
        self._format_string = fmt or DEFAULT_FORMAT
        self._style = style
        self._dye = dye
        
        self._cached_level_formats = None
        self._color_theme = None

    def get_level_formats(self) -> dict:
        self._cached_level_formats = self._build_level_formats()
        return self._cached_level_formats
    
    def undyed(self):
        if not self._dye:
            return self
        return Theme(
            self._color_config, self._format_string,
            self._style, False,
        )

    @property
    def style(self) -> str:
        """Returns the format style."""
        return self._style
    
    @property
    def color_theme(self) -> dict:
        """Returns the merged color theme."""
        if self._color_theme is None:
            self._color_theme = dict_deep_update(DEFAULT_COLOR_THEME, self._color_config)
        return self._color_theme
    
    def _extract_format_keys(self) -> list:
        """Extracts placeholder keys used in the format string."""
        pattern = FormatStyle.REGEX_PATTERNS[self._style]
        return pattern.findall(self._format_string)
    
    def _get_all_placeholders(self) -> dict:
        """Returns a mapping of all available keys to their placeholders."""
        all_keys = LOG_RECORD_KEYS + ('bar',)
        placeholder_template = FormatStyle.PLACEHOLDERS[self._style]
        
        return {
            key: placeholder_template.format(key=key)
            for key in all_keys
        }
    
    def _get_used_placeholders(self) -> dict:
        """Returns only the placeholders actually used in the format string."""
        used_keys = self._extract_format_keys()
        all_placeholders = self._get_all_placeholders()
        
        return {
            key: placeholder
            for key, placeholder in all_placeholders.items()
            if key in used_keys
        }
    
    def _build_theme_for_level(self, level_name: str) -> dict:
        """Builds color theme configuration for a specific log level."""
        default_theme = self.color_theme.get('INFO', {})
        level_theme = self.color_theme.get(level_name, {})
        
        theme = default_theme.copy()
        theme.update(level_theme)
        return theme
    
    def _colorize_placeholder(self, placeholder: str, color_config: dict) -> str:
        """Applies color styling to a placeholder string."""
        if not self._dye:
            return placeholder
        
        return Stencil(string=placeholder).spray(
            fore=color_config.get('fore_color'),
            bg=color_config.get('bg_color'),
            style=color_config.get('style')
        )
    
    def _apply_format_substitution(self, colored_placeholders: dict) -> str:
        """Substitutes placeholders in format string with colored versions."""
        if self._style == FormatStyle.BRACE:
            return self._format_string.format(**colored_placeholders)
        elif self._style == FormatStyle.PERCENT:
            return self._format_string % colored_placeholders
        elif self._style == FormatStyle.DOLLAR:
            return Template(self._format_string).substitute(**colored_placeholders)
        
        raise ValueError(f"Unknown format style: {self._style}")
    
    def _build_level_formats(self) -> dict:
        """Builds formatted strings for all log levels."""
        used_placeholders = self._get_used_placeholders()
        available_levels = logging._nameToLevel
        
        level_formats = {}
        
        for level_name, level_number in available_levels.items():
            theme = self._build_theme_for_level(level_name)
            
            colored_placeholders = {}
            for key, placeholder in used_placeholders.items():
                color_config = theme.get(key, {})
                colored_placeholders[key] = self._colorize_placeholder(
                    placeholder, color_config
                )
            
            level_formats[level_number] = self._apply_format_substitution(
                colored_placeholders
            )
        
        return level_formats

class CustomFormatter(logging.Formatter):
    """
    Custom formatter that applies different formatting based on log level.
    """
    
    def __init__(self, fmt=None, datefmt=None, style='%', 
                 validate=True, defaults=None, theme: Theme = None):
        self._theme = theme or Theme()
        style = self._theme.style or style
        
        super().__init__(
            fmt=fmt, 
            datefmt=datefmt, 
            style=style, 
            validate=validate, 
            defaults=defaults
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record with level-specific styling."""
        # Add bar separator if not present
        if not hasattr(record, 'bar'):
            record.bar = '|'
        
        # Pad level name for alignment
        max_len_level_names = max([len(k) for k in logging._nameToLevel.keys()])
        record.levelname = record.levelname.ljust(max_len_level_names)
        
        # Get format string for this level
        theme_level_formats = self._theme.get_level_formats()
        fmt = theme_level_formats.get(
            record.levelno, 
            theme_level_formats[logging.INFO]
        )
        
        # Create temporary formatter with the selected format
        formatter = logging.Formatter(
            fmt=fmt,
            style=self._theme.style,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        return formatter.format(record)

class PintarStreamHandler(logging.StreamHandler):
    """
    StreamHandler that applies colored formatting to log messages.
    """
    
    def __init__(self, stream=None, theme: Theme | dict = None):
        super().__init__(stream or sys.stdout)
        self._theme = theme
        
        # Create theme if dictionary or None was passed
        if not isinstance(theme, Theme):
            self._theme = Theme(color_config=theme) if theme else Theme()
        
        # Set the custom formatter
        self.setFormatter(CustomFormatter(theme=self._theme))

class PintarFileHandler(logging.FileHandler):
    """
    StreamHandler that applies colored formatting to log messages.
    """
    
    def __init__(self, filename, mode='a', encoding=None, delay=False, errors=None, theme=None):
        super().__init__(filename=filename, mode=mode, encoding=encoding, delay=delay, errors=errors)
        self._theme = theme
        # Asugurar que el parametro theme sea un objeto Theme 
        if not isinstance(theme, Theme):
            self._theme = Theme(color_config=theme, dye=False) if theme else Theme(dye=False)
        
        # Set the custom formatter
        self.setFormatter(CustomFormatter(theme=self._theme.undyed()))



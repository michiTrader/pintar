import colorsys
from re import match
from abc import ABCMeta, abstractmethod, abstractclassmethod
from math import sqrt

class Color(metaclass=ABCMeta):
    """Clase base abstracta para representar colores genéricos."""

    def __repr__(self) -> str:
        return self.to_css()

    # ==============================
    # Métodos utilitarios
    # ==============================

    @staticmethod
    def clamp(value: float, maximum: float | None = None) -> float:
        """Limita un valor a un rango válido (0 a máximo opcional)."""
        value = max(value, 0)
        return min(value, maximum) if maximum is not None else value

    # ==============================
    # Métodos abstractos (deben implementarse)
    # ==============================

    @abstractmethod
    def copy(self) -> 'Color':
        """Devuelve una copia del color."""
        raise NotImplementedError

    @abstractclassmethod
    def from_hsl(cls, value: 'HSL') -> 'Color':
        """Crea un color a partir de un valor HSL."""
        raise NotImplementedError

    @abstractclassmethod
    def from_rgb(cls, value: 'RGB') -> 'Color':
        """Crea un color a partir de un valor RGB."""
        raise NotImplementedError

    @abstractmethod
    def to_css(self) -> str:
        """Devuelve una representación CSS del color."""
        raise NotImplementedError

    @abstractmethod
    def to_hsl(self) -> 'HSL':
        """Convierte el color actual a formato HSL."""
        raise NotImplementedError

    @abstractmethod
    def to_rgb(self) -> 'RGB':
        """Convierte el color actual a formato RGB."""
        raise NotImplementedError

    def to_ansi_index(self) -> int:
        """Convierte el color actual al índice ANSI más cercano (0-255)."""
        raise NotImplementedError



    # ==============================
    # Métodos de manipulación
    # ==============================

    def lighten(self, amount: float) -> 'Color':
        """Aclara el color aumentando su luminancia."""
        rgb = self.to_rgb()
        h, l, s = colorsys.rgb_to_hls(rgb.r / 255, rgb.g / 255, rgb.b / 255)
        l = self.clamp(l + amount, 1)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return self.from_rgb(RGB(round(r * 255), round(g * 255), round(b * 255), rgb.a))

    def darken(self, amount: float) -> 'Color':
        """Oscurece el color reduciendo su luminancia."""
        return self.lighten(-amount)

    def saturate(self, amount: float) -> 'Color':
        """Aumenta la saturación del color."""
        hsl = self.to_hsl()
        hsl.s = self.clamp(hsl.s + amount, 1)
        return self.from_hsl(hsl)

    def desaturate(self, amount: float) -> 'Color':
        """Reduce la saturación del color."""
        hsl = self.to_hsl()
        hsl.s = self.clamp(hsl.s - amount, 1)
        return self.from_hsl(hsl)

    def tint(self, amount: float) -> 'Color':
        """
        Mezcla el color con BLANCO (hace el color más claro).
        
        Args:
            amount: Cantidad de blanco a mezclar (0.0 a 1.0)
                   0.0 = color original
                   1.0 = blanco puro
        
        Ejemplo:
            rojo = RGB(255, 0, 0)
            rosa = rojo.tint(0.5)  # Mezcla 50% blanco
        """
        rgb = self.to_rgb()
        amount = self.clamp(amount, 1.0)
        
        # Interpolar hacia blanco (255, 255, 255)
        r = round(rgb.r + (255 - rgb.r) * amount)
        g = round(rgb.g + (255 - rgb.g) * amount)
        b = round(rgb.b + (255 - rgb.b) * amount)
        
        return self.from_rgb(RGB(r, g, b, rgb.a))

    def shade(self, amount: float) -> 'Color':
        """
        Mezcla el color con NEGRO (hace el color más oscuro).
        
        Args:
            amount: Cantidad de negro a mezclar (0.0 a 1.0)
                   0.0 = color original
                   1.0 = negro puro
        
        Ejemplo:
            rojo = RGB(255, 0, 0)
            rojo_oscuro = rojo.shade(0.5)  # Mezcla 50% negro
        """
        rgb = self.to_rgb()
        amount = self.clamp(amount, 1.0)
        
        # Interpolar hacia negro (0, 0, 0)
        r = round(rgb.r * (1 - amount))
        g = round(rgb.g * (1 - amount))
        b = round(rgb.b * (1 - amount))
        
        return self.from_rgb(RGB(r, g, b, rgb.a))

class RGB(Color):
    """Representa un color en formato RGB (0-255) + alpha opcional."""

    def __init__(self, r: int, g: int, b: int, a: float = 1.0) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.a = a
        
    # ==============================
    # Creación de instancias
    # ==============================

    def copy(self) -> 'RGB':
        return RGB(self.r, self.g, self.b, self.a)

    @classmethod
    def from_hsl(cls, value: 'HSL') -> 'RGB':
        return value.to_rgb()

    @classmethod
    def from_rgb(cls, value: 'RGB') -> 'RGB':
        return value.copy()

    @classmethod
    def from_tuple(cls, value: tuple) -> 'RGB':
        """Crea un RGB desde una tupla (r, g, b) o (r, g, b, a)."""
        if len(value) == 3:
            return RGB(*value)
        elif len(value) == 4:
            return RGB(*value)
        else:
            raise ValueError("La tupla debe tener 3 o 4 valores.")

    @classmethod
    def from_hex_string(cls, hex_string: str) -> 'RGB':
        """Crea un RGB desde una cadena hexadecimal (#RRGGBB o #RRGGBBAA)."""
        if isinstance(hex_string, str):
            if match(r"#([\da-fA-F]{2}){3,4}\Z", hex_string):
                r = int(hex_string[1:3], 16)
                g = int(hex_string[3:5], 16)
                b = int(hex_string[5:7], 16)
                a = int(hex_string[7:9], 16) / 255.0 if len(hex_string) > 7 else 1.0
                return RGB(r, g, b, a)

            if match(r"#[\da-fA-F]{3,4}\Z", hex_string):
                r = int(hex_string[1] * 2, 16)
                g = int(hex_string[2] * 2, 16)
                b = int(hex_string[3] * 2, 16)
                a = int(hex_string[4] * 2, 16) / 255.0 if len(hex_string) > 4 else 1.0
                return RGB(r, g, b, a)

        raise ValueError(f"'{hex_string}' no es un color hexadecimal válido.")

    @classmethod
    def from_ansi_index(cls, index: int) -> 'RGB':
        """Crea un color RGB a partir de un índice ANSI de 8 bits (0–255)."""
        if not 0 <= index <= 255:
            raise ValueError("El índice ANSI debe estar entre 0 y 255.")

        if index < 16:
            base_colors = [
                (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
                (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
                (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
                (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)
            ]
            r, g, b = base_colors[index]

        elif index < 232:
            index -= 16
            r = (index // 36) % 6
            g = (index // 6) % 6
            b = index % 6
            r = 55 + r * 40 if r > 0 else 0
            g = 55 + g * 40 if g > 0 else 0
            b = 55 + b * 40 if b > 0 else 0

        else:
            gray = 8 + (index - 232) * 10
            r = g = b = gray

        return cls(r, g, b)

    # ==============================
    # Conversión
    # ==============================

    def to_css(self) -> str:
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})" if self.a < 1.0 else f"rgb({self.r}, {self.g}, {self.b})"

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{int(round(self.a*255)):02x}" if self.a < 1.0 else f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_hsl(self) -> 'HSL':
        h, l, s = colorsys.rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        return HSL(h * 360, s, l, self.a)

    def to_rgb(self) -> 'RGB':
        return self.copy()

    def to_ansi_index(self) -> int:
        """Convierte un color RGB al índice ANSI más cercano (0–255)."""
        r, g, b = self.r, self.g, self.b

        if r == g == b:
            if r < 8:
                return 16
            if r > 248:
                return 231
            return round(((r - 8) / 247) * 24) + 232

        def to_ansi_component(v):
            if v < 75:
                return 0
            return (v - 35) // 40

        r_i = to_ansi_component(r)
        g_i = to_ansi_component(g)
        b_i = to_ansi_component(b)
        return 16 + (36 * r_i) + (6 * g_i) + b_i

    # ==============================
    # Propiedades
    # ==============================

    @property
    def brightness(self) -> float:
        """Calcula el brillo visual aproximado."""
        return sqrt(0.299*self.r**2 + 0.587*self.g**2 + 0.114*self.b**2) / 255

    @property
    def luminance(self) -> float:
        """Calcula la luminancia percibida."""
        return (0.2126*self.r**2.2 + 0.7152*self.g**2.2 + 0.0722*self.b**2.2) / 255**2.2

    @property
    def rgb_tuple(self) -> tuple:
        return (self.r, self.g, self.b)



    # ==============================
    # Métodos de manipulación
    # ==============================

    def saturate(self, amount: float) -> 'RGB':
        """Aumenta la saturación del color."""
        hsl = self.to_hsl()
        hsl.s = self.clamp(hsl.s + amount, 1)
        rgb = RGB.from_hsl(hsl)
        return rgb

    def desaturate(self, amount: float) -> 'RGB':
        """Disminuye la saturación del color."""
        hsl = self.to_hsl()
        hsl.s = self.clamp(hsl.s - amount, 1)
        rgb = RGB.from_hsl(hsl)
        return rgb

class HSL(Color):
    """Representa un color en formato HSL (Hue, Saturation, Lightness)."""

    def __init__(self, h: float, s: float, l: float, a: float = 1.0) -> None:
        # Normalizar el hue al rango 0-360
        self.h = h % 360
        # Clamp saturation y lightness al rango 0-1
        self.s = max(0.0, min(1.0, s))
        self.l = max(0.0, min(1.0, l))
        self.a = max(0.0, min(1.0, a))

    def copy(self) -> 'HSL':
        return HSL(self.h, self.s, self.l, self.a)

    @classmethod
    def from_hsl(cls, value: 'HSL') -> 'HSL':
        return value.copy()

    @classmethod
    def from_rgb(cls, value: RGB) -> 'HSL':
        return value.to_hsl()

    def to_css(self) -> str:
        base = f"hsl({self.h:.0f}, {self.s*100:.1f}%, {self.l*100:.1f}%)"
        return base if self.a == 1.0 else f"hsla({self.h:.0f}, {self.s*100:.1f}%, {self.l*100:.1f}%, {self.a})"

    def to_hsl(self) -> 'HSL':
        return self.copy()

    def to_rgb(self) -> RGB:
        r, g, b = colorsys.hls_to_rgb(self.h / 360, self.l, self.s)
        return RGB(round(r * 255), round(g * 255), round(b * 255), self.a)

    def to_hex(self):
        return self.to_rgb().to_hex()

    def to_ansi_index(self):
        return self.to_rgb().to_ansi_index()

    def lighten(self, amount: float) -> 'HSL':
        hsl = self.copy()
        hsl.l = self.clamp(hsl.l + amount, 1)
        return self.from_hsl(hsl)

    def darken(self, amount: float) -> 'HSL':
        return self.lighten(-amount)

    def saturate(self, amount: float) -> 'HSL':
        hsl = self.copy()
        hsl.s = self.clamp(hsl.s + amount, 1)
        return self.from_hsl(hsl)

    def desaturate(self, amount: float) -> 'HSL':
        return self.saturate(-amount)

class HEX(Color):
    """Representa un color en formato hexadecimal (#RRGGBB o #RRGGBBAA)."""

    def __init__(self, value: str) -> None:
        """
        Inicializa un color HEX desde una cadena.
        
        Args:
            value: String hexadecimal (#RGB, #RRGGBB, #RGBA, #RRGGBBAA)
        
        Ejemplos:
            HEX('#F00')        -> Rojo corto
            HEX('#FF0000')     -> Rojo largo
            HEX('#FF0000FF')   -> Rojo con alpha
            HEX('#F00F')       -> Rojo corto con alpha
        """
        if not isinstance(value, str):
            raise TypeError("El valor debe ser una cadena de texto")
        
        if not value.startswith('#'):
            raise ValueError("El color hexadecimal debe comenzar con '#'")
        
        # Validar y normalizar el formato
        hex_part = value[1:]  # Remover el '#'
        
        if not match(r'^[\da-fA-F]+$', hex_part):
            raise ValueError(f"'{value}' contiene caracteres no hexadecimales")
        
        length = len(hex_part)
        if length not in [3, 4, 6, 8]:
            raise ValueError(f"'{value}' no tiene una longitud válida (debe ser 3, 4, 6 u 8 caracteres)")
        
        self._value = value.upper()
        self._parse_value()

    def _parse_value(self) -> None:
        """Parsea el valor hexadecimal y extrae los componentes RGB(A)."""
        hex_part = self._value[1:]
        length = len(hex_part)
        
        if length == 3:  # #RGB
            self._r = int(hex_part[0] * 2, 16)
            self._g = int(hex_part[1] * 2, 16)
            self._b = int(hex_part[2] * 2, 16)
            self._a = 1.0
        elif length == 4:  # #RGBA
            self._r = int(hex_part[0] * 2, 16)
            self._g = int(hex_part[1] * 2, 16)
            self._b = int(hex_part[2] * 2, 16)
            self._a = int(hex_part[3] * 2, 16) / 255.0
        elif length == 6:  # #RRGGBB
            self._r = int(hex_part[0:2], 16)
            self._g = int(hex_part[2:4], 16)
            self._b = int(hex_part[4:6], 16)
            self._a = 1.0
        else:  # length == 8: #RRGGBBAA
            self._r = int(hex_part[0:2], 16)
            self._g = int(hex_part[2:4], 16)
            self._b = int(hex_part[4:6], 16)
            self._a = int(hex_part[6:8], 16) / 255.0

    # ==============================
    # Propiedades para acceder a componentes
    # ==============================

    @property
    def r(self) -> int:
        """Componente rojo (0-255)."""
        return self._r

    @property
    def g(self) -> int:
        """Componente verde (0-255)."""
        return self._g

    @property
    def b(self) -> int:
        """Componente azul (0-255)."""
        return self._b

    @property
    def a(self) -> float:
        """Componente alpha (0.0-1.0)."""
        return self._a

    @property
    def value(self) -> str:
        """Devuelve el valor hexadecimal normalizado."""
        return self._value

    # ==============================
    # Creación de instancias
    # ==============================

    def copy(self) -> 'HEX':
        """Devuelve una copia del color."""
        return HEX(self._value)

    @classmethod
    def from_hsl(cls, value: HSL) -> 'HEX':
        """Crea un HEX desde un valor HSL."""
        rgb = value.to_rgb()
        return cls.from_rgb(rgb)

    @classmethod
    def from_rgb(cls, value: RGB) -> 'HEX':
        """Crea un HEX desde un valor RGB."""
        if value.a < 1.0:
            hex_str = f"#{value.r:02X}{value.g:02X}{value.b:02X}{int(round(value.a * 255)):02X}"
        else:
            hex_str = f"#{value.r:02X}{value.g:02X}{value.b:02X}"
        return cls(hex_str)

    @classmethod
    def from_tuple(cls, value: tuple) -> 'HEX':
        """Crea un HEX desde una tupla (r, g, b) o (r, g, b, a)."""
        rgb = RGB.from_tuple(value)
        return cls.from_rgb(rgb)

    # ==============================
    # Conversión
    # ==============================

    def to_css(self) -> str:
        """Devuelve una representación CSS del color."""
        return self._value.lower()

    def to_hex(self) -> str:
        """Devuelve el valor hexadecimal."""
        return self._value

    def to_hsl(self) -> HSL:
        """Convierte el color actual a formato HSL."""
        return self.to_rgb().to_hsl()

    def to_rgb(self) -> RGB:
        """Convierte el color actual a formato RGB."""
        return RGB(self._r, self._g, self._b, self._a)

    def to_ansi_index(self) -> int:
        """Convierte el color actual al índice ANSI más cercano (0-255)."""
        return self.to_rgb().to_ansi_index()

    # ==============================
    # Métodos de formato
    # ==============================

    def to_short_hex(self) -> str:
        """
        Convierte a formato corto (#RGB) si es posible.
        Retorna el formato largo si no se puede acortar.
        """
        if self._a < 1.0:
            # Con alpha
            alpha_hex = int(round(self._a * 255))
            if (self._r % 17 == 0 and self._g % 17 == 0 and 
                self._b % 17 == 0 and alpha_hex % 17 == 0):
                r = hex(self._r // 17)[2:]
                g = hex(self._g // 17)[2:]
                b = hex(self._b // 17)[2:]
                a = hex(alpha_hex // 17)[2:]
                return f"#{r}{g}{b}{a}".upper()
        else:
            # Sin alpha
            if self._r % 17 == 0 and self._g % 17 == 0 and self._b % 17 == 0:
                r = hex(self._r // 17)[2:]
                g = hex(self._g // 17)[2:]
                b = hex(self._b // 17)[2:]
                return f"#{r}{g}{b}".upper()
        
        return self._value

    def to_long_hex(self) -> str:
        """Convierte siempre a formato largo (#RRGGBB o #RRGGBBAA)."""
        if self._a < 1.0:
            return f"#{self._r:02X}{self._g:02X}{self._b:02X}{int(round(self._a * 255)):02X}"
        return f"#{self._r:02X}{self._g:02X}{self._b:02X}"

    # ==============================
    # Operadores de comparación
    # ==============================

    def __eq__(self, other) -> bool:
        """Compara dos colores HEX."""
        if not isinstance(other, HEX):
            return False
        return (self._r == other._r and self._g == other._g and 
                self._b == other._b and abs(self._a - other._a) < 0.001)

    def __hash__(self) -> int:
        """Permite usar HEX como clave de diccionario."""
        return hash((self._r, self._g, self._b, round(self._a, 3)))

    def __str__(self) -> str:
        """Representación en string."""
        return self._value.lower()


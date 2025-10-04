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
        self.h = h
        self.s = s
        self.l = l
        self.a = a

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


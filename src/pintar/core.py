# TODO: que el operador suma '+' funcione para poder concatenarse con otro str o otro dye
# TODO: que en vez de string acepte cualquier parametro que se pueda cambiar a str como un entero

from .colors import RGB, Color
from typing import Tuple, List, Any, Union

class dye:
    """Dar color a una cadena de texto con códigos ANSI."""
    def __init__(self, string: Union[str, 'dye'] , fore: str | Color = None, bg: Color = None, style: int | Color = None):

        if isinstance(string, dye):
            self.string = string.string_format

        self.string = str(string)
        self.fore = self._process_color_parameter(fore)
        self.bg = self._process_color_parameter(bg)
        self.style = style 

        self.string_format = self.get_string_format()

    def __format__(self, format_spec):
        return format(self.string_format, format_spec)

    def __repr__(self):
        return f"{self.string_format!r}"

    def __str__(self):
        return self.string_format

    def __len__(self):
        return len(self.clean)

    def __getitem__(self, index):
        # Asegurarse de que el texto formateado esté preprocesado
        if not hasattr(self, 'clean_indexes'):
            self._preprocessing_text()

        # Convertir el índice en un slice si es necesario
        if not isinstance(index, slice):
            index = slice(index, index + 1, 1)

        # Manejar valores por defecto del slice
        start = index.start if index.start is not None else 0
        stop = index.stop if index.stop is not None else len(self.clean_indexes)
        step = index.step if index.step is not None else 1

        # Generar los índices limpios seleccionados por el slice
        clean_selected_indexes = list(range(len(self.clean_indexes)))[start:stop:step]
        clean_selected_set = set(clean_selected_indexes)

        # Reconstruir el texto incluyendo ANSI y caracteres limpios seleccionados
        result = []
        for i, (is_ansi, clean_idx) in enumerate(self.char_info):
            if is_ansi:
                result.append(self.original_string_format[i])
            else:
                if clean_idx in clean_selected_set:
                    result.append(self.original_string_format[i])
        final_result = ''.join(result)
        return dye(final_result, self.fore_ansi_sec, self.bg_ansi_sec, self.style_ansi_sec)

    def __iter__(self):
        return iter(self.clean)

    @classmethod
    def start(cls, fore=None, bg=None, style=None, repr=False):
        # Configurar a formatos validos
        font_ansi = cls._color_to_ansi_rgb_seccion(fore)
        bg_ansi = cls._color_to_ansi_rgb_seccion(bg)
        style_ansi = cls._style_to_ansi_seccion(style)

        # Preparar la seuencia ANSI par cada formato de estilo 
        ansi_text_format = "\033[39m"
        ansi_bg_format = "\033[49m"
        format_in_style = "\033[22m"

        # Construir la secuencia de escape ANSI
        if font_ansi is not None:
            ansi_text_format = f"\033[38;{"5" if font_ansi.isalnum() else "2"};{font_ansi}m" 
        if bg_ansi is not None:
            ansi_bg_format = f"\033[48;{"5" if bg_ansi.isalnum() else "2"};{bg_ansi}m"
        if style_ansi is not None:
            format_in_style = f"\033[{style_ansi}m"

        ansi = ""

        ansi += ansi_text_format
        ansi += ansi_bg_format
        ansi += format_in_style 

        if repr: return ansi
        else: print(ansi, end="")

    @classmethod
    def end(cls, repr=False):
        ansi = "\033[0m"
        if repr: 
            return ansi
        else: 
            print(ansi, end="") #  = "\033[39m" "\033[49m" "\033[22m"

    @classmethod
    def palette(cls):
        """Muestra los colores basicos de la paleta de 256 colores"""
        columns = 10
        rows = int(256/columns)
        # Crear la matriz y secuencias
        matriz = [[row + col * rows + 1 for col in range(columns)] for row in range(rows)]
        for l in matriz:
            for i in range(columns):
                print(f"{l[i]:>3}-\033[48;5;{l[i]}m Font \033[0m \033[38;5;{l[i]}mText\033[0m    ", end="")
            print()
        return ""

    @staticmethod
    def _color_to_ansi_rgb_seccion(color: RGB):
        """ convierte un color en formato rgb o hex a codigo ansi"""
        if color is None: return

        return ';'.join(map(str, color.rgb_tuple))

    @staticmethod
    def _style_to_ansi_seccion(style: str | int | List[int]) -> Tuple[int]:
        " solo acepta 'bold+italic' o 1 o '1' o (1,3)"
        
        if style is None: return

        assert isinstance(style, (int, str, list)), "Parametro style invalido. Parametros validos: (int, str, list)"

        # Diccionario de estilos a números ANSI
        style_codes = {
            "bold": 1,
            "italic": 3,
            "underline": 4,
            "strikethrough": 9,  # Tachado
            }

        if isinstance(style, str):
            styles_ansi_indexes = [style_codes[str_style] for str_style in style.split('+')]
        elif isinstance(style, int):
            assert style in style_codes.values()
            styles_ansi_indexes = [style]
        else:
            assert all([True if sty in style_codes.values() else False for sty in style])
            styles_ansi_indexes = style

        return ';'.join( map(str, styles_ansi_indexes)) 


    def update_colors(self, fore=None, bg=None, style=None):
        self.fore = self._process_color_parameter(fore) or self.fore
        self.bg = self._process_color_parameter(bg) or self.bg
        self.style = self._process_color_parameter(style) or self.style

        self.string_format = self.get_string_format()

    def get_string_format(self):
        
        self.fore_ansi_sec = self._color_to_ansi_rgb_seccion(self.fore)
        self.bg_ansi_sec = self._color_to_ansi_rgb_seccion(self.bg)
        self.style_ansi_sec = self._style_to_ansi_seccion(self.style)

        # Preparar la seuencia ANSI par cada formato de estilo 
        ansi_text_format = ""
        ansi_bg_format = ""
        ansi_style_format = ""

        # Construir la secuencia de escape ANSI
        if self.fore_ansi_sec is not None:
            ansi_text_format += f"\033[38;{"5" if self.fore_ansi_sec.isalnum() else "2"};{self.fore_ansi_sec}m" 
        if self.bg_ansi_sec is not None:
            ansi_bg_format += f"\033[48;{"5" if self.bg_ansi_sec.isalnum() else "2"};{self.bg_ansi_sec}m"
        if self.style_ansi_sec is not None:
            ansi_style_format += f"\033[{self.style_ansi_sec}m"

        # CREAR UN NUEVO SISTEMA CON CAPACIDAD DE DETECTAR SI ES rawin de fondo de texto o estilo y usar replace para cambiarlos con "[6m, [7m, [8m"
        # Código para resetear los estilos y colores
        # Usar códigos únicos como placeholders
        raw_in_text     =  "\033[39m"  # Reset foreground color    | si falla: probar con 50m (que no hace nada)
        raw_in_bg       =  "\033[49m"  # Reset background (neutro) | si falla: probar con 51m (que no hace nada)
        raw_in_style    =  "\033[22m"  # Reset bold/dim (neutro)   | si falla: probar con 52m (que no hace nada)
        raw_sequence  = raw_in_text + raw_in_bg + raw_in_style

        all_out    = "\033[0m"

        # Agregar los delimitadores de 'raw_in' y 'all_out'
        string_format = raw_sequence + self.string + all_out

        # Reeplazar los delimitadores de 'raw_in'  por los códigos ANSI
        if ansi_text_format != "":
            string_format = string_format.replace(raw_in_text, ansi_text_format)
        if ansi_bg_format != "":
            string_format = string_format.replace(raw_in_bg, ansi_bg_format) 
        if ansi_style_format != "":
            string_format = string_format.replace(raw_in_style, ansi_style_format) 
        
        # Proteger el texto formateado con los delimitadores de 'base_out' y 'base_in' 
        self.string_format = all_out + string_format + raw_sequence

        return self.string_format

    def _preprocessing_text(self):
        self.original_string_format = self.string_format
        # Lista de tuplas: (es_ansi, índice_limpio)
        self.char_info = []
        # Lista de índices originales para caracteres limpios
        self.clean_indexes = []

        i = 0
        while i < len(self.original_string_format):

            if self.original_string_format.startswith('\x1b[', i):
                # Encontrar el final de la secuencia ANSI (termina en 'm')
                j = self.original_string_format.find('m', i) + 1
                if j == 0:
                    j = len(self.original_string_format)
                # Marcar todos los caracteres en este rango como ANSI
                for k in range(i, j):
                    self.char_info.append((True, None))
                i = j
            else:
                # Marcar como carácter limpio y guardar su índice
                self.char_info.append((False, len(self.clean_indexes)))
                self.clean_indexes.append(i)
                i += 1

    def _process_color_parameter(self, color: Any) -> Color:
        if isinstance(color, RGB):
            return color
        if isinstance(color, tuple):
            return RGB(color)
        if isinstance(color, str):
            if color[0] == '#':
                return RGB.from_hex_string(color)
        if isinstance(color, int):
            return RGB.from_ansi_index(color) 


    @property
    def clean(self):
        """Devuelve la cadena de texto sin códigos de formato ANSI"""
        # Asegurarse de que el texto formateado esté preprocesado
        if not hasattr(self, 'clean_indexes'):
            self._preprocessing_text()

        # Reconstruir el texto limpio usando los índices de self.clean_indexes
        return ''.join([self.string_format[i] for i in self.clean_indexes])
    
class Brush:
    @classmethod
    def load(cls, fore=None, bg=None, style=None):
        ansi_color: str = dye.start(fore, bg, style, repr=True)
        ansi_end: str = dye.end(repr=True)
        return lambda string: ansi_color + string + ansi_end

class Stencil:
    def __init__(self, string) -> None:
        self.string = string

    def spray(self, fore=None, bg=None, style=None):
        return dye(self.string, fore, bg, style)


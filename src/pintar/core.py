import re
# TODO: cambiar 'return_repr' por 'repr' en dye.start
# TODO: que el operador suma '+' funcione para poder concatenarse con otro str o otro dye
# TODO: cambiar 'tex' por 'txt' 
# TODO: que en vez de string acepte cualquier parametro que se pueda cambiar a str como un entero

class dye:
    """Dar color a una cadena de texto con códigos ANSI."""
    def __init__(self, string, text_color=None, bg_color=None, style=None):
        self.string = string.string_format if isinstance(string, dye) else str(string)
        self.final_string = None # Se asigna al final

        # Configurar a formatos validos
        self.font_ansi = self._convert_color_to_ansi(text_color)
        self.bg_ansi = self._convert_color_to_ansi(bg_color)
        self.style_ansi = self._conver_style_to_ansi(style)

        # Preparar la seuencia ANSI par cada formato de estilo 
        ansi_text_format = ""
        ansi_bg_format = ""
        format_in_style = ""

        # Construir la secuencia de escape ANSI
        if self.font_ansi is not None:
            ansi_text_format += f"\033[38;{"5" if self.font_ansi.isalnum() else "2"};{self.font_ansi}m" 
        if self.bg_ansi is not None:
            ansi_bg_format += f"\033[48;{"5" if self.bg_ansi.isalnum() else "2"};{self.bg_ansi}m"
        if self.style_ansi is not None:
            format_in_style += f"\033[{self.style_ansi}m"

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
        if format_in_style != "":
            string_format = string_format.replace(raw_in_style, format_in_style) 
        
        # Proteger el texto formateado con los delimitadores de 'base_out' y 'base_in' 
        self.string_format = all_out + string_format + raw_sequence

        # # preoprocesar el texto
        # self._preprocessing_text()

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

    @staticmethod
    def _convert_color_to_ansi(color):
        if color is None:
            return None
        
        # Asegurarse de que el color sea una cadena
        color = str(color).strip()
        
        # Si es hexadecimal aseugurar la cantidad de 6 caracteres 
        color = color[:7] if len(color) > 7 and "#" in color else color

        # Expresiones regulares para validar formatos
        rgb_pattern = re.compile(r"^rgb\(\s*(\d{1,3}%?)\s*,\s*(\d{1,3}%?)\s*,\s*(\d{1,3}%?)\s*\)$")
        hex_pattern = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")

        # Verificar si es un color RGB
        if rgb_pattern.match(color):
            # Extraer los valores de r, g, b
            r, g, b = re.findall(r"\d+", color)
            r, g, b = int(r), int(g), int(b)
            return f"{r};{g};{b}"

        # Verificar si es un color HEX
        if hex_pattern.match(color):
            hex_value = color.lstrip("#")
            # Si es de 3 caracteres, expandirlo a 6
            if len(hex_value) == 3:
                hex_value = "".join([c * 2 for c in hex_value])
            # Convertir a RGB
            r = int(hex_value[0:2], 16)
            g = int(hex_value[2:4], 16)
            b = int(hex_value[4:6], 16)
            return f"{r};{g};{b}"

        # Verificar si es un color de 8 bits (0-255)
        try:
            color_int = int(color)
            if 0 <= color_int <= 256:
                return str(color_int)  # Dejarlo tal cual
        except ValueError:
            pass  # No es un número válido

        # Si no coincide con ningún formato, lanzar una excepción
        raise ValueError(f"No se reconoce el formato de color '{color}'.")
   
    @staticmethod
    def _conver_style_to_ansi(style):
        if style is None:
            return None

        # Diccionario de estilos a números ANSI
        estilos_ansi = {
            "bold": 1,
            "italic": 3,
            "underline": 4,
            "strikethrough": 9,  # Tachado
        }

        # Si el estilo ya es un número o una cadena numérica, devolverlo tal cual
        if isinstance(style, int):
            return str(style)
        if isinstance(style, str) and style.replace(";", "").isdigit():
            return style
        if isinstance(style, list) and all(isinstance(x, int) for x in style):
            return ";".join(map(str, style))

        # Si es una cadena, procesarla
        if isinstance(style, str):
            # Separar por "+" si hay múltiples estilos
            partes = style.split("+")
            numeros = []
            for parte in partes:
                parte = parte.strip().lower()
                if parte in estilos_ansi:
                    numeros.append(str(estilos_ansi[parte]))
                else:
                    raise ValueError(f"Estilo no reconocido: '{parte}'")
            return ";".join(numeros)

        # Si no es un tipo válido, lanzar una excepción
        raise ValueError(f"Formato de estilo no válido: '{style}'")

    @classmethod
    def start(cls, tex=None, bg=None, sty=None, return_repr=False):
        # Configurar a formatos validos
        font_ansi = cls._convert_color_to_ansi(tex)
        bg_ansi = cls._convert_color_to_ansi(bg)
        style_ansi = cls._conver_style_to_ansi(sty)

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

        if return_repr: return ansi
        else: print(ansi, end="")

    @classmethod
    def end(cls, return_repr=False):
        ansi = "\033[0m"
        if return_repr: 
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

    @property
    def clean(self):
        """Devuelve la cadena de texto sin códigos de formato ANSI"""
        # Asegurarse de que el texto formateado esté preprocesado
        if not hasattr(self, 'clean_indexes'):
            self._preprocessing_text()

        # Reconstruir el texto limpio usando los índices de self.clean_indexes
        return ''.join([self.string_format[i] for i in self.clean_indexes])
               
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
        return dye(final_result, self.font_ansi, self.bg_ansi, self.style_ansi)

    def __iter__(self):
        return iter(self.clean)


class Brush:
    @classmethod
    def load(cls, text_color=None, bg_color=None, style=None):
        ansi_color: str = dye.start(text_color, bg_color, style, return_repr=True)
        ansi_end: str = dye.end(return_repr=True)
        return lambda string: ansi_color + string + ansi_end


class Stencil:
    def __init__(self, string) -> None:
        self.string = string

    def spray(self, tex_color=None, bg_color=None, style=None):
        return dye(self.string, tex_color, bg_color, style)




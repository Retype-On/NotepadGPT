import os
import re

def invert_svg_colors(input_svg_path, output_svg_path):
    """
    Invierte los colores en un archivo .svg y guarda el resultado en un nuevo archivo.
    """
    def invert_color(color):
        if color.startswith("#") and (len(color) == 7 or len(color) == 4):
            if len(color) == 4:
                # Convertir colores de formato #abc a #aabbcc
                color = "#" + "".join(c * 2 for c in color[1:])
            # Invertir los colores
            inverted = "#" + "".join(f"{255 - int(color[i:i+2], 16):02x}" for i in (1, 3, 5))
            return inverted
        return color

    try:
        # Leer el contenido del archivo SVG
        with open(input_svg_path, "r", encoding="utf-8") as file:
            svg_content = file.read()

        # Buscar colores en formato hexadecimal (#rrggbb o #rgb) y reemplazarlos
        hex_color_pattern = re.compile(r"#([a-fA-F0-9]{3,6})")
        inverted_content = hex_color_pattern.sub(
            lambda match: invert_color(match.group(0)), svg_content
        )

        # Guardar el contenido modificado en el archivo de salida
        with open(output_svg_path, "w", encoding="utf-8") as file:
            file.write(inverted_content)

        print(f"Archivo procesado: {output_svg_path}")
    except Exception as e:
        print(f"Error al procesar {input_svg_path}: {e}")


def process_svg_folder(input_folder, output_folder):
    """
    Procesa todos los archivos .svg en una carpeta, invierte sus colores y guarda los resultados
    en otra carpeta.
    """
    # Verificar si la carpeta de entrada existe
    if not os.path.exists(input_folder):
        print(f"La carpeta de entrada '{input_folder}' no existe.")
        return

    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterar por los archivos en la carpeta de entrada
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".svg"):
            input_svg_path = os.path.join(input_folder, file_name)
            output_svg_path = os.path.join(output_folder, file_name)
            invert_svg_colors(input_svg_path, output_svg_path)

    print("Procesamiento completado.")


# Rutas de las carpetas de entrada y salida
input_folder = "d:\\Programacion\\Git\\Programs\\NotepadGPT\\icons"  # Cambia esta ruta según tu necesidad
output_folder = "d:\\Programacion\\Git\\Programs\\NotepadGPT\\icons\\svg\\inverted"    # Cambia esta ruta según tu necesidad

# Ejecutar el programa
process_svg_folder(input_folder, output_folder)

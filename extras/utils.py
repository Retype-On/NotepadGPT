from xml.dom import minidom
import os

def invert_svg_colors(input_svg):
    # Leer el archivo SVG
    doc = minidom.parse(os.path.dirname(os.path.abspath(__file__)) +'/' + input_svg)
    paths = doc.getElementsByTagName('path')
    
    for path in paths:
        fill = path.getAttribute('fill')
        if fill:
            # Invertir el color
            inverted_color = invert_color(fill)
            path.setAttribute('fill', inverted_color)
    
    return doc.toxml()

def invert_color(color):
    if color.startswith('#') and len(color) == 7:
        r = 255 - int(color[1:3], 16)
        g = 255 - int(color[3:5], 16)
        b = 255 - int(color[5:7], 16)
        return f'#{r:02X}{g:02X}{b:02X}'
    return color

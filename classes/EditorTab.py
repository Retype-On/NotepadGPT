#import sys
#import subprocess
#import os
#import re
#from PyQt5.QtWidgets import (
#    QApplication, QMainWindow, QPlainTextEdit, QAction, QFileDialog, QMessageBox, QWidget, QTextEdit
#)
#from PyQt5.QtGui import QIcon, QColor, QSyntaxHighlighter, QTextCharFormat, QFont, QTextFormat, QPainter, QPen, QKeyEvent
#from PyQt5.QtCore import Qt, QRegExp, QRect, QSize
import re

from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtGui import QSyntaxHighlighter, QColor, QFont, QTextFormat, QTextCharFormat, QPainter
from PyQt5.QtCore import Qt, QRect, pyqtSignal

from config.Config import config

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        
        self.editor.line_number_area_paint_event(event)


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Paleta de colores para el tema oscuro
        dark_blue = QColor("#81A1C1")  # Palabras clave
        light_purple = QColor("#B48EAD")  # Nombres de funciones
        light_sky_blue = QColor("#88C0D0")  # Métodos y atributos
        dark_orange = QColor("#D08770")  # Operadores
        gray = QColor("#7d7573")  # Comentarios
        light_red = QColor("#BF616A")  # Cadenas
        yellow = QColor("#EBCB8B")  # Variables en f-strings

        # Formato para palabras clave
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(dark_blue)
        self.keyword_format.setFontWeight(QFont.Bold)

        # Formato para nombres de funciones
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(light_purple)
        self.function_format.setFontItalic(True)

        # Formato para nombres de métodos y atributos de objetos
        self.object_method_format = QTextCharFormat()
        self.object_method_format.setForeground(light_sky_blue)

        # Formato para operadores y condicionales
        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(dark_orange)

        # Formato para comentarios
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(gray)

        # Formato para cadenas
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(light_red)

        # Formato para variables dentro de cadenas formateadas
        self.fstring_variable_format = QTextCharFormat()
        self.fstring_variable_format.setForeground(yellow)

        # Palabras clave
        self.keywords = [
            "def", "class", "import", "from", "return", "if", "else", "elif",
            "for", "while", "try", "except", "finally", "with", "as", "yield", "lambda", "pass",
        ]

        # Operadores y condicionales
        self.operators = [
            r"=", r"==", r"\(", r"\)", r"\.", r"\:", r"<", r">", r"<=", r">=", r"\+", r"-", r"\*", r"/", r"%", r",", r"\[", r"\]", r"\{", r"\}",
        ]

    def highlightBlock(self, text):
        # Resaltado de palabras clave
        for keyword in self.keywords:
            for match in re.finditer(rf"\b{keyword}\b", text):
                start, end = match.span()
                self.setFormat(start, end - start, self.keyword_format)

        # Resaltado de nombres de funciones (palabras seguidas de `(`)
        for match in re.finditer(r"\b\w+(?=\()", text):
            start, end = match.span()
            self.setFormat(start, end - start, self.function_format)

        # Resaltado de métodos y atributos de objetos (solo lo que sigue a un punto '.')
        for match in re.finditer(r"\.\w+", text):
            start, end = match.span()
            self.setFormat(start + 1, end - start - 1, self.object_method_format)  # Excluir el '.' del resaltado

        # Resaltado de operadores y condicionales
        for operator in self.operators:
            for match in re.finditer(operator, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.operator_format)

        # Resaltado de cadenas (incluyendo cadenas formateadas con f-string)
        for match in re.finditer(r'f"[^"]*"|f\'[^\']*\'|"[^\"]*"|\'[^\']*\'', text):
            start, end = match.span()
            self.setFormat(start, end - start, self.string_format)

            # Si es una f-string, resaltar variables dentro de llaves
            if text[start] == "f":
                for var_match in re.finditer(r"\{[^{}]*\}", text[start:end]):
                    var_start, var_end = var_match.span()
                    var_start += 1  # Ajustar a la posición relativa
                    var_end -= 1  # Excluir las llaves
                    self.setFormat(var_start + start-1, var_end - var_start+2, self.fstring_variable_format)

        # Resaltado de comentarios
        for match in re.finditer(r"#.*", text):
            start, end = match.span()
            self.setFormat(start, end - start, self.comment_format)
                


class EditorTab(QPlainTextEdit):
    content_changed = pyqtSignal()
    def __init__(self, file_path=""):
        super().__init__()
        self.file_path = file_path
        
        self.highlighter = PythonHighlighter(self.document())  # Asocia el resaltador de sintaxis
        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        self.update_settings()
        self.line_number_area.update()  # Redibuja el área de números de línea
        
        font = QFont("Arial", 12)
        self.line_number_area.setFont(font)
        self.update_line_number_area_width(0)
        self.viewport().update()  # Actualiza la vista
        self.line_number_area.update()  # Redibuja el área de números
        
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        self.original_content = "" # Guarda el contenido original del archivo
        self.textChanged.connect(self.notify_content_change)
        
    def keyPressEvent(self, event):
        cursor = self.textCursor()
        
        if event.key() == Qt.Key_Backtab:
            cursor.movePosition(cursor.StartOfBlock)  # Nos movemos al inicio de la línea
            current_text = cursor.block().text()
            
            # Si la línea tiene al menos 4 espacios al inicio, los eliminamos
            if current_text.startswith("    "):  
                new_text = current_text[4:]
                cursor.insertText(new_text)  # Insertamos el nuevo texto sin los 4 espacios
            event.accept()  # Aceptamos el evento para no hacer otro comportamiento

        elif event.key() == Qt.Key_Tab:
            indentation = "    "  # 4 espacios por nivel de indentación
            cursor.insertText(indentation)  # Insertamos los espacios
            event.accept()  # Aceptamos el evento para no insertar la tabulación original

        elif event.key() == Qt.Key_Return:
            # Obtenemos la línea actual hasta la posición del cursor
            current_line = cursor.block().text()  
            cursor_position_in_block = cursor.positionInBlock()
            indent = self.getIndentationForLine(current_line, cursor)  # Obtenemos la indentación hasta el cursor
            #if current_line.strip().endswith(":"):
            #    indent += "    "  # Aumentamos un nivel de tabulación
            if current_line[:cursor_position_in_block].strip().endswith(":") or current_line[:cursor_position_in_block].strip().endswith("{"):
                indent += "    "
            cursor.insertText("\n" + indent)  # Insertamos una nueva línea con la misma indentación
            event.accept()  # Aceptamos el evento

        else:
            super().keyPressEvent(event)  # Dejamos que el evento se maneje normalmente

    def getIndentationForLine(self, line, cursor):
        """
        Esta función devuelve la cantidad de espacios al inicio de la línea hasta la posición del cursor.
        """
        # Obtener la posición del cursor dentro de la línea
        cursor_position = cursor.columnNumber()
        
        # Solo obtener la porción de la línea que está antes del cursor
        line_before_cursor = line[:cursor_position]
        
        # Contamos cuántos espacios tiene al principio la parte de la línea antes del cursor
        spaces_count = len(line_before_cursor) - len(line_before_cursor.lstrip(' '))
        
        # Devolvemos la cantidad adecuada de indentación con 4 espacios
        return " " * (spaces_count)  

    def set_font(self, font_size):
        """Establece la fuente para todo el EditorTab."""
        if font_size < 100 and font_size > 0:
            self.font_size = font_size  # Actualiza el tamaño de fuente guardado
            font = self.font()
            font.setPointSize(font_size)
            self.document().setDefaultFont(font)
            
            if font_size < 20 and font_size > 6:
                font2 = QFont("Arial", font_size)
                self.line_number_area.setFont(font2)
                self.update_line_number_area_width(0)
                self.viewport().update()  # Actualiza la vista
                self.line_number_area.update()  # Redibuja el área de números
        
            print(font_size)

    def update_line_number_area_width(self, _):
        """Actualiza el ancho del área de números de línea."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def line_number_area_width(self):
        """Calcula el ancho del área de los números de línea."""
        digits = len(str(max(1, self.blockCount())))  # Número de dígitos en el número de línea más grande
        font_metrics = self.fontMetrics()  # Métricas de la fuente actual
        space = 6 + font_metrics.horizontalAdvance('9') * digits + (self.font_size if self.font_size <=20 else 20) # Añade un margen adicional
        return space


    def update_line_number_area(self, rect, dy):
        """Actualiza el área de los números de línea cuando hay un cambio."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Ajusta el área de números de línea cuando se redimensiona la ventana."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
        self.viewport().update()
        #print(f"Viewport: {self.viewport().geometry()}")
        #print(f"Line Number Area: {self.line_number_area.geometry()}")



    def line_number_area_paint_event(self, event):
        """Dibuja los números de línea alineados hacia la parte superior y sin cortarse."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#3B4252"))  # Fondo del margen de números de línea

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        font_metrics = self.fontMetrics()  # Métricas de la fuente actual

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#D8DEE9"))  # Color de los números de línea

                block_height = self.blockBoundingRect(block).height()
                # Aseguramos que el número se dibuje completamente
                y_position = int(top + (block_height - font_metrics.height()) // 3)

                # Dibujar el número de línea con un margen adicional en la parte inferior para evitar el corte
                # Aquí se utiliza font_metrics.ascent() y font_metrics.descent() para ajustar el espacio vertical
                line_height = font_metrics.height() + font_metrics.descent()

                painter.drawText(0, y_position, self.line_number_area.width(), line_height,
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        """Resalta la línea actual."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#434C5E").lighter(120)  # Fondo de la línea actual
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def set_file_path(self, path):
        """Asigna una nueva ruta de archivo."""
        self.file_path = path

    def get_file_path(self):
        """Devuelve la ruta del archivo asociada."""
        return self.file_path

    def wheelEvent(self, event):
        """Maneja el zoom con Ctrl + rueda del ratón."""
        if event.modifiers() == Qt.ControlModifier:  # Verifica si Ctrl está presionado
            delta = event.angleDelta().y()
            new_font_size = self.font_size
            if delta > 0:  # Si la rueda se mueve hacia arriba, aumentar tamaño de fuente
                new_font_size += 2
            elif delta < 0:  # Si la rueda se mueve hacia abajo, reducir tamaño de fuente
                new_font_size -= 2
            self.set_font(int(new_font_size))  # Aplica el nuevo tamaño de fuente
        else:
            super().wheelEvent(event)  # Delega el evento de desplazamiento normal
    
    def update_settings(self):
        if config.wrap_mode_active:
            self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.NoWrap)
        #self.setTabStopDistance(80)
        
        self.font_size = config.font_size  # Tamaño de fuente inicial
        self.set_font(config.font_size)  # Configura la fuente inicial
        
    def load_content(self, content):
        """Carga el contenido inicial del archivo y lo guarda como estado original."""
        self.original_content = content
        self.setPlainText(content)

    def is_modified(self):
        """Devuelve True si el contenido actual difiere del original."""
        return self.toPlainText() != self.original_content

    def notify_content_change(self):
        """Emite la señal cuando hay cambios en el contenido."""
        self.content_changed.emit()
        
    def mark_as_saved(self):
        """Marca el contenido actual como guardado."""
        self.original_content = self.toPlainText()

    def reinitialize(self):
        """Reinicia las configuraciones esenciales después de mover el EditorTab."""
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.viewport().update()  # Actualiza el área de texto
        self.line_number_area.update()  # Actualiza el área de números de línea

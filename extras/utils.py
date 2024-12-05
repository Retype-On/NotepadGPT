from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QAction, QSizePolicy
)
from PyQt5.QtGui import QTextCursor, QTextDocument, QIcon
from PyQt5.QtCore import Qt

from classes.EditorTab import EditorTab

class FindReplaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar y Reemplazar")
        self.resize(600, 400)
        self.parent_editor = None  # Editor asociado
        self.parent = parent
        self.all_tabs_editors = []  # Lista de editores abiertos (para búsqueda en todos los tabs)
        self.search_direction_down = True  # Dirección inicial: hacia abajo

        # Widgets principales
        self.search_label = QLabel("Buscar:")
        self.search_input = QLineEdit()

        self.replace_label = QLabel("Reemplazar:")
        self.replace_input = QLineEdit()

        self.match_case_checkbox = QCheckBox("Distinguir mayúsculas y minúsculas")
        self.whole_word_checkbox = QCheckBox("Coincidencia de palabra completa")
        self.limit_to_selection_checkbox = QCheckBox("Limitar a selección")
        self.search_all_tabs_checkbox = QCheckBox("Buscar en todos los tabs")

        # Botones principales
        self.find_button = QPushButton("Buscar")
        #self.find_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.direction_button = QPushButton("⬇")  # Dirección inicial: abajo
        self.direction_button.setFixedWidth(40)  # Tamaño cuadrado para el botón
        self.replace_button = QPushButton("Reemplazar")
        self.replace_all_button = QPushButton("Reemplazar Todo")
        self.count_button = QPushButton("Contar Coincidencias")
        self.close_button = QPushButton("Cerrar")

        # Layout principal
        main_layout = QGridLayout()
        button_layout = QVBoxLayout()

        # Columna izquierda (entrada y opciones)
        main_layout.addWidget(self.search_label, 0, 0)
        main_layout.addWidget(self.search_input, 0, 1, 1, 3)
        main_layout.addWidget(self.replace_label, 1, 0)
        main_layout.addWidget(self.replace_input, 1, 1, 1, 3)

        main_layout.addWidget(self.match_case_checkbox, 2, 0, 1, 4)
        main_layout.addWidget(self.whole_word_checkbox, 3, 0, 1, 4)
        main_layout.addWidget(self.limit_to_selection_checkbox, 4, 0, 1, 4)
        main_layout.addWidget(self.search_all_tabs_checkbox, 5, 0, 1, 4)

        # Layout horizontal para el botón de buscar y el de dirección
        self.find_layout = QHBoxLayout()
        self.find_layout.addWidget(self.find_button)
        self.find_layout.addWidget(self.direction_button)
        #main_layout.addLayout(find_layout, 6, 1, 1, 3)

        # Columna derecha (botones adicionales)
        button_layout.addLayout(self.find_layout)
        button_layout.addWidget(self.replace_button)
        button_layout.addWidget(self.replace_all_button)
        button_layout.addWidget(self.count_button)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout, 0, 4, 7, 1)

        self.setLayout(main_layout)

        # Conexión de botones
        self.find_button.clicked.connect(self.find_text)
        self.direction_button.clicked.connect(self.toggle_direction)
        self.replace_button.clicked.connect(self.replace_text)
        self.replace_all_button.clicked.connect(self.replace_all_text)
        self.count_button.clicked.connect(self.count_matches)
        self.close_button.clicked.connect(self.close)

    def set_editor(self, editor):
        """Asocia un editor al cuadro de diálogo."""
        self.parent_editor = editor

    def set_all_tabs_editors(self):
        """Asocia todos los editores abiertos para búsqueda en todos los tabs."""
        editors = []
        current_widget = self.parent.tabs.currentWidget() 
        current_index = self.parent.tabs.indexOf(current_widget)
        for i in range(current_index, self.parent.tabs.count()):
            editors.append(self.parent.tabs.widget(i))
        self.all_tabs_editors = editors
        
    def get_search_flags(self):
        """Obtiene las banderas de búsqueda según las opciones seleccionadas."""
        flags = QTextDocument.FindFlags()
        if self.match_case_checkbox.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_checkbox.isChecked():
            flags |= QTextDocument.FindWholeWords
        if not self.search_direction_down:
            flags |= QTextDocument.FindBackward
        return flags

    def toggle_direction(self):
        """Alterna la dirección de búsqueda entre arriba y abajo."""
        self.search_direction_down = not self.search_direction_down
        self.direction_button.setText("⬇" if self.search_direction_down else "⬆")

    def find_text(self):
        """Busca el texto ingresado con las opciones seleccionadas."""
        search_text = self.search_input.text()
        if not search_text:
            QMessageBox.warning(self, "Error", "Por favor, ingresa un texto para buscar.")
            return

        flags = self.get_search_flags()
        self.set_all_tabs_editors()
        editors = self.all_tabs_editors if self.search_all_tabs_checkbox.isChecked() else [self.parent.tabs.currentWidget()]

        for i in range(len(editors)):
            editor = editors[i]
            #print(f"Estamos en position{i}/n")
            cursor = editor.textCursor()

            if self.limit_to_selection_checkbox.isChecked() and cursor.hasSelection():
                # Limitar la búsqueda al texto seleccionado
                start, end = cursor.selectionStart(), cursor.selectionEnd()
                cursor.setPosition(cursor.position())  # Mantener la posición actual para progresar
                editor.setTextCursor(cursor)

                if editor.find(search_text, flags):
                    current_position = editor.textCursor().position()
                    if start <= current_position <= end:
                        return  # Coincidencia encontrada dentro de la selección
                continue  # Saltar al siguiente editor si no hay coincidencia dentro de la selección
            else:
                # Búsqueda general sin límite de selección
                if editor.find(search_text, flags):
                    #print(f"Se encontro una coincidencia en la poss {i}")
                    self.parent.tabs.setCurrentWidget(editor)
                    return  # Coincidencia encontrada en el editor actual
                elif isinstance(editors[i+1], EditorTab) if i + 1 < len(editors) else None:
                    #print(f"nada encontrado, saltando al siguiente{i+1}",sep='/n')
                    next_cursor = editors[i+1].textCursor()
                    next_cursor.setPosition(0) 
                    editors[i].setTextCursor(next_cursor)

        # Si se recorrieron todos los editores sin encontrar coincidencia
        QMessageBox.information(self, "Buscar", "No se encontró el texto.")


    def replace_text(self):
        """Reemplaza el texto seleccionado con el texto de reemplazo."""
        cursor = self.parent_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_input.text())
            self.find_text()  # Buscar el siguiente

    def replace_all_text(self):
        """Reemplaza todas las ocurrencias del texto de búsqueda."""
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        if not search_text:
            QMessageBox.warning(self, "Error", "Por favor, ingresa un texto para buscar.")
            return

        flags = self.get_search_flags()
        self.set_all_tabs_editors()
        editors = self.all_tabs_editors if self.search_all_tabs_checkbox.isChecked() else [self.parent_editor]
        total_count = 0

        for editor in editors:
            cursor = editor.textCursor()
            if self.limit_to_selection_checkbox.isChecked() and cursor.hasSelection():
                start, end = cursor.selectionStart(), cursor.selectionEnd()
                cursor.setPosition(start)
                editor.setTextCursor(cursor)
                while cursor.position() <= end and editor.find(search_text, flags):
                    editor.textCursor().insertText(replace_text)
                    total_count += 1
            else:
                cursor.movePosition(QTextCursor.Start)
                editor.setTextCursor(cursor)
                while editor.find(search_text, flags):
                    editor.textCursor().insertText(replace_text)
                    total_count += 1

        QMessageBox.information(self, "Reemplazar Todo", f"Se reemplazaron {total_count} ocurrencias.")

    def count_matches(self):
        """Cuenta cuántas veces aparece el texto buscado."""
        search_text = self.search_input.text()
        if not search_text:
            QMessageBox.warning(self, "Error", "Por favor, ingresa un texto para buscar.")
            return

        flags = self.get_search_flags()
        self.set_all_tabs_editors()
        editors = self.all_tabs_editors if self.search_all_tabs_checkbox.isChecked() else [self.parent_editor]
        total_count = 0

        for editor in editors:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)
            while editor.find(search_text, flags):
                total_count += 1

        QMessageBox.information(self, "Contar Coincidencias", f"Se encontraron {total_count} coincidencias.")




def RAction(self, icon_name: str, description: str, shortcut: str,function):
    new_action = QAction(QIcon('NotepadGPT/icons/' + icon_name) if icon_name else QIcon.setIcon(), description, self)
    new_action.setShortcut(shortcut)
    new_action.triggered.connect(function)
    return new_action
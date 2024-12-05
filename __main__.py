import os
import sys
import subprocess
import tempfile

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QAction, QFileDialog, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from classes.EditorTab import EditorTab

from config.Config import config
from extras.utils import FindReplaceDialog, RAction

class DetachedTabWindow(QMainWindow):
    tab_reattached = pyqtSignal(EditorTab)  # Señal para devolver la pestaña al editor principal

    def __init__(self, editor_tab, title, parent=None):
        super().__init__(parent)
        self.editor = EditorTab()
        self.editor_tab = editor_tab  # Mantener referencia del EditorTab
        self.setWindowTitle(editor_tab.file_path if editor_tab.file_path else "Untiled")
        self.setCentralWidget(self.editor)
        self.resize(800, 600)
        
        #Establecer los valores necesarios:
        self.editor.setPlainText(editor_tab.toPlainText())
        self.editor.set_file_path(editor_tab.get_file_path())
        self.editor.original_content = editor_tab.original_content

        # Barra de herramientas con botón para regresar el tab
        toolbar = self.addToolBar('Detached Toolbar')
        toolbar.setMovable(False)
        
        self.initUI()
        self.show()

    def initUI(self):
        #icons_color_palletes: aea353ff, este: bd954dff
        #self.setWindowTitle('Notepad GPT')
        #ruta_proyecto = os.path.dirname(os.path.abspath(__file__))
        # Crear acciones del menú
        reattach_action = RAction(self,'reattach.svg', 'Volver a la ventana principal', 'Alt+F4', self.reattach_tab)
        save_current_file = RAction(self, 'save.svg', 'Save file', 'Ctrl+S', self.save_current_file)
        save_current_file_as = RAction(self, 'save.svg', 'Save file as...', 'Ctrl+Alt+S', self.save_current_file_as)
        undo_action = RAction(self, 'undo_2.svg', 'Undo last action', 'Ctrl+Z', self.undo)
        redo_action = RAction(self, 'redo_2.svg', 'Redo last action', 'Ctrl+Y', self.redo)
        cut_action = RAction(self, 'cut.svg', 'Cut selected text or selected line', 'Ctrl+X', self.cut)
        copy_action = RAction(self, 'copy.svg', 'Copy selected text or selected line', 'Ctrl+C', self.copy)
        paste_action = RAction(self, 'paste.svg', 'Paste of clipboard', 'Ctrl+V', self.paste)
        run_code = RAction(self, 'run.svg', 'Run in console', 'Ctrl+R', self.run_code)
        
        # Crear barra de menús
        #file_menu.addSeparator()
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(reattach_action)
        file_menu.addSeparator()
        file_menu.addAction(save_current_file)
        file_menu.addAction(save_current_file_as)
        
        file_menu = menubar.addMenu('&Edit')
        file_menu.addAction(undo_action)
        file_menu.addAction(redo_action)
        file_menu.addSeparator()
        file_menu.addAction(cut_action)
        file_menu.addAction(copy_action)
        file_menu.addAction(paste_action)
        file_menu = menubar.addMenu('&Run')
        file_menu.addAction(run_code)
        
        # Crear barra de herramientas con solo iconos debajo de la barra de menús
        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(reattach_action)
        toolbar.addSeparator()
        toolbar.addAction(save_current_file)
        toolbar.addAction(save_current_file_as)
        toolbar.addSeparator()
        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)
        toolbar.addSeparator()
        toolbar.addAction(cut_action)
        toolbar.addAction(copy_action)
        toolbar.addAction(paste_action)
        toolbar.addSeparator()
        toolbar.addAction(run_code)
        
        # Ajustar la apariencia de la barra de herramientas (iconos solamente, sin texto)
        toolbar.setIconSize(QSize(32, 32))  # Ajustar el tamaño de los iconos
        toolbar.setFloatable(False)  # Evitar que la barra de herramientas se pueda liberar
        toolbar.setMovable(True)  # Evitar que la barra de herramientas se pueda mover

    def reattach_tab(self):
        """Devuelve la pestaña a la ventana principal."""
        self.editor_tab.setPlainText(self.editor.toPlainText())
        self.editor_tab.set_file_path(self.editor.get_file_path())
        self.editor_tab.original_content = self.editor.original_content
        self.tab_reattached.emit(self.editor_tab)  # Emitir señal para devolver el tab
        self.close()
    
    def closeEvent(self, event):
        self.reattach_tab()
        event.accept()
    
    def save_current_file(self):
        if isinstance(self.editor, EditorTab) and self.editor.file_path:
            with open(self.editor.get_file_path(), 'w') as f:
                f.write(self.editor.toPlainText())
            self.editor.mark_as_saved()
            #self.update_this_tab_icon(editor)              Aqui se arreglaria el simbolo de guardado...
        else:
            self.save_current_file_as()
    
    def save_current_file_as(self):
        """Guarda el archivo enviado con una nueva ruta."""
        if isinstance(self.editor, EditorTab):
            fname, _ = QFileDialog.getSaveFileName(self, 'Save file', '', "Python Files (*.py);;All Files (*)")
            if fname:
                self.editor.set_file_path(fname)
                with open(fname, 'w') as f:
                    f.write(self.editor.toPlainText())
                self.setWindowTitle(fname)
                self.editor.mark_as_saved()
                #self.update_this_tab_icon(self.editor)      Aqui se arreglaria el simbolo de guardado...

    def run_code(self):
        """Ejecuta el código del archivo actual."""        
        # Comprobar si el editor es una instancia de EditorTab
        if isinstance(self.editor, EditorTab):
            file_path = self.editor.get_file_path()
            # Si no hay ruta, crear un archivo temporal
            if not file_path:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding=config.encoding_files) as temp_file:
                    temp_file.write(self.editor.toPlainText())
                    file_path = temp_file.name

            # Comando para ejecutar el archivo en una nueva consola
            if config.keep_console_open:
                command = ['start', 'cmd', '/k', 'python', file_path]  # Mantener la consola abierta
            else:
                command = ['start', 'cmd', '/c', 'python', file_path]  # Cerrar la consola al finalizar
            
            # Ejecutar el comando
            subprocess.Popen(command, shell=True)
        else:
            print("El widget actual no es una instancia de EditorTab")

    def undo(self):
        """Deshace la última acción."""
        if self.editor:
            self.editor.undo()

    def redo(self):
        """Rehace la última acción deshecha."""
        if self.editor:
            self.editor.redo()

    def cut(self):
        """Corta el texto seleccionado."""
        if self.editor:
            self.editor.cut()

    def copy(self):
        """Copia el texto seleccionado."""
        if self.editor:
            self.editor.copy()

    def paste(self):
        """Pega el contenido del portapapeles."""
        if self.editor:
            self.editor.paste()

class MWCodeEditor(QMainWindow):
    #   Editor principal
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)  # Habilitar reordenamiento de pestañas
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_title)
        self.setCentralWidget(self.tabs)
        
        self.tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self.context_menu_requested)
        
        self.find_dialog = FindReplaceDialog(self)
        
        self.unsaved_icon = QIcon('NotepadGPT/icons/handwriter.svg')

        self.initUI()
        
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.load_stylesheet("NotepadGPT/styles/mainW.css")
        
        self.mode_actions = {
            1: self.showFullScreen, 
            2: self.showMaximized, 
            3: self.showMinimized, 
            4: self.showNormal
        }
        self.change_view_mode(config.view_mode_value)

    def change_view_mode(self, index):
        action = self.mode_actions.get(index)
        if action:
            action()
        

    def tab_detached(self, index):
        """Desancla un tab y lo mueve a una nueva ventana."""
        widget = self.tabs.widget(index)
        if not widget:
            return

        # Extrae el widget de la pestaña y crea una nueva ventana
        title = self.tabs.tabText(index)
        self.tabs.removeTab(index)

        detached_window = DetachedTabWindow(widget, title, self)
        widget.reinitialize()
        detached_window.tab_reattached.connect(self.reattach_tab)  # Conectar señal
        detached_window.show()

    def reattach_tab(self, editor_tab):
        """Devuelve un tab desanclado a la ventana principal."""
        try:
            title = editor_tab.file_path.split('/')[-1] or "New File"
        except:
            title = "New File"
            
        index = self.tabs.addTab(editor_tab, title)
        self.tabs.setCurrentWidget(editor_tab)
        
        self.update_tab_icon()
        
        # Reconectar la señal para actualizar íconos
        editor_tab.content_changed.connect(self.update_tab_icon)


    def context_menu_requested(self, pos):
        """Muestra un menú contextual en las pestañas."""
        index = self.tabs.tabBar().tabAt(pos)
        if index == -1:
            return

        menu = QMenu(self)
        detach_action = QAction("Mover a ventana independiente", self)
        detach_action.triggered.connect(lambda: self.tab_detached(index))
        menu.addAction(detach_action)
        menu.exec_(self.tabs.mapToGlobal(pos))


    def load_stylesheet(self, path):
        """Carga un archivo CSS y aplica el estilo a la ventana."""
        try:
            with open(path, "r", encoding=config.encoding_files) as file:
                css = file.read()
                self.setStyleSheet(css)
        except FileNotFoundError:
            print(f"Error: El archivo {path} no se encontró.")
        except Exception as e:
            print(f"Error al cargar el archivo CSS: {e}")

        # Aplicar el estilo a cada pestaña existente y para pestañas futuras
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if isinstance(editor, EditorTab):
                editor.setStyleSheet(tab_style)

    def initUI(self):
        
        #icons_color_palletes: aea353ff, este: bd954dff
        self.setWindowTitle('Notepad GPT')
        #ruta_proyecto = os.path.dirname(os.path.abspath(__file__))
        # Crear acciones del menú
        new_tab = RAction(self, 'new_file.svg', 'New Tab', 'Ctrl+T', self.new_tab)
        open_file = RAction(self, 'open.svg', 'Open', 'Ctrl+O', self.open_file)
        save_current_file = RAction(self, 'save.svg', 'Save file', 'Ctrl+S', self.save_current_file)
        save_current_file_as=RAction(self, 'save.svg', 'Save file as...', 'Ctrl+Alt+S', self.save_current_file_as)
        save_all_files = RAction(self, 'save.svg', 'Save all files', 'Ctrl+Shift+S', self.save_all_files)
        run_code = RAction(self, 'run.svg', 'Run in console', 'Ctrl+R', self.run_code)
        undo_action = RAction(self, 'undo_2.svg', 'Undo last action', 'Ctrl+Z', self.undo)
        redo_action = RAction(self, 'redo_2.svg', 'Redo last action', 'Ctrl+Y', self.redo)
        cut_action = RAction(self, 'cut.svg', 'Cut selected text or selected line', 'Ctrl+X', self.cut)
        copy_action = RAction(self, 'copy.svg', 'Copy selected text or selected line', 'Ctrl+C', self.copy)
        paste_action = RAction(self, 'paste.svg', 'Paste of clipboard', 'Ctrl+V', self.paste)
        find_dialog = RAction(self, 'document-magnifying-glass.svg', 'Search or Replace', 'Ctrl+F', self.open_find_dialog)
        
        # Crear barra de menús
        #file_menu.addSeparator()
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(new_tab)
        file_menu.addAction(open_file)
        file_menu.addSeparator()
        file_menu.addAction(save_current_file)
        file_menu.addAction(save_current_file_as)
        file_menu.addAction(save_all_files)
        
        file_menu = menubar.addMenu('&Edit')
        file_menu.addAction(undo_action)
        file_menu.addAction(redo_action)
        file_menu.addSeparator()
        file_menu.addAction(cut_action)
        file_menu.addAction(copy_action)
        file_menu.addAction(paste_action)
        
        file_menu = menubar.addMenu('&Run')
        file_menu.addAction(find_dialog)
        file_menu.addAction(run_code)
        
        
        # Crear barra de herramientas con solo iconos debajo de la barra de menús
        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(new_tab)
        toolbar.addAction(open_file)
        toolbar.addAction(save_current_file)
        toolbar.addAction(save_current_file_as)
        toolbar.addAction(save_all_files)
        toolbar.addSeparator()
        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)
        toolbar.addSeparator()
        toolbar.addAction(cut_action)
        toolbar.addAction(copy_action)
        toolbar.addAction(paste_action)
        toolbar.addSeparator()
        toolbar.addAction(find_dialog)
        toolbar.addAction(run_code)
        
        # Ajustar la apariencia de la barra de herramientas (iconos solamente, sin texto)
        toolbar.setIconSize(QSize(32, 32))  # Ajustar el tamaño de los iconos
        toolbar.setFloatable(False)  # Evitar que la barra de herramientas se pueda liberar
        toolbar.setMovable(True)  # Evitar que la barra de herramientas se pueda mover

        self.setGeometry(300, 300, config.window_size[0], config.window_size[1])
        self.show()

    def new_tab(self, file_name="New File"):
        """Crea una nueva pestaña sin archivo asociado."""
        editor = EditorTab()
        file_name = file_name if isinstance(file_name, str) else "New File"
        #editor.setStyleSheet(self.actual_theme)
        tab_index = self.tabs.addTab(editor, file_name)
        self.tabs.setCurrentWidget(editor)
        
        editor.content_changed.connect(self.update_tab_icon)

    def close_tab(self, index):
        """Cierra una pestaña específica."""
        editor = self.tabs.widget(index)
        if isinstance(editor, EditorTab):
            editor.content_changed.disconnect(self.update_tab_icon)
        self.tabs.removeTab(index)


    def open_file(self):
        """Abre un archivo y crea una nueva pestaña para él."""
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '', "Python Files (*.py);;All Files (*)")
        if fname:
            with open(fname, 'r') as f:
                data = f.read()
            editor = EditorTab(file_path=fname)
            editor.setPlainText(data)
            #editor.setStyleSheet(self.actual_theme)
            tab_index = self.tabs.addTab(editor, fname.split('/')[-1])
            self.tabs.setCurrentWidget(editor)
            
            editor.mark_as_saved()
            editor.content_changed.connect(self.update_tab_icon)
            editor.highlighter.rehighlight()
    
    def save_all_files(self):
        """Guarda el archivo actual."""
        for i in range(self.tabs.count()):
            editor = self.parent.tabs.widget(i)
            self.save_file(editor, i)
    
    def save_current_file(self):
        """Guarda el archivo actual."""
        editor = self.tabs.currentWidget()
        index = self.tabs.currentIndex()
        self.save_file(editor, index)
    
    def save_file(self, editor, index):
        if isinstance(editor, EditorTab) and editor.file_path:
            with open(editor.get_file_path(), 'w') as f:
                f.write(editor.toPlainText())
            editor.mark_as_saved()
            self.update_this_tab_icon(editor)
        else:
            self.save_file_as(editor, index)

    def save_current_file_as(self):
        """Guarda el archivo actual con una nueva ruta."""
        editor = self.tabs.currentWidget()
        index = self.tabs.currentIndex()
        self.save_file_as(editor, index)
    
    def save_file_as(self, editor, index):
        """Guarda el archivo enviado con una nueva ruta."""
        if isinstance(editor, EditorTab):
            fname, _ = QFileDialog.getSaveFileName(self, 'Save file', '', "Python Files (*.py);;All Files (*)")
            if fname:
                editor.set_file_path(fname)
                with open(fname, 'w') as f:
                    f.write(editor.toPlainText())
                self.tabs.setTabText(index, fname.split('/')[-1])
                editor.mark_as_saved()
                self.update_this_tab_icon(editor)

    def run_code(self):
        """Ejecuta el código del archivo actual."""
        editor = self.tabs.currentWidget()
        
        # Comprobar si el editor es una instancia de EditorTab
        if isinstance(editor, EditorTab):
            file_path = editor.get_file_path()
            
            # Si no hay ruta, crear un archivo temporal
            if not file_path:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding=config.encoding_files) as temp_file:
                    temp_file.write(editor.toPlainText())
                    file_path = temp_file.name

            # Comando para ejecutar el archivo en una nueva consola
            if config.keep_console_open:
                command = ['start', 'cmd', '/k', 'python', file_path]  # Mantener la consola abierta
            else:
                command = ['start', 'cmd', '/c', 'python', file_path]  # Cerrar la consola al finalizar
            
            # Ejecutar el comando
            subprocess.Popen(command, shell=True)
        else:
            print("El widget actual no es una instancia de EditorTab")

    def get_current_editor(self):
        """Obtiene el editor actual activo en la pestaña."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, EditorTab):
            return current_widget
        return None

    def undo(self):
        """Deshace la última acción."""
        editor = self.get_current_editor()
        if editor:
            editor.undo()

    def redo(self):
        """Rehace la última acción deshecha."""
        editor = self.get_current_editor()
        if editor:
            editor.redo()

    def cut(self):
        """Corta el texto seleccionado."""
        editor = self.get_current_editor()
        if editor:
            editor.cut()

    def copy(self):
        """Copia el texto seleccionado."""
        editor = self.get_current_editor()
        if editor:
            editor.copy()

    def paste(self):
        """Pega el contenido del portapapeles."""
        editor = self.get_current_editor()
        if editor:
            editor.paste()

    def update_title(self, index):
        """Actualiza el título de la ventana según la pestaña activa."""
        if index != -1:
            editor = self.tabs.widget(index)
            if isinstance(editor, EditorTab):
                self.setWindowTitle(editor.get_file_path() or "Untitled")

    def update_tab_icon(self):
        """Actualiza el ícono de la pestaña cuando hay cambios en el contenido."""
        current_editor = self.tabs.currentWidget()
        if isinstance(current_editor, EditorTab):
            tab_index = self.tabs.indexOf(current_editor)
            file_name = current_editor.get_file_path() or "New File"
            
            if current_editor.is_modified():
                # Agrega el ícono de "sin guardar" a la pestaña
                self.tabs.setTabIcon(tab_index, self.unsaved_icon)
            else:
                # Elimina el ícono de "sin guardar"
                self.tabs.setTabIcon(tab_index, QIcon())  # Sin ícono    
                
    def update_this_tab_icon(self, editor):
        """Actualiza el ícono de la pestaña cuando hay cambios en el contenido."""
        #current_editor = self.tabs.currentWidget()
        if isinstance(editor, EditorTab):
            tab_index = self.tabs.indexOf(editor)
            file_name = editor.get_file_path() or "New File"
            
            if editor.is_modified():
                # Agrega el ícono de "sin guardar" a la pestaña
                self.tabs.setTabIcon(tab_index, self.unsaved_icon)
            else:
                # Elimina el ícono de "sin guardar"
                self.tabs.setTabIcon(tab_index, QIcon())  # Sin ícono

    def on_tab_changed(self, index):
        editor = self.tabs.widget(index)
        if isinstance(editor, EditorTab):
            editor.update_font()

    def open_find_dialog(self):
        """Abre el cuadro de diálogo de buscar y reemplazar."""
        editor = self.get_current_editor()
        if editor:
            self.find_dialog.set_editor(editor)
            self.find_dialog.show()
        else:
            QMessageBox.warning(self, "Error", "No hay ningún editor activo.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MWCodeEditor()
    ex.new_tab("Welcome!")
    sys.exit(app.exec_())

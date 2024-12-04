import os
import sys
import subprocess

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QAction, QFileDialog, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from classes.EditorTab import EditorTab

from config.Config import config

class DetachedTabWindow(QMainWindow):
    tab_reattached = pyqtSignal(EditorTab)  # Señal para devolver la pestaña al editor principal

    def __init__(self, editor_tab, title, parent=None):
        super().__init__(parent)
        self.editor = EditorTab()
        self.editor_tab = editor_tab  # Mantener referencia del EditorTab
        self.setWindowTitle(title)
        self.setCentralWidget(self.editor)
        self.resize(800, 600)
        
        #Establecer los valores necesarios:
        self.editor.setPlainText(editor_tab.toPlainText())
        
        # Aplicar el estilo actual del editor principal, si está definido
        if hasattr(parent, 'editor_style'):
            editor_tab.setStyleSheet(parent.editor_style)

        # Barra de herramientas con botón para regresar el tab
        toolbar = self.addToolBar('Detached Toolbar')
        toolbar.setMovable(False)
        reattach_action = QAction(QIcon('NotepadGPT/icons/reattach.svg'), 'Volver a la ventana principal', self)
        reattach_action.triggered.connect(self.reattach_tab)
        toolbar.addAction(reattach_action)
        
        self.show()

    def reattach_tab(self):
        """Devuelve la pestaña a la ventana principal."""
        self.editor_tab.setPlainText(self.editor.toPlainText())
        #self.editor_tab.#
        self.tab_reattached.emit(self.editor_tab)  # Emitir señal para devolver el tab
        self.close()
    
    def closeEvent(self, event):
        self.reattach_tab()
        event.accept()

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
        
        self.unsaved_icon = QIcon('NotepadGPT/icons/handwriter.svg')

        self.initUI()
            
        self.load_stylesheet("NotepadGPT/styles/mainW.css")

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
            with open(path, "r", encoding="utf-8") as file:
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
        self.setWindowTitle('Code Editor')
        ruta_proyecto = os.path.dirname(os.path.abspath(__file__))
        # Crear acciones del menú
        open_file = QAction(QIcon('NotepadGPT/icons/open.svg'), 'Open', self)
        open_file.setShortcut('Ctrl+O')
        open_file.triggered.connect(self.open_file)

        save_current_file = QAction(QIcon('NotepadGPT/icons/save.svg'), 'Save', self)
        save_current_file.setShortcut('Ctrl+S')
        save_current_file.triggered.connect(self.save_current_file)
        
        save_all_files = QAction(QIcon('NotepadGPT/icons/save.svg'), 'Save all', self)
        save_all_files.setShortcut('Ctrl+Shift+S')
        save_all_files.triggered.connect(self.save_all_files)
        
        run_code = QAction(QIcon('NotepadGPT/icons/run.svg'), 'Run', self)
        run_code.setShortcut('Ctrl+R')
        run_code.triggered.connect(self.run_code)

        new_tab = QAction(QIcon('NotepadGPT/icons/new_file.svg'), 'New Tab', self)
        new_tab.setShortcut('Ctrl+T')
        new_tab.triggered.connect(self.new_tab)
        
        

        # Crear barra de menús
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(open_file)
        file_menu.addAction(save_current_file)
        file_menu.addAction(save_all_files)
        file_menu.addAction(run_code)
        file_menu.addAction(new_tab)
        
        
        # Crear barra de herramientas con solo iconos debajo de la barra de menús
        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(new_tab)  # Agregar icono de nueva pestaña
        toolbar.addAction(open_file)  # Agregar icono de abrir archivo
        toolbar.addAction(save_current_file)  # Agregar icono de guardar archivo
        toolbar.addAction(save_all_files)  # Agregar icono de guardar archivo
        toolbar.addSeparator()
        toolbar.addAction(run_code)  # Agregar icono de ejecutar código
        
        # Ajustar la apariencia de la barra de herramientas (iconos solamente, sin texto)
        toolbar.setIconSize(QSize(32, 32))  # Ajustar el tamaño de los iconos
        toolbar.setFloatable(False)  # Evitar que la barra de herramientas se pueda mover
        toolbar.setMovable(False)  # Evitar que la barra de herramientas se pueda mover

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
            editor = self.tabs.widget(i)
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
        if isinstance(editor, EditorTab) and editor.get_file_path():
            subprocess.Popen(['start', 'cmd', '/k', 'python', editor.get_file_path()], shell=True)

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MWCodeEditor()
    ex.new_tab()
    sys.exit(app.exec_())

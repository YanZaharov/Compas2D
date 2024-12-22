from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from .canvas import Canvas
from .toolbar import ToolBar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Настройка основного окна
        self.setWindowTitle("Компас 2D")
        self.setGeometry(100, 100, 1200, 800)

        # Создание главного виджета и макета
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Создание холста для рисования
        self.canvas = Canvas()
        self.layout.addWidget(self.canvas)

        # Создание панели инструментов
        self.toolbar = ToolBar(self)
        self.addToolBar(self.toolbar)

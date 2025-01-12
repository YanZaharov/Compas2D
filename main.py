import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QInputDialog, QStatusBar, QDockWidget, QMessageBox
from PyQt5.QtCore import Qt
from ui.canvas import Canvas
from ui.objects_tree import ConstructionTree
from PyQt5.QtWidgets import QColorDialog

# Константы для строковых значений
COORD_SYSTEMS = {'cartesian': 'Декартова', 'polar': 'Полярная'}
LINE_TYPES = {'solid': 'Сплошная линия', 'dash': 'Штриховая линия', 'dash_dot': 'Штрих-пунктирная', 'dash_dot_dot': 'Штрих-пунктирная с двумя точками'}
DRAWING_MODES = {
    'line': 'Линия',
    'circle_center_radius': 'По центру и радиусу',
    'circle_three_points': 'По трём точкам',
    'arc_three_points': 'По трём точкам',
    'arc_radius_chord': 'По радиусу и хорде',
    'polygon': 'По точкам',
    'polygon_inscribed': 'Вписанный',
    'polygon_circumscribed': 'Описанный',
    'rectangle_sides': 'По сторонам',
    'rectangle_center': 'От центра',
    'spline_bezier': 'Безье',
    'spline_segments': 'По отрезкам'
}

GROUPED_DRAWING_MODES = {
    "Дуга": ['arc_three_points', 'arc_radius_chord'],
    "Окружность": ['circle_center_radius', 'circle_three_points'],
    "Прямоугольник": ['rectangle_sides', 'rectangle_center'],
    "Многоугольник": ['polygon', 'polygon_inscribed', 'polygon_circumscribed'],
    "Сплайн": ['spline_bezier', 'spline_segments']
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compas 2D")
        self.setGeometry(100, 100, 1600, 1000)
        self.is_dark_theme = False  # По умолчанию светлая тема
        self.initUI()

    def initUI(self):
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.createMenus()
        self.createStatusBar()
        self.createConstructionTree()
        self.applyTheme()

    def setGridSize(self):
        size, ok = QInputDialog.getInt(
            self, 
            "Размер сетки",
            "Введите размер ячейки сетки:",
            value=self.canvas.grid_size,
            min=10,
            max=200
        )
        if ok:
            self.canvas.grid_size = size
            self.canvas.update()
            self.statusBar.showMessage(f"Размер сетки установлен: {size}")

    def applyTheme(self):
        if self.is_dark_theme:
            # Получаем handle окна
            hwnd = self.winId().__int__()
            
            # Устанавливаем темный цвет для заголовка
            DWMWA_CAPTION_COLOR = 35
            from ctypes import windll, c_int, byref, sizeof
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_CAPTION_COLOR,
                byref(c_int(0x1e1e1e)), # Темно-серый цвет
                sizeof(c_int)
            )
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-bottom: 1px solid #3d3d3d;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                }
                QMenu::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border-top: 1px solid #3d3d3d;
                }
                QDockWidget {
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                }
                QDockWidget::title {
                    background-color: #2d2d2d;
                    padding: 8px;
                }
                QLabel{
                    color: #ffffff;
                }
                QTreeWidget {
                    background-color: #2d2d2d;
                    border: 1px solid #3d3d3d;
                }
                QTreeWidget::item:selected {
                    background-color: #3d3d3d;
                }
                QInputDialog, QMessageBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #4d4d4d;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
                QPushButton:pressed {
                    background-color: #5d5d5d;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #4d4d4d;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
        else:
            # Получаем handle окна
            hwnd = self.winId().__int__()
            
            # Возвращаем стандартный цвет заголовка
            DWMWA_CAPTION_COLOR = 35
            from ctypes import windll, c_int, byref, sizeof
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_CAPTION_COLOR,
                byref(c_int(-1)), # Сброс к системному цвету
                sizeof(c_int)
            )
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QMenuBar {
                    background-color: #ffffff;
                    border-bottom: 1px solid #e0e0e0;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                }
                QMenu::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QStatusBar {
                    background-color: #ffffff;
                    color: #424242;
                    border-top: 1px solid #e0e0e0;
                }
                QDockWidget {
                    border: 1px solid #e0e0e0;
                }
                QDockWidget::title {
                    background-color: #f5f5f5;
                    padding: 8px;
                }
                QTreeWidget {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                }
                QTreeWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: #424242;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                    border-color: #1976d2;
                    color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #e3f2fd;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)


    def createMenus(self):
        mainMenu = self.menuBar()

        # Добавляем кнопку переключения темы
        themeAction = QAction('Сменить тему', self)
        themeAction.setStatusTip("Переключить между светлой и темной темой")
        themeAction.triggered.connect(self.toggleTheme)
        mainMenu.addAction(themeAction)

        # Добавляем меню для работы с сеткой
        gridMenu = mainMenu.addMenu('Сетка')

        # Кнопка показать/скрыть сетку
        gridAction = QAction('Показать/скрыть сетку', self)
        gridAction.setStatusTip("Переключить отображение сетки")
        gridAction.triggered.connect(self.toggleGrid)
        gridMenu.addAction(gridAction)

        # Кнопка изменения размера сетки
        gridSizeAction = QAction('Размер сетки', self)
        gridSizeAction.setStatusTip("Изменить размер ячейки сетки")
        gridSizeAction.triggered.connect(self.setGridSize)
        gridMenu.addAction(gridSizeAction)
        
        # Остальные меню
        self.createDrawingObjectsMenu(mainMenu)
        self.createLineSettingsMenu(mainMenu)
        self.createShapeSettingsMenu(mainMenu)
        self.createCoordinateSystemMenu(mainMenu)
    
    def toggleGrid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.update()
        grid_state = "включена" if self.canvas.show_grid else "выключена"
        self.statusBar.showMessage(f"Сетка {grid_state}")

    def toggleTheme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.applyTheme()
        theme_name = "темную" if self.is_dark_theme else "светлую"
        self.statusBar.showMessage(f"Тема переключена на {theme_name}")

    def createDrawingObjectsMenu(self, menu):
        drawingObjectsMenu = menu.addMenu('Объекты')

        # Добавление отдельных режимов
        for mode, label in DRAWING_MODES.items():
            if not any(mode in group for group in GROUPED_DRAWING_MODES.values()):
                action = QAction(label, self)
                action.setStatusTip(f"Режим рисования: {label}")
                action.triggered.connect(lambda checked, m=mode: self.setDrawingMode(m))
                drawingObjectsMenu.addAction(action)

        # Добавление режимов по группам в нужном порядке
        group_order = ['Линия', 'Сплайн', 'Прямоугольник', 'Многоугольник', 'Окружность', 'Дуга']
        
        for group_name in group_order:
            if group_name in GROUPED_DRAWING_MODES:
                modes = GROUPED_DRAWING_MODES[group_name]
                groupMenu = drawingObjectsMenu.addMenu(group_name)
                for mode in modes:
                    action = QAction(DRAWING_MODES[mode], self)
                    action.setStatusTip(f"Режим рисования: {DRAWING_MODES[mode]}")
                    action.triggered.connect(lambda checked, m=mode: self.setDrawingMode(m))
                    groupMenu.addAction(action)

    def createLineSettingsMenu(self, menu):
        lineSettingsMenu = menu.addMenu('Тип линии')
        for line_type, label in LINE_TYPES.items():
            action = QAction(label, self)
            action.setStatusTip(f"Установить {label.lower()}")
            action.triggered.connect(lambda checked, lt=line_type: self.setLineType(lt))
            lineSettingsMenu.addAction(action)

    def createShapeSettingsMenu(self, menu):
        shapeSettingsMenu = menu.addMenu('Настройки объектов')
        
        # Кнопка выбора цвета
        colorAction = QAction('Выбрать цвет', self)
        colorAction.setStatusTip("Выбрать цвет для новых построений")
        colorAction.triggered.connect(self.chooseColor)
        shapeSettingsMenu.addAction(colorAction)
        
        # Кнопка изменения толщины линии
        lineThicknessAction = QAction('Толщина линии', self)
        lineThicknessAction.setStatusTip("Изменить толщину линии")
        lineThicknessAction.triggered.connect(self.setLineThickness)
        shapeSettingsMenu.addAction(lineThicknessAction)
    
    def chooseColor(self):
        color = QColorDialog.getColor(Qt.black, self, "Выберите цвет")
        if color.isValid():
            self.canvas.currentColor = color
            self.statusBar.showMessage(f"Цвет линии изменен на {color.name()}")

    def createCoordinateSystemMenu(self, menu):
        coordinateSystemMenu = menu.addMenu('Система координат')

        # Создаем действие для "Полярная"
        polarAction = QAction('Полярная', self)
        polarAction.setStatusTip("Переключиться на Полярную систему координат")
        polarAction.triggered.connect(lambda: self.setCoordinateSystem('polar'))
        coordinateSystemMenu.addAction(polarAction)
        
        # Создаем действие для "Декартова"
        cartesianAction = QAction('Декартова', self)
        cartesianAction.setStatusTip("Переключиться на Декартову систему координат")
        cartesianAction.triggered.connect(lambda: self.setCoordinateSystem('cartesian'))
        coordinateSystemMenu.addAction(cartesianAction)

    def createConstructionTree(self):
        if not self.findChild(QDockWidget, "Дерево построений"):
            self.constructionTree = ConstructionTree(self, self.canvas)
            self.addDockWidget(Qt.RightDockWidgetArea, self.constructionTree)

    def createStatusBar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def handleManualInput(self):
        self.canvas.handle_manual_input()  # Вызываем метод handle_manual_input из Canvas

    def setCoordinateSystem(self, mode):
        self.canvas.inputCoordinateSystem = mode  # Используем атрибут из canvas.py для изменения системы координат
        self.statusBar.showMessage(f"Система координат переключена на {COORD_SYSTEMS[mode].lower()}")

        # Показать окно с информацией о выбранной системе координат
        if mode == 'cartesian':
            QMessageBox.information(self, "Система координат ввода", "Ввод координат будет производиться в Декартовой системе.")
        else:
            QMessageBox.information(self, "Система координат ввода", "Ввод координат будет производиться в Полярной системе.")

    def setDrawingMode(self, mode):
        self.canvas.drawingMode = mode
        self.statusBar.showMessage(f"Режим рисования: {DRAWING_MODES[mode]}")

    def setLineType(self, line_type):
        self.canvas.lineType = line_type
        self.statusBar.showMessage(f"Установлен тип линии: {LINE_TYPES[line_type]}")

    def setLineThickness(self):
        thickness, ok = QInputDialog.getDouble(self, "Толщина линии", "Введите толщину линии:", value=self.canvas.lineThickness, min=0.1, decimals=1)
        if ok:
            self.canvas.lineThickness = thickness
            self.statusBar.showMessage(f"Толщина линии установлена: {thickness}")

    def rotateLeft(self):
        self.canvas.rotate(10)
        self.statusBar.showMessage("Поворот против часовой стрелки")

    def rotateRight(self):
        self.canvas.rotate(-10)
        self.statusBar.showMessage("Поворот по часовой стрелке")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

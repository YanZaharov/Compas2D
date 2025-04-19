import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QInputDialog, QStatusBar,QDockWidget, QMessageBox, QFileDialog, QLabel)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from ui.canvas import Canvas
from ui.objects_tree import ConstructionTree
from PySide6.QtGui import QColor
from dxf_handler import save_to_dxf_advanced, read_from_dxf

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
        self.current_file = None  # Track the current file
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
            minValue=10,
            maxValue=200
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
            try:
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 
                    DWMWA_CAPTION_COLOR,
                    byref(c_int(0x1e1e1e)), # Темно-серый цвет
                    sizeof(c_int)
                )
            except Exception:
                pass  # Игнорируем ошибки для совместимости с разными платформами
                
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #121212;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 1px solid #3d3d3d;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    color: #ffffff;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #2979ff;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #ffffff;
                }
                QMenu::item:selected {
                    background-color: #2979ff;
                    color: #ffffff;
                }
                QStatusBar {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-top: 1px solid #3d3d3d;
                }
                QDockWidget {
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                }
                QDockWidget::title {
                    background-color: #1e1e1e;
                    padding: 8px;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QTreeWidget {
                    background-color: #1e1e1e;
                    border: 1px solid #3d3d3d;
                    color: #ffffff;
                }
                QTreeWidget::item {
                    color: #ffffff;
                }
                QTreeWidget::item:selected {
                    background-color: #2979ff;
                    color: #ffffff;
                }
                QInputDialog, QMessageBox, QDialog {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QInputDialog QLabel, QMessageBox QLabel, QDialog QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2979ff;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #448aff;
                }
                QPushButton:pressed {
                    background-color: #2962ff;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 5px;
                    selection-background-color: #2979ff;
                    selection-color: #ffffff;
                }
                QComboBox::drop-down {
                    border: 0px;
                    background-color: #2979ff;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    width: 14px;
                    height: 14px;
                    color: #ffffff;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    selection-background-color: #2979ff;
                    selection-color: #ffffff;
                }
                QToolTip {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #3d3d3d;
                }
                QTabWidget::pane {
                    border: 1px solid #3d3d3d;
                }
                QTabBar::tab {
                    background-color: #1e1e1e;
                    color: #b0b0b0;
                    padding: 8px 16px;
                    border: 1px solid #3d3d3d;
                    border-bottom: none;
                }
                QTabBar::tab:selected {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QTabBar::tab:!selected {
                    margin-top: 2px;
                }
                QHeaderView::section {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #3d3d3d;
                }
                QScrollBar:vertical {
                    background-color: #1e1e1e;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #3d3d3d;
                    min-height: 20px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #4d4d4d;
                }
                QScrollBar:horizontal {
                    background-color: #1e1e1e;
                    height: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #3d3d3d;
                    min-width: 20px;
                    border-radius: 6px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #4d4d4d;
                }
            """)
        else:
            # Получаем handle окна
            hwnd = self.winId().__int__()
            
            # Возвращаем стандартный цвет заголовка
            DWMWA_CAPTION_COLOR = 35
            from ctypes import windll, c_int, byref, sizeof
            try:
                windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 
                    DWMWA_CAPTION_COLOR,
                    byref(c_int(-1)), # Сброс к системному цвету
                    sizeof(c_int)
                )
            except Exception:
                pass  # Игнорируем ошибки для совместимости с разными платформами
                
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QMenuBar {
                    background-color: #ffffff;
                    border-bottom: 1px solid #e0e0e0;
                    color: #333333;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    border-radius: 4px;
                    color: #333333;
                }
                QMenuBar::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QMenu {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                    color: #333333;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #333333;
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
                    color: #333333;
                }
                QDockWidget::title {
                    background-color: #f5f5f5;
                    padding: 8px;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QTreeWidget {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    color: #333333;
                }
                QTreeWidget::item {
                    color: #333333;
                }
                QTreeWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QDialog, QInputDialog, QMessageBox {
                    background-color: #ffffff;
                    color: #333333;
                }
                QDialog QLabel, QInputDialog QLabel, QMessageBox QLabel {
                    color: #333333;
                }
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 6px 12px;
                    color: #333333;
                    font-weight: normal;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                    border-color: #1976d2;
                    color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #e3f2fd;
                }
                QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 5px;
                    color: #333333;
                }
                QComboBox::drop-down {
                    border: 0px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #333333;
                    selection-background-color: #e3f2fd;
                    selection-color: #1976d2;
                }
            """)

    def createMenus(self):
        mainMenu = self.menuBar()

        # Create File menu
        fileMenu = mainMenu.addMenu('Файл')
        
        # New action
        newAction = QAction('Новый', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Создать новый файл')
        newAction.triggered.connect(self.newFile)
        fileMenu.addAction(newAction)
        
        # Open DXF action
        openDxfAction = QAction('Открыть DXF...', self)
        openDxfAction.setShortcut('Ctrl+O')
        openDxfAction.setStatusTip('Открыть файл DXF')
        openDxfAction.triggered.connect(self.openDxfFile)
        fileMenu.addAction(openDxfAction)
        
        # Save action
        saveAction = QAction('Сохранить', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Сохранить файл')
        saveAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveAction)
        
        # Save As action
        saveAsAction = QAction('Сохранить как...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.setStatusTip('Сохранить файл как...')
        saveAsAction.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveAsAction)
        
        fileMenu.addSeparator()
        
        # Exit action
        exitAction = QAction('Выход', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Выйти из программы')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        # Add theme toggle button
        themeAction = QAction('Сменить тему', self)
        themeAction.setStatusTip("Переключить между светлой и темной темой")
        themeAction.triggered.connect(self.toggleTheme)
        mainMenu.addAction(themeAction)

        # Add grid menu
        gridMenu = mainMenu.addMenu('Сетка')

        # Grid toggle button
        gridAction = QAction('Показать/скрыть сетку', self)
        gridAction.setStatusTip("Переключить отображение сетки")
        gridAction.triggered.connect(self.toggleGrid)
        gridMenu.addAction(gridAction)

        # Grid size button
        gridSizeAction = QAction('Размер сетки', self)
        gridSizeAction.setStatusTip("Изменить размер ячейки сетки")
        gridSizeAction.triggered.connect(self.setGridSize)
        gridMenu.addAction(gridSizeAction)
        
        # Other menus
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

        if hasattr(self, 'constructionTree'):
            self.constructionTree.updateThemeStyles(self.is_dark_theme)

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
        """
        Открывает диалог выбора стандартных CAD-совместимых цветов
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QGridLayout
        from PySide6.QtGui import QColor, QIcon, QPixmap
        from PySide6.QtCore import Qt, QSize
        
        # Стандартные цвета AutoCAD, совместимые с большинством CAD-программ
        standard_colors = {
            "Черный": (0, 0, 0),          # Black (0)
            "Красный": (255, 0, 0),       # Red (1)
            "Желтый": (255, 255, 0),      # Yellow (2)
            "Зеленый": (0, 255, 0),       # Green (3)
            "Голубой": (0, 255, 255),     # Cyan (4)
            "Синий": (0, 0, 255),         # Blue (5)
            "Фиолетовый": (255, 0, 255),  # Magenta (6)
            "Белый": (255, 255, 255),     # White (7)
            "Серый": (128, 128, 128),     # Gray (8)
            "Светло-серый": (192, 192, 192)  # Light Gray (9)
        }
        
        # Создаем диалог выбора цвета
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите CAD-совместимый цвет")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Добавляем заголовок
        info_label = QLabel("Выберите один из стандартных CAD-совместимых цветов:")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Создаем сетку для цветов (3 колонки)
        grid = QGridLayout()
        grid.setSpacing(10)
        
        # Функция для создания цветного квадрата
        def create_color_square(color):
            pixmap = QPixmap(32, 32)
            pixmap.fill(color)
            return QIcon(pixmap)
        
        # Добавляем цветные кнопки в сетку
        row, col = 0, 0
        for color_name, rgb in standard_colors.items():
            color = QColor(*rgb)
            button = QPushButton()
            button.setToolTip(color_name)
            button.setIcon(create_color_square(color))
            button.setIconSize(QSize(32, 32))
            button.setMinimumHeight(50)
            button.clicked.connect(lambda checked, c=color: self.setSelectedColor(c, dialog))
            
            # Добавляем метку с названием цвета под кнопкой
            color_layout = QVBoxLayout()
            color_layout.addWidget(button)
            color_layout.addWidget(QLabel(color_name, alignment=Qt.AlignCenter))
            
            grid.addLayout(color_layout, row, col)
            
            col += 1
            if col > 2:  # 3 колонки
                col = 0
                row += 1
        
        layout.addLayout(grid)
        
        # Кнопки Отмена/OK в нижней части
        buttons_layout = QHBoxLayout()
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def setSelectedColor(self, color, dialog):
        """
        Устанавливает выбранный цвет и закрывает диалог
        """
        if color.isValid():
            self.canvas.currentColor = color
            self.statusBar.showMessage(f"Цвет линии изменен на {color.name()}")
            dialog.accept()

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
        
        # Add file name label to status bar
        self.fileNameLabel = QLabel("Новый файл")
        self.statusBar.addPermanentWidget(self.fileNameLabel)

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
        self.canvas.setDrawingMode(mode)
        self.statusBar.showMessage(f"Режим рисования: {DRAWING_MODES[mode]}")

    def setLineType(self, line_type):
        self.canvas.lineType = line_type
        self.statusBar.showMessage(f"Установлен тип линии: {LINE_TYPES[line_type]}")

    def setLineThickness(self):
        """
        Показывает диалог выбора стандартной толщины линии согласно ISO
        """
        # Стандартные значения толщины линий по ISO в мм
        standard_thicknesses = [
            0.00, 0.05, 0.09,  # Очень тонкие
            0.13, 0.15, 0.18, 0.20, 0.25,  # Тонкие
            0.30, 0.35, 0.40, 0.50,  # Средние
            0.70,  # Толстые
            1.00   # Очень толстые
        ]
        
        # Находим ближайшее стандартное значение к текущей толщине
        current_thickness = self.canvas.lineThickness
        closest_thickness = min(standard_thicknesses, key=lambda x: abs(x - current_thickness))
        current_index = standard_thicknesses.index(closest_thickness)
        
        # Создаем описательные метки для каждой толщины
        thickness_labels = []
        for t in standard_thicknesses:
            if t <= 0.09:
                category = "Очень тонкая"
            elif t <= 0.25:
                category = "Тонкая"
            elif t <= 0.50:
                category = "Средняя"
            elif t <= 0.70:
                category = "Толстая"
            else:
                category = "Очень толстая"
            thickness_labels.append(f"{t:.2f} мм ({category})")
        
        # Показываем диалог выбора толщины
        thickness, ok = QInputDialog.getItem(
            self, 
            "Толщина линии", 
            "Выберите стандартную толщину линии по ISO:", 
            thickness_labels, 
            current_index, 
            False
        )
        
        if ok:
            # Извлекаем значение толщины из выбранной метки
            selected_thickness = float(thickness.split()[0])
            self.canvas.lineThickness = selected_thickness
            self.statusBar.showMessage(f"Толщина линии установлена: {selected_thickness} мм")

    def rotateLeft(self):
        self.canvas.rotate(10)
        self.statusBar.showMessage("Поворот против часовой стрелки")

    def rotateRight(self):
        self.canvas.rotate(-10)
        self.statusBar.showMessage("Поворот по часовой стрелке")

    # New file handling methods
    def newFile(self):
        # Check if there are unsaved changes
        if self.canvas.shapes and self.confirmSaveChanges():
            # Save current file if user wants to
            self.saveFile()
            
        # Clear canvas
        self.canvas.shapes.clear()
        self.canvas.update()
        self.constructionTree.updateConstructionTree()
        
        # Reset current file
        self.current_file = None
        self.fileNameLabel.setText("Новый файл")
        self.statusBar.showMessage("Создан новый файл")
    
    def openDxfFile(self):
        # Check if there are unsaved changes
        if self.canvas.shapes and self.confirmSaveChanges():
            # Save current file if user wants to
            self.saveFile()
        
        # Open file dialog
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть DXF файл", 
            "", 
            "DXF Files (*.dxf);;All Files (*)", 
            options=options
        )
        
        if filename:
            try:
                # Clear current shapes
                self.canvas.shapes.clear()
                
                # Load shapes from DXF file
                loaded_shapes = read_from_dxf(filename, self.canvas)
                
                # Add loaded shapes to canvas
                if loaded_shapes:
                    self.canvas.shapes.extend(loaded_shapes)
                    self.canvas.update()
                    self.constructionTree.updateConstructionTree()
                    
                    # Update current file
                    self.current_file = filename
                    self.fileNameLabel.setText(f"Файл: {self.getFileNameFromPath(filename)}")
                    self.statusBar.showMessage(f"Загружен файл: {filename}")
                else:
                    QMessageBox.warning(self, "Ошибка загрузки", "Не удалось загрузить фигуры из файла.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка загрузки", f"Произошла ошибка при загрузке файла:\n{str(e)}")
    
    def saveFile(self):
        # If no current file, use save as
        if not self.current_file:
            return self.saveFileAs()
        
        # Save to current file
        try:
            success = save_to_dxf_advanced(self.canvas.shapes, self.current_file)  # Используем advanced версию
            if success:
                self.statusBar.showMessage(f"Файл сохранен: {self.current_file}")
                return True
            else:
                QMessageBox.warning(self, "Ошибка сохранения", "Не удалось сохранить файл.")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", f"Произошла ошибка при сохранении файла:\n{str(e)}")
            return False
    
    def saveFileAs(self):
        # Open file dialog
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить как DXF файл", 
            "", 
            "DXF Files (*.dxf)", 
            options=options
        )
        
        if filename:
            # Add .dxf extension if not present
            if not filename.lower().endswith('.dxf'):
                filename += '.dxf'
                
            # Save to file
            try:
                success = save_to_dxf_advanced(self.canvas.shapes, filename)  # Используем advanced версию
                if success:
                    self.current_file = filename
                    self.fileNameLabel.setText(f"Файл: {self.getFileNameFromPath(filename)}")
                    self.statusBar.showMessage(f"Файл сохранен: {filename}")
                    return True
                else:
                    QMessageBox.warning(self, "Ошибка сохранения", "Не удалось сохранить файл.")
                    return False
            except Exception as e:
                QMessageBox.critical(self, "Ошибка сохранения", f"Произошла ошибка при сохранении файла:\n{str(e)}")
                return False
        
        return False
    
    def confirmSaveChanges(self):
        """Ask the user whether to save changes to the current file"""
        reply = QMessageBox.question(
            self, 
            "Несохраненные изменения", 
            "Сохранить изменения в текущем файле?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            return True
        elif reply == QMessageBox.Discard:
            return False
        else:  # Cancel
            return None
    
    def getFileNameFromPath(self, path):
        """Extract just the file name from a path"""
        import os
        return os.path.basename(path)
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.canvas.shapes and self.confirmSaveChanges():
            if self.saveFile():
                event.accept()
            else:
                # If save failed, ask if they want to quit anyway
                reply = QMessageBox.question(
                    self, 
                    "Ошибка сохранения", 
                    "Не удалось сохранить файл. Выйти без сохранения?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

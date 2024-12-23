from PyQt5.QtWidgets import QToolBar, QAction, QComboBox, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QColorDialog, QPushButton
from PyQt5.QtGui import QIcon, QColor
from PyQt5 import QtGui
from config.settings import LINE_TYPE, LINE_THICKNESS, DASH_SPACING


class ToolBar(QToolBar):
    def __init__(self, parent):
        super().__init__("Инструменты", parent)
        self.parent = parent  # Ссылаемся на главное окно

        # Инициализация параметров линии
        self.line_type = LINE_TYPE
        self.line_thickness = LINE_THICKNESS
        self.dash_spacing = DASH_SPACING
        self.style_applied = False  # Флаг, который отслеживает, применен ли стиль

        # Основной вертикальный layout для панели инструментов
        main_layout = QVBoxLayout()

        # Инструменты (верхний уровень)
        self.add_tools(main_layout)

        # Добавление виджетов для настройки стиля линий (второй уровень)
        self.add_line_style_controls(main_layout)

        # Добавление кнопки для применения стиля
        self.add_apply_style_button(main_layout)

        # Создаем центральный виджет и устанавливаем layout
        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.addWidget(central_widget)

    def add_tools(self, layout):
        """Добавление инструментов (верхний уровень)."""
        tools_layout = QHBoxLayout()  # Используем горизонтальный layout для компактного размещения

        # Добавляем все инструменты (включая методы дуг) в один список
        self.add_tool("Линия", tools_layout, "line")
        self.add_tool("Окружность", tools_layout, "circle")
        self.add_tool("Прямоугольник", tools_layout, "rectangle")
        self.add_tool("Многоугольник", tools_layout, "polygon")
        self.add_tool("Сплайн", tools_layout, "spline")
        self.add_tool("Дуга 3 точки", tools_layout, "three_points")
        self.add_tool("Дуга по хорде и радиусу", tools_layout, "radius_chord")

        layout.addLayout(tools_layout)

    def add_tool(self, label, layout, tool_name):
        """Добавление инструмента на панель."""
        button = QPushButton(label, self)
        button.setFixedSize(160, 30)  # Уменьшаем размер кнопки для компактного отображения
        button.clicked.connect(lambda: self.activate_tool(tool_name))  # Привязываем кнопку к действию
        layout.addWidget(button)  # Добавляем кнопку в layout

    def activate_tool(self, tool_name):
        """Активирует инструмент на холсте."""
        self.parent.canvas.set_tool(tool_name)

    def add_line_style_controls(self, layout):
        """Добавление виджетов для настройки стиля линий на панель инструментов."""
        style_controls_layout = QHBoxLayout()  # Горизонтальный layout для параметров линии

        # Тип линии
        line_style_combo = QComboBox(self)
        line_style_combo.addItem("Сплошная", "solid")
        line_style_combo.addItem("Штриховая", "dashed")
        line_style_combo.addItem("Пунктирная", "dotted")
        line_style_combo.addItem("Штрих-пунктирная", "dash-dotted")
        line_style_combo.addItem("Штрих-пунктирная с двумя точками", "dash-dot-two-points")
        line_style_combo.setCurrentText(self.get_line_type_label(self.line_type))
        line_style_combo.currentTextChanged.connect(lambda: self.change_line_type(line_style_combo.itemData(line_style_combo.currentIndex())))
        style_controls_layout.addWidget(line_style_combo)

        # Толщина линии
        thickness_input = QLineEdit(self)
        thickness_input.setText(str(self.line_thickness))
        thickness_input.setValidator(QtGui.QIntValidator(1, 100, self))
        thickness_input.editingFinished.connect(lambda: self.change_line_thickness(thickness_input.text()))
        style_controls_layout.addWidget(thickness_input)

        # Расстояние между штрихами
        dash_spacing_input = QLineEdit(self)
        dash_spacing_input.setText(str(self.dash_spacing))
        dash_spacing_input.setValidator(QtGui.QIntValidator(1, 100, self))
        dash_spacing_input.editingFinished.connect(lambda: self.change_dash_spacing(dash_spacing_input.text()))
        style_controls_layout.addWidget(dash_spacing_input)

        # Виджет для выбора цвета линии
        color_button = QPushButton("Цвет линии", self)
        color_button.setFixedSize(120, 30)  # Уменьшаем размер кнопки для компактного отображения
        color_button.clicked.connect(self.select_color)
        style_controls_layout.addWidget(color_button)

        layout.addLayout(style_controls_layout)

    def add_apply_style_button(self, layout):
        """Добавление кнопки 'Применить стиль'."""
        apply_button = QPushButton("Применить стиль", self)
        apply_button.setFixedSize(120, 30)
        apply_button.clicked.connect(self.apply_line_style)
        layout.addWidget(apply_button)

    def select_color(self):
        """Открывает диалог для выбора цвета линии."""
        color = QColorDialog.getColor(initial=QColor(0, 0, 0), parent=self)  # Черный цвет по умолчанию
        if color.isValid():
            self.set_line_color(color)

    def set_line_color(self, color):
        """Устанавливает выбранный цвет линии на холсте."""
        self.parent.canvas.update_line_color(color)

    def change_line_thickness(self, thickness):
        """Изменение толщины линии и обновление сцены."""
        try:
            thickness = int(thickness)
            if 1 <= thickness <= 100:
                self.line_thickness = thickness
        except ValueError:
            pass

    def change_line_type(self, line_type):
        """Изменение типа линии."""
        self.line_type = line_type

    def change_dash_spacing(self, spacing):
        """Изменение расстояния между штрихами."""
        try:
            spacing = int(spacing)
            if 1 <= spacing <= 100:
                self.dash_spacing = spacing
            else:
                raise ValueError("Расстояние между штрихами должно быть в диапазоне от 1 до 100.")
        except ValueError:
            pass

    def apply_line_style(self):
        """Применение стиля к новым линиям."""
        self.style_applied = True
        self.refresh_scene()  # Применяем стиль ко всем новым линиям

    def refresh_scene(self):
        """Перерисовывает сцену с новыми параметрами линии."""
        if self.style_applied:
            # Обновляем стиль для всех объектов
            self.parent.canvas.update_line_type(self.line_type)
            self.parent.canvas.update_line_thickness(self.line_thickness)
            self.parent.canvas.update_line_dash_spacing(self.dash_spacing)

    @staticmethod
    def get_line_type_label(line_type):
        """Получить название типа линии."""
        mapping = {
            "solid": "Сплошная",
            "dashed": "Штриховая",
            "dotted": "Точечная",
            "dash-dotted": "Штрих-пунктирная",
            "dash-dot-two-points": "Штрих-пунктирная с двумя точками"
        }
        return mapping.get(line_type, "Сплошная")

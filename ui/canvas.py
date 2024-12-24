from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPathItem, QSlider, QVBoxLayout, QWidget, QAction
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath
from core.geometry import draw_line, draw_polygon
from core.transformations import pan_view, zoom_view
from core.spline import update_bezier_curve, save_bezier_curve
from core.arc import draw_arc_three_points, draw_arc_radius_chord

class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        self.style_updated = False  # Флаг для отслеживания обновления стиля

        self.line_color = QColor(0, 0, 0)  # Черный цвет по умолчанию
        self.line_type = "solid"  # Тип линии по умолчанию
        self.line_thickness = 2  # Толщина линии по умолчанию
        self.dash_spacing = 5  # Расстояние между штрихами по умолчанию

        self.drawing_items = []  # Список элементов для рисования

        # Инициализация сетки и осей
        self.draw_grid()
        self.draw_axes()

        # Переменные для инструментов
        self.current_tool = None
        self.start_point = None
        self.temp_item = None
        self.points = []  # Для хранения точек для многоугольника и сплайнов

        self.control_points_items = []  # Графические элементы для точек
        self.spline_paths = []  # Список сплайнов
        self.is_editing = False
        self.editing_index = None

        # Панорамирование
        self.last_mouse_pos = None

        # Зум и масштаб
        self.scale_factor = 1.0

        # Добавляем элементы интерфейса для изменения стилей линий
        self.line_color = QColor(0, 0, 0)

        # Создание ползунков для изменения угла кривой Безье
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(0, 360)
        self.angle_slider.setValue(0)

        # Кнопки для изменения стилей
        self.line_style_action = QAction("Line Style", self)
        self.line_style_action.triggered.connect(self.update_line_style)

        # Кнопки для выбора дуги
        self.arc_button_3points = QAction("Arc (3 points)", self)
        self.arc_button_3points.triggered.connect(lambda: self.set_arc_method("three_points"))

        self.arc_button_radius_chord = QAction("Arc (Radius & Chord)", self)
        self.arc_button_radius_chord.triggered.connect(lambda: self.set_arc_method("radius_chord"))

        # Вставляем ползунок в интерфейс
        layout = QVBoxLayout()
        layout.addWidget(self.angle_slider)
        container = QWidget()
        container.setLayout(layout)
        container.show()

        # Дополнительные переменные для отслеживания объектов
        self.spline_path = None  # Путь кривой Безье
        self.arc_method = "three_points"  # По умолчанию метод "по 3 точкам"


    def update_line_color(self, color):
        print(f"Updated line color: {color.name()}")
        self.line_color = color
        self.style_updated = True

    def update_line_type(self, line_type):
        print(f"Updated line type: {line_type}")
        self.line_type = line_type
        self.style_updated = True

    def update_line_thickness(self, thickness):
        print(f"Updated line thickness: {thickness}")
        self.line_thickness = thickness
        self.style_updated = True

    def update_line_dash_spacing(self, spacing):
        print(f"Updated dash spacing: {spacing}")
        self.dash_spacing = spacing
        self.style_updated = True

    def set_arc_method(self, method):
        """Выбор метода рисования дуги."""
        self.arc_method = method
        self.points.clear()  # Сброс точек

    def update_line_style(self, item):
        """Применение стиля линии к графическому элементу."""
        if item is None:
            return  # Если item равен None, не продолжаем

        pen = QPen(self.line_color, self.line_thickness)
        pen.setStyle(self.get_pen_style(self.line_type))

        if self.line_type == "dash-dot-two-points":  # Обработка нового типа линии
            # Паттерн для штрих-пунктирной линии с двумя точками
            pen.setDashPattern([10, 5, 1, 5, 1, 5])  

        if self.line_type in ["dashed", "dotted", "dash-dotted", "dash-dot-two-points"]:
            pen.setDashOffset(self.dash_spacing)  # Применяем отступы для штрихов

        item.setPen(pen)

    def apply_style_to_new_items(self):
        """Применение стиля только к новым элементам."""
        if self.style_updated:
            self.style_updated = False  # Сбрасываем флаг
            # Применяем стиль только к новым элементам, рисуемым после изменения стиля
            if self.temp_item:
                self.update_line_style(self.temp_item)

    def set_tool(self, tool):
        # Завершаем текущую работу с инструментом перед переключением
        if self.current_tool == "spline" and self.points:
            save_bezier_curve(self)

        self.current_tool = tool
        self.start_point = None
        self.temp_item = None
        self.points.clear()
        self.clear_control_points()

    def wheelEvent(self, event):
        zoom_view(self, event)

    def mousePressEvent(self, event):
        """
        Обрабатывает события нажатия кнопок мыши.
        """
        pos = self.mapToScene(event.pos())  # Преобразуем координаты в сцену
        pen = QPen(self.line_color, self.line_thickness)  # Создаем Pen с цветом и толщиной
        pen.setStyle(self.get_pen_style(self.line_type))  # Устанавливаем стиль линии

        if event.button() == Qt.LeftButton:
            if self.current_tool == "line":
                self.start_point = pos  # Устанавливаем начальную точку для линии
            elif self.current_tool == "circle":
                self.start_point = pos  # Устанавливаем начальную точку для окружности
            elif self.current_tool == "rectangle":
                self.start_point = pos  # Устанавливаем начальную точку для прямоугольника
            elif self.current_tool in {"three_points", "radius_chord"}:
                # Работа с дугами
                self.points.append(pos)
                if self.current_tool == "three_points" and len(self.points) == 3:
                    draw_arc_three_points(self.scene, self.points, pen)  # Вызов функции рисования дуги
                    self.points.clear()
                elif self.current_tool == "radius_chord" and len(self.points) == 2:
                    draw_arc_radius_chord(self.scene, self.points, pen)  # Вызов функции рисования дуги
                    self.points.clear()
            elif self.current_tool == "polygon":
                # Добавляем новую точку в список точек полигона
                self.points.append(pos)
                if len(self.points) > 1:
                    draw_line(self.scene, self.points[-2], self.points[-1], pen)  # Рисуем линию между двумя последними точками
            elif self.current_tool == "spline":
                # Редактирование или добавление точек сплайна
                closest_index = self.get_closest_point(pos)
                if closest_index is not None:
                    self.is_editing = True
                    self.editing_index = closest_index
                else:
                    self.points.append(pos)
                    control_point_item = self.scene.addEllipse(
                        pos.x() - 5, pos.y() - 5, 10, 10, QPen(QColor(0, 0, 0), 2)
                    )
                    self.control_points_items.append(control_point_item)
                    update_bezier_curve(self)
        elif event.button() == Qt.MiddleButton:
            # Сохраняем позицию для панорамирования
            self.last_mouse_pos = event.pos()
        elif event.button() == Qt.RightButton:
            if self.current_tool == "polygon":
                # Завершаем рисование полигона
                draw_polygon(self.scene, self.points, pen)
                self.points.clear()
            elif self.current_tool == "spline":
                # Сохраняем текущий сплайн
                save_bezier_curve(self)

    def mouseMoveEvent(self, event):
        pen = QPen(self.line_color, self.line_thickness)  # Цвет и толщина
        pen.setStyle(self.get_pen_style(self.line_type))  # Стиль линии
        if event.buttons() == Qt.MiddleButton:
            pan_view(self, event)

        elif self.current_tool in {"line", "circle", "rectangle", "three_points", "radius_chord"} and self.start_point:
            end_point = self.mapToScene(event.pos())
            self.clear_temp_item()

            if self.line_type == "dash-dot-two-points":
                pen.setDashPattern([10, 5, 1, 5, 1, 5])

            if self.line_type in ["dashed", "dotted", "dash-dotted", "dash-dot-two-points"]:
                pen.setDashOffset(self.dash_spacing)

            if self.current_tool == "line":
                self.apply_style_to_new_items()  # Применяем стиль к новому элементу
                self.temp_item = self.scene.addLine(self.start_point.x(), self.start_point.y(), end_point.x(), end_point.y(), pen)

            elif self.current_tool == "circle":
                radius = self.distance(self.start_point, end_point)
                self.apply_style_to_new_items()  # Применяем стиль к новому элементу
                self.temp_item = self.scene.addEllipse(
                    self.start_point.x() - radius, self.start_point.y() - radius, radius * 2, radius * 2, pen
                )
            elif self.current_tool == "rectangle":
                width = end_point.x() - self.start_point.x()
                height = end_point.y() - self.start_point.y()
                self.apply_style_to_new_items()  # Применяем стиль к новому элементу
                self.temp_item = self.scene.addRect(
                    min(self.start_point.x(), end_point.x()),
                    min(self.start_point.y(), end_point.y()),
                    abs(width),
                    abs(height),
                    pen,
                )
            elif self.current_tool in {"three_points", "radius_chord"}:
                radius = self.distance(self.start_point, end_point)
                rect = QRectF(self.start_point.x() - radius, self.start_point.y() - radius, radius * 2, radius * 2)
                self.temp_item = self.scene.addPath(QPainterPath())  # Для временной дуги

        elif self.current_tool == "spline":
            # Проверяем корректность editing_index
            if self.editing_index is not None and 0 <= self.editing_index < len(self.points):
                pos = self.mapToScene(event.pos())
                self.points[self.editing_index] = pos
                control_item = self.control_points_items[self.editing_index]
                control_item.setRect(pos.x() - 5, pos.y() - 5, 10, 10)
                update_bezier_curve(self)
            else:
                # Сбрасываем редактирование, если индекс некорректен
                self.is_editing = False
                self.editing_index = None

    def mouseReleaseEvent(self, event):
        pen = QPen(self.line_color, self.line_thickness)  # Цвет и толщина
        pen.setStyle(self.get_pen_style(self.line_type))  # Стиль линии
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())

            if self.current_tool == "line" and self.start_point:
                # Создание линии и добавление ее в сцену
                line_item = self.scene.addLine(self.start_point.x(), self.start_point.y(), pos.x(), pos.y(), pen)
                self.drawing_items.append(line_item)  # Сохраняем в список рисуемых объектов
                self.update_line_style(line_item)  # Применяем стиль линии

                self.start_point = None
            elif self.current_tool == "circle" and self.start_point:
                radius = self.distance(self.start_point, pos)
                circle_item = self.scene.addEllipse(
                    self.start_point.x() - radius, self.start_point.y() - radius, radius * 2, radius * 2, pen
                )
                self.drawing_items.append(circle_item)
                self.update_line_style(circle_item)

                self.start_point = None
            elif self.current_tool == "rectangle" and self.start_point:
                width = pos.x() - self.start_point.x()
                height = pos.y() - self.start_point.y()
                rect_item = self.scene.addRect(
                    min(self.start_point.x(), pos.x()),
                    min(self.start_point.y(), pos.y()),
                    abs(width),
                    abs(height),
                    pen,
                )
                self.drawing_items.append(rect_item)
                self.update_line_style(rect_item)

                self.start_point = None


    def get_pen_style(self, line_type):
        """Возвращает стиль линии в зависимости от типа."""
        if line_type == "dashed":
            return Qt.DashLine
        elif line_type == "dotted":
            return Qt.DotLine
        elif line_type == "dash-dotted":
            return Qt.DashDotLine
        elif line_type == "dash-dot-two-points":
            return Qt.CustomDashLine  # Используем произвольный паттерн
        return Qt.SolidLine  # По умолчанию сплошная линия

    def clear_temp_item(self):
        if self.temp_item and self.temp_item.scene():
            self.scene.removeItem(self.temp_item)
            self.temp_item = None

    def clear_control_points(self):
        for item in self.control_points_items:
            if item.scene():
                self.scene.removeItem(item)
        self.control_points_items.clear()

    def draw_grid(self):
        grid_size = 20
        rect = QRectF(-20000, -10000, 40000, 20000)
        self.scene.setSceneRect(rect)
        pen = QPen(QColor(200, 200, 200), 0.5)
        for x in range(-20000, 20000, grid_size):
            self.scene.addLine(x, -10000, x, 10000, pen)
        for y in range(-10000, 10000, grid_size):
            self.scene.addLine(-20000, y, 20000, y, pen)

    def draw_axes(self):
        scene_rect = self.scene.sceneRect()
        pen = QPen(QColor(0, 0, 0), 2)
        # Ось X
        self.scene.addLine(scene_rect.left(), 0, scene_rect.right(), 0, pen)
        # Ось Y
        self.scene.addLine(0, scene_rect.top(), 0, scene_rect.bottom(), pen)

    @staticmethod
    def distance(point1, point2):
        return ((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2) ** 0.5

    def get_closest_point(self, pos):
        closest_index = None
        min_distance = float("inf")
        for i, point in enumerate(self.points):
            dist = self.distance(pos, point)
            if dist < min_distance and dist < 10:
                min_distance = dist
                closest_index = i
        return closest_index

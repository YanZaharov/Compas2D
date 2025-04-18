import math
from PySide6.QtWidgets import QWidget, QInputDialog, QMessageBox
from PySide6.QtGui import QPainter, QColor, QPen, QCursor
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QSizeF, Signal
from core.line import Line
from core.circle import Circle, CircleByThreePoints
from utils.handle_input import handle_manual_input
from core.arc import ArcByThreePoints, ArcByRadiusChord
from core.polygon import Polygon
from core.rectangle import Rectangle
from core.spline import BezierSpline, SegmentSpline

# Класс Canvas отвечает за отрисовку и обработку событий ввода
class Canvas(QWidget):
    zPressed = Signal()
    shapeAdded = Signal()
    shapeRemoved = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.handle_manual_input = lambda: handle_manual_input(self)
        self.parent = parent
        # Параметры отображения
        self.backgroundColor = QColor(255, 255, 255)  # Устанавливаем белый фон
        self.currentColor = QColor(0, 0, 0)  # Добавляем текущий цвет (по умолчанию черный)
        self.shapes = []  # Список для хранения нарисованных фигур
        self.current_shape = None  # Текущая фигура, которая рисуется
        # Режимы рисования и настройки линии
        self.drawingMode = 'line'      # Текущий режим рисования
        self.lineType = 'solid'         # Тип линии (стиль)
        self.lineThickness = 1.0        # Толщина линии

        self.points = []           # Список точек для рисования фигур
        self.temp_point = None     # Временная точка для отображения при рисовании

        # Параметры для панорамирования и масштабирования
        self.panning = False       # Флаг панорамирования
        self.lastPanPoint = QPoint()
        self.offset = QPoint(0, 0)  # Смещение для панорамирования
        self.scale = 1.0            # Масштабирование
        self.rotation = 0.0         # Поворот
        self.coordinateSystem = 'cartesian'  # 'cartesian' или 'polar' для отображения координат
        self.inputCoordinateSystem = 'cartesian'  # 'cartesian' или 'polar' для ввода координат

        # Дополнительные параметры
        self.numSides = 0           # Количество сторон для многоугольников
        self.centerPoint = None     # Центр для многоугольников и других фигур
        self.start_point = None     # Начальная точка для прямоугольника по сторонам
        self.radius_point = None    # Радиус-точка для дуги по радиусу и хорде

        self.cursor_position = None  # Позиция курсора в логических координатах

        self.show_axes = True  # Флаг отображения осей координат

        # Параметры штриховых линий
        self.dash_parameters = {
            'dash_length': 5,
            'dash_gap': 5,
            'dash_space': 3,
            'dot_length': 1,
            'dot_space': 2
        }
        self.dash_auto_mode = False  # Флаг автоматического режима
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)  # Для обработки событий клавиатуры

        # Для выделения фигур
        self.highlighted_shape_index = None
        self.show_grid = True  # Флаг отображения сетки
        self.grid_size = 50    # Размер ячейки сетки в пикселях
    
    def create_pen(self):
        pen = QPen()
        pen.setColor(self.currentColor)  # Устанавливаем текущий цвет
        pen.setWidthF(self.lineThickness)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.FlatCap)

        if self.lineType == 'solid':
            pen.setStyle(Qt.SolidLine)
        elif self.lineType in ['dash', 'dash_dot', 'dash_dot_dot']:
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern(self._compute_dash_pattern())
        else:
            pen.setStyle(Qt.SolidLine)

        return pen

    def drawGrid(self, painter):
        if not self.show_grid:
            return
            
        # Получаем размеры видимой области
        viewRect = self.rect()
        
        # Получаем все четыре угла видимой области
        corners = [
            self.mapToLogicalCoordinates(viewRect.topLeft()),
            self.mapToLogicalCoordinates(viewRect.topRight()),
            self.mapToLogicalCoordinates(viewRect.bottomLeft()),
            self.mapToLogicalCoordinates(viewRect.bottomRight())
        ]
        
        # Находим крайние точки для определения границ сетки
        left = min(corner.x() for corner in corners)
        right = max(corner.x() for corner in corners)
        top = max(corner.y() for corner in corners)
        bottom = min(corner.y() for corner in corners)
        
        # Расширяем границы, чтобы сетка полностью покрывала видимую область
        margin = self.grid_size * 2
        left = math.floor((left - margin) / self.grid_size) * self.grid_size
        right = math.ceil((right + margin) / self.grid_size) * self.grid_size
        top = math.ceil((top + margin) / self.grid_size) * self.grid_size
        bottom = math.floor((bottom - margin) / self.grid_size) * self.grid_size
        
        # Настраиваем перо для сетки
        gridPen = QPen(QColor(200, 200, 200))
        gridPen.setWidthF(0.5 / self.scale)
        painter.setPen(gridPen)
        
        # Рисуем вертикальные линии
        x = left
        while x <= right:
            painter.drawLine(QPointF(x, bottom), QPointF(x, top))
            x += self.grid_size
            
        # Рисуем горизонтальные линии
        y = bottom
        while y <= top:
            painter.drawLine(QPointF(left, y), QPointF(right, y))
            y += self.grid_size

    # Метод для выделения фигуры
    def highlightShape(self, index):
        self.highlighted_shape_index = index
        self.update()

    def setDrawingMode(self, mode):
        # Если переключаемся со сплайна Безье, сбрасываем его состояние
        if self.drawingMode == 'spline_bezier' and self.current_shape:
            if isinstance(self.current_shape, BezierSpline):
                self.current_shape.is_editing = False
                self.current_shape.editing_index = None
                self.current_shape.highlight_index = None
                # Добавляем сплайн в список фигур, если он еще не добавлен
                if len(self.current_shape.points) >= 3 and self.current_shape not in self.shapes:
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
        
        # Очищаем все временные данные
        self.points.clear()
        self.current_shape = None
        self.temp_point = None
        self.centerPoint = None
        self.radius_point = None
        self.start_point = None
        self.numSides = 0
        
        # Устанавливаем новый режим
        self.drawingMode = mode
        self.update()
        
        # Обновляем статусную строку
        if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
            self.parent.statusBar.showMessage(f"Режим рисования: {self.get_drawing_mode_text()}")

    # Метод отрисовки
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Включаем сглаживание
        painter.setRenderHint(QPainter.SmoothPixmapTransform)  # Сглаживание при трансформациях
        painter.fillRect(self.rect(), self.backgroundColor)  # Заполняем фон
        painter.save()

        # Применение преобразований: смещение, масштабирование, поворот
        painter.translate(self.width() / 2 + self.offset.x(), self.height() / 2 + self.offset.y())
        painter.scale(self.scale, self.scale)
        painter.rotate(self.rotation)
        painter.scale(1, -1)

        # Сохраняем преобразование
        self.transform = painter.transform()

        # Рисуем сетку
        self.drawGrid(painter)

        # Рисование осей координат
        if self.show_axes:
            length = 10000  # Длина осей

            # Рисуем ось X красным цветом
            penX = QPen(Qt.red)  # Цвет оси X
            penX.setWidthF(0.5)  # Толщина линии
            painter.setPen(penX)
            painter.drawLine(-length, 0, length, 0)

            # Рисуем ось Y синим цветом
            penY = QPen(Qt.blue)  # Цвет оси Y
            penY.setWidthF(0.5)  # Толщина линии
            painter.setPen(penY)
            painter.drawLine(0, -length, 0, length)


        # Рисование сохраненных фигур
        for index, shape in enumerate(self.shapes):
            if index == self.highlighted_shape_index:
                # Если фигура выделена, рисуем ее красным цветом с большей толщиной
                painter.save()
                pen = QPen(Qt.red)
                pen.setWidthF(shape.line_thickness + 2)
                painter.setPen(pen)
                shape.draw(painter)
                painter.restore()
            else:
                shape.draw(painter)

        # Рисование текущей фигуры (которая еще не завершена)
        if self.current_shape:
            # Используем временный стиль пунктира для рисования текущей фигуры
            temp_pen = QPen()
            temp_pen.setWidthF(self.lineThickness)
            temp_pen.setStyle(Qt.DotLine)  # Изменено на пунктирную линию
            self.current_shape.draw(painter, pen=temp_pen)
        else:
            # Рисование временных фигур при их создании (например, при перемещении мыши)
            temp_pen = QPen()
            temp_pen.setWidthF(self.lineThickness)
            temp_pen.setStyle(Qt.DotLine)  # Изменено на пунктирную линию
            if self.drawingMode == 'line' and self.points:
                # Если рисуем линию, отображаем линию от первой точки к текущей позиции мыши
                temp_line = Line(self.points[0], self.temp_point, self.lineType, self.lineThickness,
                                 dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_line.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'circle_center_radius' and self.centerPoint and self.temp_point:
                # Если рисуем окружность по центру и точке на окружности
                radius = math.hypot(self.temp_point.x() - self.centerPoint.x(),
                                    self.temp_point.y() - self.centerPoint.y())
                temp_circle = Circle(self.centerPoint, radius, self.lineType, self.lineThickness,
                                     dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_circle.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'rectangle_sides' and self.start_point and self.temp_point:
                # Если рисуем прямоугольник по сторонам
                rect = QRectF(self.start_point, self.temp_point).normalized()
                temp_rect = Rectangle(rect, self.lineType, self.lineThickness,
                                      dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_rect.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'rectangle_center' and self.centerPoint and self.temp_point:
                # Если рисуем прямоугольник от центра
                width = abs(self.temp_point.x() - self.centerPoint.x()) * 2
                height = abs(self.temp_point.y() - self.centerPoint.y()) * 2
                topLeft = QPointF(self.centerPoint.x() - width / 2, self.centerPoint.y() - height / 2)
                rect = QRectF(topLeft, QSizeF(width, height))
                temp_rect = Rectangle(rect.normalized(), self.lineType, self.lineThickness,
                                      dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_rect.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'polygon' and self.points:
                # Если рисуем многоугольник
                points = self.points.copy()
                if self.temp_point:
                    points.append(self.temp_point)
                if len(points) > 1:
                    temp_polygon = Polygon(points, self.lineType, self.lineThickness,
                                           dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                    temp_polygon.draw(painter, pen=temp_pen)

            elif self.drawingMode in ['spline_bezier', 'spline_segments'] and self.points:
                # Если рисуем сплайн
                points = self.points.copy()
                if self.temp_point:
                    points.append(self.temp_point)

                if self.drawingMode == 'spline_bezier':
                    temp_spline = BezierSpline(points, self.lineType, self.lineThickness,
                                               dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                else:
                    temp_spline = SegmentSpline(points, self.lineType, self.lineThickness,
                                                dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_spline.draw(painter, pen=temp_pen)

            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed'] and self.centerPoint and self.temp_point:
                # Если рисуем регулярный многоугольник (вписанный/описанный)
                radius_point = self.temp_point
                radius = math.hypot(radius_point.x() - self.centerPoint.x(),
                                    radius_point.y() - self.centerPoint.y())
                # Рисуем вспомогательную окружность
                pen = QPen(Qt.DotLine)
                pen.setWidthF(1)
                painter.setPen(pen)
                rect = QRectF(self.centerPoint.x() - radius, self.centerPoint.y() - radius,
                              2 * radius, 2 * radius)
                painter.drawEllipse(rect)
                if self.numSides > 0:
                    # Вычисляем вершины многоугольника
                    polygon_points = self.calculate_regular_polygon(self.centerPoint, radius_point, self.numSides,
                                                                    self.drawingMode)
                    temp_polygon = Polygon(polygon_points, self.lineType, self.lineThickness,
                                           dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                    temp_polygon.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'circle_three_points' and len(self.points) == 2 and self.temp_point:
                # Если рисуем окружность по трем точкам
                points = self.points + [self.temp_point]
                temp_circle = CircleByThreePoints(points, self.lineType, self.lineThickness,
                                                  dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_circle.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'arc_three_points' and len(self.points) == 2 and self.temp_point:
                # Если рисуем дугу по трем точкам
                points = self.points + [self.temp_point]
                temp_arc = ArcByThreePoints(points, self.lineType, self.lineThickness,
                                            dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_arc.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'arc_radius_chord' and self.centerPoint and self.radius_point and self.temp_point:
                # Если рисуем дугу по радиусу и хорде
                temp_arc = ArcByRadiusChord(self.centerPoint, self.radius_point, self.temp_point,
                                            self.lineType, self.lineThickness,
                                            dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                               color=self.currentColor)
                temp_arc.draw(painter, pen=temp_pen)

        painter.restore()  # Восстанавливаем состояние painter после рисования фигур

        # Добавляем код для отображения координат курсора
        painter.save()
        painter.resetTransform()  # Сбрасываем трансформации
        painter.setPen(Qt.black)  # Устанавливаем цвет пера для текста

        # Отображение координат курсора
        if self.cursor_position:
            x = self.cursor_position.x()
            y = self.cursor_position.y()
            if self.inputCoordinateSystem == 'cartesian':
                text = f"X: {x:.2f}, Y: {y:.2f}"
            else:
                r = math.hypot(x, y)
                theta = math.degrees(math.atan2(y, x))
                text = f"R: {r:.2f}, θ: {theta:.2f}°"

            # Получаем размер текста, чтобы правильно расположить его
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()

            rect = self.rect()
            x_pos = rect.right() - text_width - 10  # Отступ 10 пикселей от правого края
            y_pos = rect.bottom() - 10  # Отступ 10 пикселей от нижнего края

            painter.drawText(int(x_pos), int(y_pos), text)

        # Отображение текущего режима рисования, типа линии и толщины
        mode_text = f"Режим: {self.get_drawing_mode_text()}, Линия: {self.get_line_type_text()}, Толщина: {self.lineThickness}, Ввод: {self.get_input_coordinate_system_text()}"
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(mode_text)
        x_pos = (self.width() - text_width) / 2
        y_pos = self.height() - 10  # Отступ 10 пикселей от нижнего края

        painter.drawText(int(x_pos), int(y_pos), mode_text)

        painter.restore()
        
        # After drawing all shapes, highlight the selected one
        if self.highlighted_shape_index is not None:
            painter.save()
            painter.setPen(QPen(Qt.red, self.lineThickness + 2, Qt.SolidLine))
            shape = self.shapes[self.highlighted_shape_index]
            shape.draw(painter)
            painter.restore()

    # Метод для получения названия режима рисования
    def get_drawing_mode_text(self):
        mode_translation = {
            'line': 'Линия',
            'circle_center_radius': 'Окружность (центр и радиус)',
            'circle_three_points': 'Окружность (3 точки)',
            'arc_three_points': 'Дуга (3 точки)',
            'arc_radius_chord': 'Дуга (радиус и хорда)',
            'polygon': 'Многоугольник',
            'polygon_inscribed': 'Вписанный многоугольник',
            'polygon_circumscribed': 'Описанный многоугольник',
            'rectangle_sides': 'Прямоугольник по сторонам',
            'rectangle_center': 'Прямоугольник от центра',
            'spline_bezier': 'Сплайн Безье',
            'spline_segments': 'Сплайн по отрезкам'
        }
        return mode_translation.get(self.drawingMode, 'Неизвестный')

    # Метод для получения названия типа линии
    def get_line_type_text(self):
        line_type_translation = {
            'solid': 'Сплошная',
            'dash': 'Штриховая',
            'dash_dot': 'Штрих-пунктирная',
            'dash_dot_dot': 'Штрих-пунктирная с двумя точками'
        }
        return line_type_translation.get(self.lineType, 'Неизвестный')

    # Метод для получения названия системы координат ввода
    def get_input_coordinate_system_text(self):
        return 'Декартовый' if self.inputCoordinateSystem == 'cartesian' else 'Полярный'

    # Обработчик события нажатия мыши
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Преобразуем координаты экрана в логические координаты сцены
            logicalPos = self.mapToLogicalCoordinates(event.pos())
            coord = self.getCoordinate(logicalPos)

            self.temp_point = coord  # Обновляем временную точку
            self.cursor_position = coord  # Обновляем позицию курсора

            # Обработка в зависимости от текущего режима рисования
            if self.drawingMode == 'line':
                if not self.points:
                    self.points = [coord]
                else:
                    self.points.append(coord)
                    if len(self.points) == 2:
                        self.current_shape = Line(self.points[0], self.points[1], 
                                              self.lineType, self.lineThickness,
                                              dash_parameters=self.dash_parameters, 
                                              dash_auto_mode=self.dash_auto_mode,
                                              color=self.currentColor)
                        self.shapes.append(self.current_shape)
                        self.shapeAdded.emit()
                        self.current_shape = None
                        self.points.clear()
                        self.temp_point = None
                        self.update()

            elif self.drawingMode == 'circle_center_radius':
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    radius = math.hypot(coord.x() - self.centerPoint.x(),
                                    coord.y() - self.centerPoint.y())
                    self.current_shape = Circle(self.centerPoint, radius, 
                                            self.lineType, self.lineThickness,
                                            dash_parameters=self.dash_parameters, 
                                            dash_auto_mode=self.dash_auto_mode,
                                            color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'rectangle_sides':
                if not self.current_shape:
                    self.start_point = coord
                    self.current_shape = Rectangle(QRectF(coord, coord), 
                                               self.lineType, self.lineThickness,
                                               dash_parameters=self.dash_parameters, 
                                               dash_auto_mode=self.dash_auto_mode,
                                               color=self.currentColor)
                else:
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.start_point = None
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'circle_three_points':
                self.points.append(coord)
                if len(self.points) == 3:
                    self.current_shape = CircleByThreePoints(
                        self.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.points.clear()

            # Для дуги по трём точкам:
            elif self.drawingMode == 'arc_three_points':
                self.points.append(coord)
                if len(self.points) == 3:
                    self.current_shape = ArcByThreePoints(
                        self.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.points.clear()

            # Для дуги по радиусу и хорде:
            elif self.drawingMode == 'arc_radius_chord':
                if self.centerPoint is None:
                    self.centerPoint = coord
                elif self.radius_point is None:  # Добавляем эту проверку
                    self.radius_point = coord
                else:
                    self.current_shape = ArcByRadiusChord(
                        self.centerPoint, 
                        self.radius_point, 
                        coord,
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.radius_point = None

            elif self.drawingMode == 'polygon':
                self.points.append(coord)
                self.update()

            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed']:
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    if self.numSides == 0:
                        # Запрашиваем количество сторон у пользователя
                        self.numSides, ok = QInputDialog.getInt(self, "Количество сторон", "Введите количество сторон:", 3, 3, 100, 1)
                        if not ok:
                            self.centerPoint = None
                            self.numSides = 0
                            return
                    # Вычисляем вершины многоугольника и добавляем его
                    polygon_points = self.calculate_regular_polygon(self.centerPoint, coord, self.numSides,
                                                                    self.drawingMode)
                    self.current_shape = Polygon(polygon_points, self.lineType, self.lineThickness,
                                                 dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.numSides = 0
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'rectangle_center':
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    # Создаем и добавляем прямоугольник
                    width = abs(coord.x() - self.centerPoint.x()) * 2
                    height = abs(coord.y() - self.centerPoint.y()) * 2
                    topLeft = QPointF(self.centerPoint.x() - width / 2, self.centerPoint.y() - height / 2)
                    rect = QRectF(topLeft, QSizeF(width, height))
                    self.current_shape = Rectangle(rect.normalized(), self.lineType, self.lineThickness,
                                                   dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.temp_point = None
                    self.update()
            elif self.drawingMode == 'spline_bezier':
                # Проверяем, не пытается ли пользователь захватить контрольную точку существующего сплайна
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Добавляем проверку на существование атрибута
                    if not hasattr(self.current_shape, 'is_completed'):
                        self.current_shape.is_completed = False
                    
                    if not self.current_shape.is_completed:
                        clicked_point_index = self.current_shape.get_closest_point(coord)
                        if clicked_point_index is not None:
                            self.current_shape.editing_index = clicked_point_index
                            return

                # Если нет текущей фигуры или предыдущая была завершена,
                # начинаем новый сплайн
                if not self.current_shape or not self.points:
                    self.points = [coord]
                    self.current_shape = BezierSpline(self.points.copy(), self.lineType, self.lineThickness,
                                                dash_parameters=self.dash_parameters, 
                                                dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor)
                    # Убеждаемся, что атрибут существует у нового объекта
                    if not hasattr(self.current_shape, 'is_completed'):
                        self.current_shape.is_completed = False
                else:
                    # Добавляем точку к существующему сплайну
                    self.points.append(coord)
                    self.current_shape.points = self.points.copy()

            elif self.drawingMode == 'spline_segments':
                self.points.append(coord)
                self.update()

            self.update()

        elif event.button() == Qt.RightButton:
            # Обработка завершения рисования многоугольника или сплайна
            if self.drawingMode == 'polygon' and len(self.points) >= 3:
                self.current_shape = Polygon(self.points.copy(), self.lineType, self.lineThickness,
                                             dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor)
                self.shapes.append(self.current_shape)
                self.shapeAdded.emit()
                self.current_shape = None
                self.points.clear()
                self.temp_point = None
                self.update()

            elif self.drawingMode == 'spline_bezier' and len(self.points) >= 3:
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Помечаем сплайн как завершенный
                    self.current_shape.is_completed = True
                    self.current_shape.is_editing = False
                    # Создаем новый сплайн с текущими точками
                    new_spline = BezierSpline(
                        self.current_shape.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    new_spline.is_completed = True  # Важно: помечаем новый сплайн как завершенный
                    new_spline.is_editing = False   # И выключаем режим редактирования
                    self.shapes.append(new_spline)
                    self.shapeAdded.emit()
                
                # Сбрасываем все состояния для следующего построения
                self.current_shape = None
                self.points = []
                self.temp_point = None
                self.update()

            elif self.drawingMode == 'spline_segments' and len(self.points) >= 2:
                self.current_shape = SegmentSpline(self.points.copy(), self.lineType, self.lineThickness,
                                                   dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor)
                self.shapes.append(self.current_shape)
                self.shapeAdded.emit()
                self.current_shape = None
                self.points.clear()
                self.temp_point = None
                self.update()
            else:
                # Отмена текущего рисования
                self.points.clear()
                self.current_shape = None
                self.temp_point = None
                self.update()
        elif event.button() == Qt.MiddleButton:
            # Начало панорамирования
            self.panning = True
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            self.lastPanPoint = event.pos()

    # Обработчик движения мыши
    def mouseMoveEvent(self, event):
        if self.panning:
            # Обработка панорамирования
            delta = event.pos() - self.lastPanPoint
            self.offset += delta
            self.lastPanPoint = event.pos()
            self.update()
        elif self.drawingMode:
            # Преобразуем координаты экрана в логические координаты сцены
            logicalPos = self.mapToLogicalCoordinates(event.pos())
            coord = self.getCoordinate(logicalPos)
            self.temp_point = coord  # Обновляем временную точку
            self.cursor_position = coord  # Обновляем позицию курсора

            # Обновляем текущую фигуру в зависимости от режима рисования
            if self.drawingMode == 'line' and self.points:
                if len(self.points) == 1:
                    self.current_shape = Line(self.points[0], coord, self.lineType, self.lineThickness,
                                          dash_parameters=self.dash_parameters, 
                                          dash_auto_mode=self.dash_auto_mode,
                                          color=self.currentColor)
            elif self.drawingMode == 'circle_center_radius' and self.centerPoint:
                radius = math.hypot(coord.x() - self.centerPoint.x(), coord.y() - self.centerPoint.y())
                self.current_shape = Circle(self.centerPoint, radius, self.lineType, self.lineThickness,
                                        dash_parameters=self.dash_parameters, 
                                        dash_auto_mode=self.dash_auto_mode,
                                        color=self.currentColor)
            elif self.drawingMode == 'rectangle_sides' and self.start_point:
                rect = QRectF(self.start_point, coord).normalized()
                self.current_shape = Rectangle(rect, self.lineType, self.lineThickness,
                                          dash_parameters=self.dash_parameters, 
                                          dash_auto_mode=self.dash_auto_mode,
                                          color=self.currentColor)

            elif self.drawingMode == 'rectangle_center' and self.centerPoint:
                pass  # Обработка происходит в paintEvent

            elif self.drawingMode == 'spline_bezier':
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Проверяем, не перетаскивается ли точка
                    if self.current_shape.editing_index is not None:
                        # Обновляем позицию перетаскиваемой точки
                        self.current_shape.points[self.current_shape.editing_index] = coord
                        self.points = self.current_shape.points  # Обновляем список точек
                    
                    # Обновляем подсветку ближайшей точки
                    self.current_shape.highlight_index = self.current_shape.get_closest_point(coord)

            elif self.drawingMode in ['polygon', 'spline_segments']:
                pass  # Обработка происходит в paintEvent
            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed'] and self.centerPoint:
                pass  # Обработка происходит в paintEvent
            elif self.drawingMode == 'arc_radius_chord' and self.centerPoint and self.radius_point:
                pass  # Обработка происходит в paintEvent

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            # Завершаем панорамирование
            self.panning = False
            self.setCursor(QCursor(Qt.ArrowCursor))
        elif event.button() == Qt.LeftButton:
            if self.drawingMode == 'spline_bezier':
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    self.current_shape.editing_index = None

    # Обработчик прокрутки колесика мыши для масштабирования
    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        self.scale += delta * 0.1
        if self.scale < 0.1:
            self.scale = 0.1
        self.update()

    # Преобразование экранных координат в логические координаты сцены
    def mapToLogicalCoordinates(self, pos):
        if hasattr(self, 'transform'):
            inverse_transform, ok = self.transform.inverted()
            if ok:
                logical_pos = inverse_transform.map(pos)
                return logical_pos
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось инвертировать преобразование.")
                return QPointF()
        else:
            return QPointF(pos)

    # Получение координат в зависимости от системы координат
    def getCoordinate(self, pos):
        if self.coordinateSystem == 'cartesian':
            return pos
        elif self.coordinateSystem == 'polar':
            r = math.hypot(pos.x(), pos.y())
            theta = math.atan2(pos.y(), pos.x())
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            return QPointF(x, y)

    # Вычисление вершин регулярного многоугольника (вписанного или описанного)
    def calculate_regular_polygon(self, center, radius_point, num_sides, mode):
        radius = math.hypot(radius_point.x() - center.x(), radius_point.y() - center.y())
        points = []
        angle_step = 2 * math.pi / num_sides
        start_angle = math.atan2(radius_point.y() - center.y(), radius_point.x() - center.x())
        if mode == 'polygon_inscribed':
            vertex_radius = radius
        elif mode == 'polygon_circumscribed':
            vertex_radius = radius / math.cos(math.pi / num_sides)
        else:
            vertex_radius = radius
        for i in range(num_sides):
            angle = start_angle + i * angle_step
            x = center.x() + vertex_radius * math.cos(angle)
            y = center.y() + vertex_radius * math.sin(angle)
            points.append(QPointF(x, y))
        return points

    def rotate(self, angle):
        self.rotation += angle
        self.update()

    def zoomIn(self):
        self.scale *= 1.1  # Увеличиваем масштаб на 10%
        self.update()

    def zoomOut(self):
        self.scale /= 1.1  # Уменьшаем масштаб на 10%
        self.update()

    # Обработка нажатия клавиш
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            self.show_grid = not self.show_grid
            self.update()

        if event.key() == Qt.Key_Escape:
            # Отмена текущего построения
            self.points.clear()
            self.current_shape = None
            self.temp_point = None
            self.centerPoint = None
            self.radius_point = None
            self.start_point = None
            self.numSides = 0
            # Добавляем сброс состояния редактирования сплайна
            if isinstance(self.current_shape, BezierSpline):
                self.current_shape.is_editing = False
                self.current_shape.editing_index = None
                self.current_shape.highlight_index = None
            self.update()
            self.parent.statusBar.showMessage('Отмена текущего построения')

        if event.key() == Qt.Key_Z:
            if self.shapes:
                self.shapes.pop()
            self.update()
            self.parent.statusBar.showMessage('Отмена предыдущего построения')
            self.zPressed.emit()

        if event.key() == Qt.Key_V:
            self.handle_manual_input()
        #Ctrl + стрелки
        elif event.key() == Qt.Key_Right and event.modifiers() & Qt.ControlModifier:
            self.rotation += 5  # Поворот против часовой стрелке
            self.update()
            self.parent.statusBar.showMessage('Поворот по часовой стрелке')
        elif event.key() == Qt.Key_Left and event.modifiers() & Qt.ControlModifier:
            self.rotation -= 5  # Поворот по часовой стрелки
            self.update()
            self.parent.statusBar.showMessage('Поворот против часовой стрелки')
        elif event.key() == Qt.Key_M:
            self.show_axes = not self.show_axes  # Переключаем отображение осей
            self.update()
        elif event.key() == Qt.Key_C:
            self.inputCoordinateSystem = 'cartesian'
            QMessageBox.information(self, "Система координат ввода", "Ввод координат будет производиться в Декартовой системе.")
        elif event.key() == Qt.Key_P:
            self.inputCoordinateSystem = 'polar'
            QMessageBox.information(self, "Система координат ввода", "Ввод координат будет производиться в Полярной системе.")
        else:
            super().keyPressEvent(event)

import math
from PySide6.QtGui import QPainterPath, QPen, QColor
from PySide6.QtCore import QPointF, QRectF
from core.base_geometry import Geometry
from math import factorial
from PySide6.QtCore import Qt

class BezierSpline(Geometry):
    def __init__(self, points, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.points = points
        self.num_segments = 100
        self.is_editing = False
        self.editing_index = None
        self.control_point_size = 6  # Размер контрольных точек
        self.highlight_index = None  # Индекс подсвеченной точки

    @staticmethod
    def binomial_coefficient(n, k):
        """Вычисляет биномиальный коэффициент"""
        return factorial(n) // (factorial(k) * factorial(n - k))

    def bezier_point(self, t):
        """Вычисляет точку на кривой Безье по параметру t"""
        n = len(self.points) - 1
        x, y = 0, 0
        for i in range(n + 1):
            binom = self.binomial_coefficient(n, i)
            factor = (1 - t) ** (n - i) * t ** i
            x += binom * factor * self.points[i].x()
            y += binom * factor * self.points[i].y()
        return QPointF(x, y)

    def generate_bezier_path(self):
        """Создает путь для кривой Безье"""
        if len(self.points) < 2:
            return None

        path = QPainterPath(self.points[0])
        t_values = [i / self.num_segments for i in range(self.num_segments + 1)]
        
        for t in t_values[1:]:
            point = self.bezier_point(t)
            path.lineTo(point)
        
        return path

    def draw(self, painter, pen=None):
        """Отрисовка сплайна и контрольных точек"""
        if len(self.points) < 2:
            return
                
        # Рисуем основную кривую
        super().draw(painter, pen)
        path = self.generate_bezier_path()
        if path:
            old_background_mode = painter.backgroundMode()
            painter.setBackgroundMode(Qt.TransparentMode)
            painter.drawPath(path)
            painter.setBackgroundMode(old_background_mode)

        # Добавляем проверку на существование атрибута
        if not hasattr(self, 'is_completed'):
            self.is_completed = False

        # Показываем контрольные точки при создании или редактировании
        if not self.is_completed:
            original_pen = painter.pen()
            
            control_pen = QPen(Qt.DashLine)
            control_pen.setColor(QColor(128, 128, 128))
            control_pen.setWidth(1)
            painter.setPen(control_pen)
            
            for i in range(len(self.points) - 1):
                painter.drawLine(self.points[i], self.points[i + 1])

            for i, point in enumerate(self.points):
                if i == self.highlight_index:
                    painter.setBrush(QColor(255, 165, 0))
                    painter.setPen(QPen(QColor(255, 140, 0), 2))
                else:
                    painter.setBrush(QColor(255, 255, 255))
                    painter.setPen(QPen(QColor(0, 0, 0), 1))
                
                rect = QRectF(
                    point.x() - self.control_point_size/2,
                    point.y() - self.control_point_size/2,
                    self.control_point_size,
                    self.control_point_size
                )
                painter.drawRect(rect)

            painter.setPen(original_pen)

    def get_closest_point(self, pos, threshold=10):
        """Находит ближайшую контрольную точку"""
        for i, point in enumerate(self.points):
            if (point.x() - pos.x()) ** 2 + (point.y() - pos.y()) ** 2 < threshold ** 2:
                return i
        return None

    def update_point(self, index, new_pos):
        """Обновляет положение контрольной точки"""
        if 0 <= index < len(self.points):
            self.points[index] = new_pos

    def get_total_length(self):
        """Вычисляет общую длину сплайна"""
        if len(self.points) < 2:
            return 0

        length = 0
        prev_point = self.bezier_point(0)
        
        for i in range(1, self.num_segments + 1):
            t = i / self.num_segments
            current_point = self.bezier_point(t)
            length += math.hypot(current_point.x() - prev_point.x(), 
                               current_point.y() - prev_point.y())
            prev_point = current_point
            
        return length

class SegmentSpline(Geometry):
    def __init__(self, points, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.points = points

    def draw(self, painter, pen=None):
        if len(self.points) < 2:
            return
        super().draw(painter, pen)
        spline_points = self.generate_spline_points()
        if spline_points:
            painter.drawPolyline([QPointF(pt.x(), pt.y()) for pt in spline_points])

    def generate_spline_points(self):
        spline_points = []
        num_points = 20
        for i in range(len(self.points) - 1):
            p0 = self.points[i - 1] if i > 0 else self.points[i]
            p1 = self.points[i]
            p2 = self.points[i + 1]
            p3 = self.points[i + 2] if i + 2 < len(self.points) else self.points[i + 1]
            spline_points.extend(self.catmull_rom_spline(p0, p1, p2, p3, num_points))
        return spline_points

    def catmull_rom_spline(self, p0, p1, p2, p3, num_points):
        return [QPointF(
            0.5 * ((2 * p1.x()) + (-p0.x() + p2.x()) * t + (2 * p0.x() - 5 * p1.x() + 4 * p2.x() - p3.x()) * t**2 + (-p0.x() + 3 * p1.x() - 3 * p2.x() + p3.x()) * t**3),
            0.5 * ((2 * p1.y()) + (-p0.y() + p2.y()) * t + (2 * p0.y() - 5 * p1.y() + 4 * p2.y() - p3.y()) * t**2 + (-p0.y() + 3 * p1.y() - 3 * p2.y() + p3.y()) * t**3)
        ) for t in (i / (num_points - 1) for i in range(num_points))]

    def get_total_length(self):
        if len(self.points) < 2:
            return 0
        length = 0
        previous_point = self.points[0]
        spline_points = self.generate_spline_points()
        for point in spline_points:
            length += math.hypot(point.x() - previous_point.x(), point.y() - previous_point.y())
            previous_point = point
        return length

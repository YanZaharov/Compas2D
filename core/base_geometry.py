from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt
import math
from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF

# Базовый класс для всех фигур
class Geometry:
    def __init__(self, line_type='solid', line_thickness=1.0, dash_parameters=None, dash_auto_mode=False, color=None):
        self.line_type = line_type
        self.line_thickness = line_thickness
        self.dash_parameters = dash_parameters or {}
        self.dash_auto_mode = dash_auto_mode
        self.is_closed = False
        self.color = color or QColor(0, 0, 0)  # Добавляем цвет, по умолчанию черный

    def rotate_around_point(self, angle_degrees, center_point):
        """Поворачивает фигуру вокруг заданной точки"""
        angle_radians = math.radians(angle_degrees)
        cos_a = math.cos(angle_radians)
        sin_a = math.sin(angle_radians)
        
        def rotate_point(point):
            dx = point.x() - center_point.x()
            dy = point.y() - center_point.y()
            new_x = center_point.x() + dx * cos_a - dy * sin_a
            new_y = center_point.y() + dx * sin_a + dy * cos_a
            return QPointF(new_x, new_y)

        # Для каждого типа фигуры своя реализация поворота
        if hasattr(self, 'points'):
            self.points = [rotate_point(p) for p in self.points]
        if hasattr(self, 'start_point'):
            self.start_point = rotate_point(self.start_point)
        if hasattr(self, 'end_point'):
            self.end_point = rotate_point(self.end_point)
        if hasattr(self, 'center'):
            self.center = rotate_point(self.center)
        if hasattr(self, 'radius_point'):
            self.radius_point = rotate_point(self.radius_point)
        if hasattr(self, 'chord_point'):
            self.chord_point = rotate_point(self.chord_point)
        if hasattr(self, 'rect'):
            # Для прямоугольника поворачиваем все углы
            topleft = rotate_point(self.rect.topLeft())
            bottomright = rotate_point(self.rect.bottomRight())
            self.rect = QRectF(topleft, bottomright)

    def draw(self, painter, pen=None):
        painter.setPen(pen if pen else self.create_pen())

    def create_pen(self):
        pen = QPen()
        pen.setColor(self.color)  # Используем цвет фигуры
        pen.setWidthF(self.line_thickness)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.FlatCap)

        if self.line_type == 'solid':
            pen.setStyle(Qt.SolidLine)
        elif self.line_type in ['dash', 'dash_dot', 'dash_dot_dot']:
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern(self._compute_dash_pattern())
        else:
            pen.setStyle(Qt.SolidLine)

        return pen

    def _compute_dash_pattern(self):
        if self.dash_auto_mode:
            total_length = self.get_total_length() or 1  # Избегаем деления на ноль
            return self._generate_auto_dash_pattern(total_length)
        return self._generate_custom_dash_pattern()

    def _generate_auto_dash_pattern(self, total_length):
        if not self.is_closed:
            return self._generate_unclosed_pattern(total_length)
        return self._generate_closed_pattern(total_length)

    def _generate_unclosed_pattern(self, total_length):
        ratio_map = {'dash': [4, 2, 0], 'dash_dot': [4, 2, 2], 'dash_dot_dot': [4, 2, 1]}
        return self._compute_scaled_pattern(total_length, ratio_map.get(self.line_type, [4, 2, 0]))

    def _generate_closed_pattern(self, total_length):
        N = 10  # Количество повторений паттерна
        pattern_length = total_length / N
        dash_length = 0.6 * pattern_length
        gap_length = pattern_length - dash_length
        return [dash_length, gap_length]

    def _generate_custom_dash_pattern(self):
        params = self.dash_parameters
        if self.line_type == 'dash':
            return [params.get('dash_length', 5), params.get('dash_gap', 5)]
        if self.line_type == 'dash_dot':
            return [
                params.get('dash_length', 5), params.get('dash_space', 3),
                params.get('dot_length', 1), params.get('dash_space', 3)
            ]
        if self.line_type == 'dash_dot_dot':
            return [
                params.get('dash_length', 5), params.get('dash_space', 3),
                params.get('dot_length', 1), params.get('dot_space', 2),
                params.get('dot_length', 1), params.get('dash_space', 3)
            ]
        return []

    def _compute_scaled_pattern(self, total_length, ratios):
        pattern_count = 10
        scale_factor = self.line_thickness
        dash_ratio, gap_ratio, dot_ratio = ratios

        denominator = (
            pattern_count * dash_ratio +
            (pattern_count - 1) * (gap_ratio + (dot_ratio if dot_ratio > 0 else 0))
        )
        unit_length = total_length / denominator

        dash_length = unit_length * dash_ratio
        gap_length = unit_length * gap_ratio
        dot_length = unit_length * dot_ratio

        pattern = []
        for _ in range(pattern_count):
            pattern.append(dash_length)
            pattern.append(gap_length)
            if dot_ratio > 0:
                pattern.append(dot_length)
                pattern.append(gap_length)

        return pattern[:-1] if dot_ratio > 0 else pattern[:-2]

    def get_total_length(self):
        return 0

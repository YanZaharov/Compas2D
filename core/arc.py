import math
from PyQt5.QtCore import QRectF, QPointF
from core.base_geometry import Geometry

class ArcByThreePoints(Geometry):
    def __init__(self, points, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.points = points

    def draw(self, painter, pen=None):
        if len(self.points) < 3:
            return
        super().draw(painter, pen)
        center, radius, start_angle, span_angle = self.calculate_arc()
        if radius is None:
            return
        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        painter.drawArc(rect, int(-start_angle * 16), int(-span_angle * 16))

    def get_total_length(self):
        if len(self.points) < 3:
            return 0
        _, radius, _, span_angle = self.calculate_arc()
        return 0 if radius is None else radius * abs(math.radians(span_angle))

    def calculate_arc(self):
        A, B, C = self.points
        D = 2 * (A.x() * (B.y() - C.y()) + B.x() * (C.y() - A.y()) + C.x() * (A.y() - B.y()))
        if D == 0:
            return None, None, None, None
        Ux = ((A.x() ** 2 + A.y() ** 2) * (B.y() - C.y()) + (B.x() ** 2 + B.y() ** 2) * (C.y() - A.y()) + (C.x() ** 2 + C.y() ** 2) * (A.y() - B.y())) / D
        Uy = ((A.x() ** 2 + A.y() ** 2) * (C.x() - B.x()) + (B.x() ** 2 + B.y() ** 2) * (A.x() - C.x()) + (C.x() ** 2 + C.y() ** 2) * (B.x() - A.x())) / D
        center = QPointF(Ux, Uy)
        radius = math.hypot(center.x() - A.x(), center.y() - A.y())
        start_angle = math.degrees(math.atan2(A.y() - center.y(), A.x() - center.x()))
        mid_angle = math.degrees(math.atan2(B.y() - center.y(), B.x() - center.x()))
        end_angle = math.degrees(math.atan2(C.y() - center.y(), C.x() - center.x()))
        start_angle, mid_angle, end_angle = (start_angle + 360) % 360, (mid_angle + 360) % 360, (end_angle + 360) % 360
        span_angle = (end_angle - start_angle) % 360 if ((end_angle - start_angle + 360) % 360) >= ((mid_angle - start_angle + 360) % 360) else (end_angle - start_angle) % 360 - 360
        return center, radius, start_angle, span_angle

class ArcByRadiusChord(Geometry):
    def __init__(self, center, radius_point, chord_point, line_type='solid', 
                 line_thickness=1.0, dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.center = center
        self.radius_point = radius_point
        self.chord_point = chord_point

    def draw(self, painter, pen=None):
        super().draw(painter, pen)
        radius, start_angle, span_angle = self.calculate_arc()
        rect = QRectF(self.center.x() - radius, self.center.y() - radius, 2 * radius, 2 * radius)
        painter.drawArc(rect, int(-start_angle * 16), int(-span_angle * 16))

    def calculate_arc(self):
        # Вычисляем радиус
        radius = math.hypot(self.radius_point.x() - self.center.x(), 
                        self.radius_point.y() - self.center.y())
        
        # Вычисляем углы в градусах
        start_angle = math.degrees(math.atan2(self.radius_point.y() - self.center.y(), 
                                            self.radius_point.x() - self.center.x()))
        end_angle = math.degrees(math.atan2(self.chord_point.y() - self.center.y(), 
                                        self.chord_point.x() - self.center.x()))
        
        # Нормализуем углы в положительный диапазон
        start_angle = (start_angle + 360) % 360
        end_angle = (end_angle + 360) % 360
        
        # Вычисляем угол дуги
        span_angle = end_angle - start_angle
        if span_angle <= 0:
            span_angle += 360
        
        # Если дуга должна быть больше 180 градусов
        if math.hypot(self.chord_point.x() - self.radius_point.x(),
                    self.chord_point.y() - self.radius_point.y()) > radius * math.sqrt(2):
            if span_angle < 180:
                span_angle = 360 - span_angle
        
        return radius, start_angle, span_angle

    def get_total_length(self):
        radius, _, span_angle = self.calculate_arc()
        return radius * abs(math.radians(span_angle))

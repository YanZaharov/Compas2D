import math
from PyQt5.QtCore import QRectF, QPointF
from core.base_geometry import Geometry

class Circle(Geometry):
    def __init__(self, center, radius, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.center = center
        self.radius = radius

    def draw(self, painter, pen=None):
        super().draw(painter, pen)
        rect = QRectF(self.center.x() - self.radius, self.center.y() - self.radius, 
                     2 * self.radius, 2 * self.radius)
        painter.drawEllipse(rect)

    def get_total_length(self):
        return 2 * math.pi * self.radius

class CircleByThreePoints(Geometry):
    def __init__(self, points, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.points = points

    def draw(self, painter, pen=None):
        if len(self.points) < 3:
            return
        super().draw(painter, pen)
        center, radius = self.calculate_circle()
        if radius is None:
            return
        rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        painter.drawEllipse(rect)

    def get_total_length(self):
        if len(self.points) < 3:
            return 0
        _, radius = self.calculate_circle()
        return 0 if radius is None else 2 * math.pi * radius

    def calculate_circle(self):
        A, B, C = self.points
        D = 2 * (A.x() * (B.y() - C.y()) + B.x() * (C.y() - A.y()) + C.x() * (A.y() - B.y()))
        if D == 0:
            return None, None
        Ux = ((A.x() ** 2 + A.y() ** 2) * (B.y() - C.y()) + (B.x() ** 2 + B.y() ** 2) * (C.y() - A.y()) + (C.x() ** 2 + C.y() ** 2) * (A.y() - B.y())) / D
        Uy = ((A.x() ** 2 + A.y() ** 2) * (C.x() - B.x()) + (B.x() ** 2 + B.y() ** 2) * (A.x() - C.x()) + (C.x() ** 2 + C.y() ** 2) * (B.x() - A.x())) / D
        center = QPointF(Ux, Uy)
        radius = math.hypot(center.x() - A.x(), center.y() - A.y())
        return center, radius

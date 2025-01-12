import math
from core.base_geometry import Geometry

class Line(Geometry):
    def __init__(self, start_point, end_point, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, painter, pen=None):
        super().draw(painter, pen)
        painter.drawLine(self.start_point, self.end_point)

    def get_total_length(self):
        return math.hypot(self.end_point.x() - self.start_point.x(), 
                         self.end_point.y() - self.start_point.y())

import math
from core.base_geometry import Geometry

class Polygon(Geometry):
    def __init__(self, points, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.points = points

    def draw(self, painter, pen=None):
        if len(self.points) < 3:
            return
        super().draw(painter, pen)
        painter.drawPolygon(self.points)

    def get_total_length(self):
        if len(self.points) < 2:
            return 0
        return sum(math.hypot(self.points[i].x() - self.points[i - 1].x(),
                            self.points[i].y() - self.points[i - 1].y())
                  for i in range(len(self.points)))
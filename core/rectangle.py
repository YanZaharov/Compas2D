from core.base_geometry import Geometry

class Rectangle(Geometry):
    def __init__(self, rect, line_type='solid', line_thickness=1.0, 
                 dash_parameters=None, dash_auto_mode=False, color=None):
        super().__init__(line_type, line_thickness, dash_parameters, dash_auto_mode, color)
        self.rect = rect

    def draw(self, painter, pen=None):
        super().draw(painter, pen)
        painter.drawRect(self.rect)

    def get_total_length(self):
        return 2 * (self.rect.width() + self.rect.height())

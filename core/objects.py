class CADObject:
    """
    Базовый класс для всех объектов.
    """
    def __init__(self, color, thickness):
        self.color = color
        self.thickness = thickness


class Line(CADObject):
    """
    Класс для линий.
    """
    def __init__(self, start_point, end_point, color="black", thickness=1):
        super().__init__(color, thickness)
        self.start_point = start_point
        self.end_point = end_point


class Circle(CADObject):
    """
    Класс для окружностей.
    """
    def __init__(self, center, radius, color="blue", thickness=1):
        super().__init__(color, thickness)
        self.center = center
        self.radius = radius


class Rectangle(CADObject):
    """
    Класс для прямоугольников.
    """
    def __init__(self, top_left, width, height, color="purple", thickness=1):
        super().__init__(color, thickness)
        self.top_left = top_left
        self.width = width
        self.height = height


class Polygon(CADObject):
    """
    Класс для многоугольников.
    """
    def __init__(self, points, color="green", thickness=1):
        super().__init__(color, thickness)
        self.points = points

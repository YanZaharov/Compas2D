from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QPen
from math import factorial

def binomial_coefficient(n, k):
    """Вычисляет биномиальный коэффициент."""
    return factorial(n) // (factorial(k) * factorial(n - k))

def bezier_point(t, points):
    """Вычисляет точку на кривой Безье по параметру t."""
    n = len(points) - 1
    x, y = 0, 0
    for i in range(n + 1):
        binom = binomial_coefficient(n, i)
        factor = (1 - t) ** (n - i) * t ** i
        x += binom * factor * points[i].x()
        y += binom * factor * points[i].y()
    return x, y

def generate_bezier_path(points, num_segments=100):
    """Создает путь для кривой Безье."""
    if len(points) < 2:
        return None

    from PyQt5.QtGui import QPainterPath

    path = QPainterPath(points[0])
    t_values = [i / num_segments for i in range(num_segments + 1)]
    
    for t in t_values:
        x, y = bezier_point(t, points)
        path.lineTo(x, y)
    
    return path

def update_bezier_curve(self):
    if len(self.points) < 2:
        return
    self.clear_temp_item()
    path = generate_bezier_path(self.points)
    if path:
        self.temp_item = QGraphicsPathItem(path)
        self.temp_item.setPen(QPen(self.line_color, self.line_thickness))
        self.scene.addItem(self.temp_item)

def save_bezier_curve(self):
    if len(self.points) >= 2:
        path = generate_bezier_path(self.points)
        if path:
            final_path = QGraphicsPathItem(path)
            final_path.setPen(QPen(self.line_color, self.line_thickness))
            self.spline_paths.append(final_path)
            self.scene.addItem(final_path)
    self.points.clear()
    self.clear_control_points()
    self.clear_temp_item()

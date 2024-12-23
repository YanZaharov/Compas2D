from PyQt5.QtGui import QPen, QColor

def draw_line(scene, start_point, end_point, pen=None):
    """
    Рисует линию между двумя точками.
    """
    if not pen:
        pen = QPen(QColor(0, 0, 0), 2)  # Черный цвет по умолчанию
    scene.addLine(start_point.x(), start_point.y(), end_point.x(), end_point.y(), pen)

def draw_polygon(scene, points, pen=None):
    """
    Рисует многоугольник по списку точек.
    """
    if not pen:
        pen = QPen(QColor(0, 128, 0), 2)  # Зеленый цвет по умолчанию
    if len(points) < 3:
        raise ValueError("Для многоугольника нужно минимум три точки.")
    for i in range(len(points)):
        scene.addLine(points[i].x(), points[i].y(), points[(i + 1) % len(points)].x(), points[(i + 1) % len(points)].y(), pen)

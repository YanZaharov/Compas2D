from PyQt5.QtGui import QPen, QColor, QPainterPath
from PyQt5.QtCore import QRectF

def draw_line(scene, start_point, end_point, pen=None):
    """
    Рисует линию между двумя точками.
    """
    if not pen:
        pen = QPen(QColor(0, 0, 0), 2)  # Черный цвет по умолчанию
    scene.addLine(start_point.x(), start_point.y(), end_point.x(), end_point.y(), pen)

def draw_circle(scene, center, radius, pen=None):
    """
    Рисует окружность по центру и радиусу.
    """
    if not pen:
        pen = QPen(QColor(0, 0, 255), 2)  # Синий цвет по умолчанию
    if radius <= 0:
        raise ValueError("Радиус должен быть положительным.")
    scene.addEllipse(center.x() - radius, center.y() - radius, radius * 2, radius * 2, pen)

def draw_arc(scene, center, radius, start_angle, end_angle, pen=None):
    """
    Рисует дугу по центру, радиусу и углам (начальный и конечный).
    """
    if not pen:
        pen = QPen(QColor(255, 0, 0), 2)  # Красный цвет по умолчанию
    if radius <= 0:
        raise ValueError("Радиус должен быть положительным.")

    # Создание прямоугольника для дуги
    rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

    # Углы в 1/16 градуса для QPainterPath
    start_angle_16 = start_angle * 16
    end_angle_16 = end_angle * 16
    span_angle_16 = end_angle_16 - start_angle_16

    # Проверка на отрицательный угол
    if span_angle_16 < 0:
        span_angle_16 += 360 * 16  # Исправляем, если угол отрицательный

    # Создание пути для дуги
    path = QPainterPath()
    path.arcTo(rect, start_angle_16, span_angle_16)

    # Добавление пути на сцену
    scene.addPath(path, pen)

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

def draw_rectangle(scene, top_left, width, height, pen=None):
    """
    Рисует прямоугольник по верхнему левому углу, ширине и высоте.
    """
    if not pen:
        pen = QPen(QColor(128, 0, 128), 2)  # Фиолетовый цвет по умолчанию
    
    # Обработка отрицательной ширины и высоты
    x = top_left.x()
    y = top_left.y()
    if width < 0:
        x += width
        width = abs(width)
    if height < 0:
        y += height
        height = abs(height)
    
    # Рисуем прямоугольник
    scene.addRect(x, y, width, height, pen)

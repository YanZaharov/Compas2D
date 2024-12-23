from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen, QColor
from math import atan2, degrees
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtGui import QPainterPath
from PyQt5.QtCore import QRectF
from PyQt5.QtCore import Qt


def draw_arc_three_points(scene, points, pen):
    """
    Рисует дугу через три точки.
    """
    if len(points) == 3:
        result = calculate_arc_three_points(points)
        if result[0] is None:
            print("Не удалось вычислить дугу: точки могут быть на одной линии.")
            return None
        center, radius, start_angle, span_angle = result

        # Если угол больше 180 градусов, меняем направление дуги
        if span_angle > 180:
            span_angle = 360 - span_angle
            start_angle = (start_angle + 180) % 360

        return draw_arc(scene, center, radius, start_angle, span_angle, pen)


def calculate_arc_three_points(points):
    """
    Вычисляет параметры дуги (центр, радиус, углы) через три точки.
    """
    p1, p2, p3 = points

    # Вычисляем середины отрезков
    mid1 = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
    mid2 = QPointF((p2.x() + p3.x()) / 2, (p2.y() + p3.y()) / 2)

    # Вектора нормалей
    norm1 = QPointF(p2.y() - p1.y(), p1.x() - p2.x())
    norm2 = QPointF(p3.y() - p2.y(), p2.x() - p3.x())

    # Решаем систему уравнений для нахождения центра окружности
    det = norm1.x() * norm2.y() - norm1.y() * norm2.x()
    if abs(det) < 1e-6:  # Точки могут быть на одной линии
        return None, None, None, None

    t = ((mid2.x() - mid1.x()) * norm2.y() - (mid2.y() - mid1.y()) * norm2.x()) / det
    center = QPointF(mid1.x() + t * norm1.x(), mid1.y() + t * norm1.y())

    # Вычисляем радиус
    radius = ((center.x() - p1.x()) ** 2 + (center.y() - p1.y()) ** 2) ** 0.5

    # Углы
    start_angle = degrees(atan2(p1.y() - center.y(), p1.x() - center.x()))
    end_angle = degrees(atan2(p3.y() - center.y(), p3.x() - center.x()))
    span_angle = end_angle - start_angle
    if span_angle < 0:
        span_angle += 360

    return center, radius, start_angle, span_angle


def draw_arc_radius_chord(scene, points, pen):
    """
    Рисует дугу по радиусу и хорде.
    """
    if len(points) == 2:
        center = points[0]
        chord_end = points[1]
        radius = prompt_for_radius()

        if radius is not None:
            dist = distance(center, chord_end)
            if radius < dist:
                print(f"Радиус {radius} меньше расстояния от центра {dist}, попробуйте снова.")
                return None

            # Вычисление угла между центром и конечной точкой хорды
            angle = degrees(atan2(chord_end.y() - center.y(), chord_end.x() - center.x()))

            # Определяем начальный и конечный угол для дуги
            start_angle = angle - 90  # Начальный угол
            end_angle = angle + 90    # Конечный угол для дуги

            return draw_arc(scene, center, radius, start_angle, end_angle - start_angle, pen)


def prompt_for_radius():
    """
    Реализует диалог для ввода радиуса.
    """
    radius, ok = QInputDialog.getDouble(None, "Введите радиус", "Радиус:", 50, 1, 10000, 2)
    return radius if ok else None


def distance(point1, point2):
    """
    Вычисляет расстояние между двумя точками.
    """
    return ((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2) ** 0.5


def draw_arc(scene, center, radius, start_angle, span_angle, pen=None):
    """
    Рисует дугу по центру, радиусу и углам.
    """
    if not pen:
        pen = QPen(QColor(255, 0, 0), 2)  # Красный цвет по умолчанию
    if radius <= 0:
        raise ValueError("Радиус должен быть положительным.")

    # Создание прямоугольника для дуги
    rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

    # Углы в 1/16 градуса для QPainterPath
    start_angle_16 = start_angle * 16
    span_angle_16 = span_angle * 16

    # Создание пути для дуги
    path = QPainterPath()
    path.arcTo(rect, start_angle_16, span_angle_16)

    # Добавление пути на сцену
    scene.addPath(path, pen)

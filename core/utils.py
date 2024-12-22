from PyQt5.QtCore import QPointF
import math


def polar_to_cartesian(radius, angle_deg):
    """
    Переводит полярные координаты в декартовы.
    """
    angle_rad = math.radians(angle_deg)
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    return QPointF(x, y)


def cartesian_to_polar(point):
    """
    Переводит декартовы координаты в полярные.
    """
    radius = math.sqrt(point.x() ** 2 + point.y() ** 2)
    angle_deg = math.degrees(math.atan2(point.y(), point.x()))
    return radius, angle_deg


def calculate_distance(point1, point2):
    """
    Вычисляет расстояние между двумя точками.
    """
    return math.sqrt((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2)


def midpoint(point1, point2):
    """
    Вычисляет середину между двумя точками.
    """
    mid_x = (point1.x() + point2.x()) / 2
    mid_y = (point1.y() + point2.y()) / 2
    return QPointF(mid_x, mid_y)

from PyQt5.QtCore import QPointF
from math import cos, sin, radians


def pan_view(view, event):
    """
    Реализует панорамирование.
    """
    delta = event.pos() - view.last_mouse_pos
    view.last_mouse_pos = event.pos()
    view.horizontalScrollBar().setValue(view.horizontalScrollBar().value() - delta.x())
    view.verticalScrollBar().setValue(view.verticalScrollBar().value() - delta.y())


def zoom_view(view, event):
    """
    Реализует зуммирование с использованием колесика мыши.
    Учитывает ограничения по масштабу.
    """
    zoom_in_factor = 1.15
    zoom_out_factor = 0.85
    old_scale = view.scale_factor

    # Проверяем направление прокрутки
    if event.angleDelta().y() > 0:  # Zoom In
        new_scale_factor = view.scale_factor * zoom_in_factor
    else:  # Zoom Out
        new_scale_factor = view.scale_factor * zoom_out_factor

    # Ограничиваем масштабирование
    if 0.05 <= new_scale_factor <= 20.0:  # Ограничиваем минимальные и максимальные значения
        scale_factor_delta = new_scale_factor / old_scale
        view.scale(scale_factor_delta, scale_factor_delta)
        view.scale_factor = new_scale_factor
    else:
        event.ignore()  # Игнорируем событие, если масштаб выходит за границы



def rotate_scene(view, angle):
    """
    Реализует поворот сцены.
    """
    view.rotate(angle)


def rotate_point(point, center, angle):
    """
    Поворачивает точку вокруг центра на заданный угол.
    """
    angle_rad = radians(angle)
    translated_x = point.x() - center.x()
    translated_y = point.y() - center.y()

    rotated_x = cos(angle_rad) * translated_x - sin(angle_rad) * translated_y + center.x()
    rotated_y = sin(angle_rad) * translated_x + cos(angle_rad) * translated_y + center.y()

    return QPointF(rotated_x, rotated_y)

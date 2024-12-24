import math
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QMessageBox
from PyQt5.QtGui import QPen, QColor, QPainterPath
from math import atan2

class RadiusDialog(QDialog):
    def __init__(self, min_radius, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите радиус")
        self.setMinimumWidth(300)
        self.resize(300, 80)

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Радиус (минимум {min_radius:.2f}):", self)
        layout.addWidget(self.label)

        self.spin_box = QDoubleSpinBox(self)
        self.spin_box.setRange(min_radius, 10000)
        self.spin_box.setValue(min_radius)
        self.spin_box.setDecimals(2)
        layout.addWidget(self.spin_box)

        self.ok_button = QPushButton("OK", self)
        layout.addWidget(self.ok_button)

        self.ok_button.clicked.connect(self.accept)

    def get_radius(self):
        return self.spin_box.value()


def draw_arc_three_points(scene, points, pen):
    """
    Рисует дугу через три точки.
    """
    if len(points) != 3:
        print("Нужно указать три точки для построения дуги.")
        return None

    result = calculate_arc_three_points(points)
    if result[0] is None:
        print("Не удалось вычислить дугу: точки могут быть на одной линии.")
        return None

    center, radius, start_angle, end_angle = result

    # Рисуем дугу, используя параметрическое уравнение окружности
    return draw_arc_using_parametric_equation(scene, center, radius, start_angle, end_angle, pen)


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
    radius = distance(center, p1)

    # Углы
    start_angle = math.degrees(atan2(p1.y() - center.y(), p1.x() - center.x()))
    end_angle = math.degrees(atan2(p3.y() - center.y(), p3.x() - center.x()))

    return center, radius, start_angle, end_angle


def draw_arc_radius_chord(scene, points, pen):
    """
    Рисует дугу по радиусу и хорде.
    """
    if len(points) != 2:
        print("Нужно указать две точки: центр и конец хорды.")
        return None

    center, chord_end = points
    min_radius = distance(center, chord_end)

    # Ожидаем ввода радиуса через кастомный диалог
    dialog = RadiusDialog(min_radius)
    if dialog.exec_() != QDialog.Accepted:
        return None

    radius = dialog.get_radius()

    # Рассчитываем угол хорды относительно центра
    chord_angle = math.degrees(math.atan2(chord_end.y() - center.y(), chord_end.x() - center.x()))

    # Позиция начальной точки дуги относительно центра окружности и радиуса
    start_x = center.x() + radius * math.cos(math.radians(chord_angle))
    start_y = center.y() + radius * math.sin(math.radians(chord_angle))
    start_point = QPointF(start_x, start_y)

    # Определяем угол начальной и конечной точек
    start_angle = chord_angle
    end_angle = start_angle + 180  # угол на противоположной стороне окружности

    # Проверка на направление дуги
    if start_angle > end_angle:
        # Если начальный угол больше конечного, значит дуга по часовой стрелке
        start_angle, end_angle = end_angle, start_angle

    # Рисуем дугу, используя параметрическое уравнение окружности
    return draw_arc_using_parametric_equation(scene, center, radius, start_angle, end_angle, pen)

def draw_arc_using_parametric_equation(scene, center, radius, start_angle, end_angle, pen=None):
    """
    Рисует дугу с использованием параметрического уравнения окружности.
    """
    if radius <= 0:
        print("Радиус должен быть положительным.")
        return None

    # Преобразуем углы в радианы
    start_angle_rad = math.radians(start_angle)
    end_angle_rad = math.radians(end_angle)

    # Инициализируем путь для дуги
    path = QPainterPath()

    # Вычислим несколько точек на дуге
    num_points = 100  # Количество точек для дуги
    for i in range(num_points + 1):
        # Вычисляем угол на текущем шаге
        t = i / num_points
        angle = start_angle_rad + t * (end_angle_rad - start_angle_rad)

        # Параметрическое уравнение окружности
        x = center.x() + radius * math.cos(angle)
        y = center.y() + radius * math.sin(angle)

        point = QPointF(x, y)

        if i == 0:
            path.moveTo(point)  # Начальная точка дуги
        else:
            path.lineTo(point)  # Соединяем точки на дуге

    # Добавляем путь на сцену
    scene.addPath(path, pen)


def points_are_equal(point1, point2, tolerance=1e-6):
    """
    Сравнивает две точки с учетом погрешности (tolerance).
    """
    return abs(point1.x() - point2.x()) < tolerance and abs(point1.y() - point2.y()) < tolerance


def distance(point1, point2):
    """
    Вычисляет расстояние между двумя точками.
    """
    return ((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2) ** 0.5

import math
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from PyQt5.QtCore import QPointF, QRectF, QSizeF
from core.line import Line
from core.circle import Circle, CircleByThreePoints
from core.arc import ArcByThreePoints, ArcByRadiusChord
from core.polygon import Polygon
from core.rectangle import Rectangle

def handle_manual_input(self):
    if self.drawingMode == 'arc_radius_chord':
        if self.centerPoint is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты центра X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты центра R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.centerPoint = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.centerPoint is not None and self.radius_point is None:
            radius, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите радиус:", min=0.1)
            if not ok:
                return
            else:
                # Задаём точку радиуса на угле 0 градусов
                x = self.centerPoint.x() + radius
                y = self.centerPoint.y()
                self.radius_point = QPointF(x, y)
                return
        if self.centerPoint is not None and self.radius_point is not None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты конца хорды X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты конца хорды R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                chord_point = QPointF(x, y)
                self.current_shape = ArcByRadiusChord(self.centerPoint, self.radius_point, chord_point,
                                                self.lineType, self.lineThickness,
                                                dash_parameters=self.dash_parameters, 
                                                dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
                self.shapes.append(self.current_shape)
                self.shapeAdded.emit()
                self.current_shape = None
                self.centerPoint = None
                self.radius_point = None
                self.update()
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return

    elif self.drawingMode == 'line':
        if len(self.points) == 0:
                    # Первая точка всегда в декартовых координатах
                    prompt_text = "Введите координаты начальной точки X Y через пробел:"
                    coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
                    if not ok:
                        return
                    try:
                        x_str, y_str = coord_str.strip().split()
                        x = float(x_str)
                        y = float(y_str)
                        self.points.append(QPointF(x, y))
                    except ValueError:
                        QMessageBox.warning(self, "Ошибка ввода", 
                            "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                        return
        if len(self.points) == 1:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты конечной точки X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты конечной точки R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.points.append(QPointF(x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
            self.current_shape = Line(self.points[0], self.points[1], self.lineType, self.lineThickness,
                                    dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.points.clear()
            self.update()

    elif self.drawingMode == 'circle_center_radius':
        if self.centerPoint is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты центра X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты центра R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.centerPoint = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.centerPoint is not None:
            radius, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите радиус:", min=0.1)
            if not ok:
                return
            self.current_shape = Circle(self.centerPoint, radius, self.lineType, self.lineThickness,
                                        dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.centerPoint = None
            self.update()

    elif self.drawingMode == 'rectangle_sides':
        if self.start_point is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты начальной вершины X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты начальной вершины R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.start_point = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.start_point is not None:
            length, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите длину по оси X:", min=0.1)
            if not ok:
                self.start_point = None
                return
            width, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите ширину по оси Y:", min=0.1)
            if not ok:
                self.start_point = None
                return
            # Calculate end_point
            end_point = QPointF(self.start_point.x() + length, self.start_point.y() + width)
            rect = QRectF(self.start_point, end_point).normalized()
            self.current_shape = Rectangle(rect, self.lineType, self.lineThickness,
                                        dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.start_point = None
            self.update()

    elif self.drawingMode == 'rectangle_center':
        if self.centerPoint is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты центра X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты центра R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.centerPoint = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.centerPoint is not None:
            dx, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите половину длины по оси X (полудиагональ по X):", min=0.1)
            if not ok:
                self.centerPoint = None
                return
            dy, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите половину длины по оси Y (полудиагональ по Y):", min=0.1)
            if not ok:
                self.centerPoint = None
                return
            topLeft = QPointF(self.centerPoint.x() - dx, self.centerPoint.y() - dy)
            width = 2 * dx
            height = 2 * dy
            rect = QRectF(topLeft, QSizeF(width, height))
            self.current_shape = Rectangle(rect.normalized(), self.lineType, self.lineThickness,
                                        dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.centerPoint = None
            self.update()

    elif self.drawingMode == 'circle_three_points':
        while len(self.points) < 3:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = f"Введите координаты точки {len(self.points)+1} X Y через пробел:"
            else:
                prompt_text = f"Введите полярные координаты точки {len(self.points)+1} R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok or coord_str.strip() == '':
                break
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.points.append(QPointF(x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if len(self.points) == 3:
            self.current_shape = CircleByThreePoints(self.points.copy(), self.lineType, self.lineThickness,
                                                    dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.points.clear()
            self.update()

    elif self.drawingMode == 'arc_three_points':
        while len(self.points) < 3:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = f"Введите координаты точки {len(self.points)+1} X Y через пробел:"
            else:
                prompt_text = f"Введите полярные координаты точки {len(self.points)+1} R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok or coord_str.strip() == '':
                break
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.points.append(QPointF(x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода", "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if len(self.points) == 3:
            self.current_shape = ArcByThreePoints(self.points.copy(), self.lineType, self.lineThickness,
                                                dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.points.clear()
            self.update()

        if self.centerPoint is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты центра X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты центра R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.centerPoint = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                    "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.centerPoint is not None and self.radius_point is None:
            radius, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите радиус:", min=0.1)
            if not ok:
                self.centerPoint = None
                return
            else:
                # Задаем точку радиуса под углом 0 градусов
                x = self.centerPoint.x() + radius
                y = self.centerPoint.y()
                self.radius_point = QPointF(x, y)
        if self.centerPoint is not None and self.radius_point is not None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты конца хорды X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты конца хорды R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok or coord_str.strip() == '':
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                chord_point = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                    "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
            self.current_shape = ArcByRadiusChord(self.centerPoint, self.radius_point, chord_point,
                                                self.lineType, self.lineThickness,
                                                dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
            self.shapes.append(self.current_shape)
            self.shapeAdded.emit()
            self.current_shape = None
            self.centerPoint = None
            self.radius_point = None
            self.update()

    elif self.drawingMode == 'polygon':
        # Ввод точек до тех пор, пока пользователь не отменит или не оставит поле пустым
        while True:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты вершины X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты вершины R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok or coord_str.strip() == '':
                break
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.points.append(QPointF(x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                    "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                continue
        self.update()

    elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed']:
        if self.centerPoint is None:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты центра X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты центра R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok:
                return
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.centerPoint = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                    "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                return
        if self.numSides == 0:
            numSides, ok = QInputDialog.getInt(self, "Количество сторон", "Введите количество сторон:", min=3)
            if ok:
                self.numSides = numSides
            else:
                self.centerPoint = None
                return
        radius, ok = QInputDialog.getDouble(self, "Ввод параметров", "Введите радиус:", min=0.1)
        if not ok:
            self.centerPoint = None
            self.numSides = 0
            return
        # Need a point at specified distance (radius) from center
        # Let's pick an angle of 0
        angle = 0
        x = self.centerPoint.x() + radius * math.cos(angle)
        y = self.centerPoint.y() + radius * math.sin(angle)
        radius_point = QPointF(x, y)
        polygon_points = self.calculate_regular_polygon(self.centerPoint, radius_point, self.numSides, self.drawingMode)
        self.current_shape = Polygon(polygon_points, self.lineType, self.lineThickness,
                                    dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                color=self.currentColor)
        self.shapes.append(self.current_shape)
        self.shapeAdded.emit()
        self.current_shape = None
        self.centerPoint = None
        self.numSides = 0
        self.update()

    elif self.drawingMode == 'spline_bezier' or self.drawingMode == 'spline_segments':
        # Ввод точек до тех пор, пока пользователь не отменит или не оставит поле пустым
        while True:
            if self.inputCoordinateSystem == 'cartesian':
                prompt_text = "Введите координаты точки X Y через пробел:"
            else:
                prompt_text = "Введите полярные координаты точки R θ через пробел (θ в градусах):"
            coord_str, ok = QInputDialog.getText(self, "Ввод координат", prompt_text)
            if not ok or coord_str.strip() == '':
                break
            try:
                x_str, y_str = coord_str.strip().split()
                if self.inputCoordinateSystem == 'cartesian':
                    x = float(x_str)
                    y = float(y_str)
                else:
                    r = float(x_str)
                    theta_degrees = float(y_str)
                    theta_radians = math.radians(theta_degrees)
                    x = r * math.cos(theta_radians)
                    y = r * math.sin(theta_radians)
                self.points.append(QPointF(x, y))
            except ValueError:
                QMessageBox.warning(self, "Ошибка ввода",
                                    "Некорректный ввод координат. Пожалуйста, введите два числа, разделенных пробелом.")
                continue
        self.update()

import math
from PySide6.QtWidgets import QWidget, QInputDialog, QMessageBox, QMenu
from PySide6.QtGui import (QPainter, QColor, QPen, QCursor, QBrush, QFont, 
                         QLinearGradient, QPainterPath, QRadialGradient, QPalette)
from PySide6.QtCore import Qt, QPoint, QPointF, QRectF, QSizeF, Signal, QLineF
from core.line import Line
from core.circle import Circle, CircleByThreePoints
from utils.handle_input import handle_manual_input
from core.arc import ArcByThreePoints, ArcByRadiusChord
from core.polygon import Polygon
from core.rectangle import Rectangle
from core.spline import BezierSpline, SegmentSpline

# Canvas class handles rendering and input processing
class Canvas(QWidget):
    zPressed = Signal()
    shapeAdded = Signal()
    shapeRemoved = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.handle_manual_input = lambda: handle_manual_input(self)
        self.parent = parent
        
        # Visual parameters
        self.backgroundColor = QColor(250, 250, 252)  # Slightly blue-tinted white
        self.currentColor = QColor(20, 90, 160)  # Professional blue
        self.gridColor = QColor(230, 230, 240)  # Light grid color
        self.gridMajorColor = QColor(200, 200, 220)  # Major grid lines
        self.axisXColor = QColor(190, 60, 60)  # Red for X axis
        self.axisYColor = QColor(60, 110, 180)  # Blue for Y axis
        self.selectionColor = QColor(255, 140, 0)  # Bright orange for selection
        
        # Storage
        self.shapes = []  # List to store drawn shapes
        self.current_shape = None  # Current shape being drawn
        
        # Drawing modes and line settings
        self.drawingMode = 'line'      # Current drawing mode
        self.lineType = 'solid'        # Line style
        self.lineThickness = 1.0       # Line thickness

        self.points = []           # Point list for shape drawing
        self.temp_point = None     # Temporary point for preview
        
        # Pan and zoom parameters
        self.panning = False       # Panning flag
        self.lastPanPoint = QPoint()
        self.offset = QPoint(0, 0)  # Pan offset
        self.scale = 1.0            # Zoom scale
        self.rotation = 0.0         # Rotation angle
        self.coordinateSystem = 'cartesian'  # 'cartesian' or 'polar' for display
        self.inputCoordinateSystem = 'cartesian'  # 'cartesian' or 'polar' for input
        
        # Additional parameters
        self.numSides = 0           # Polygon sides count
        self.centerPoint = None     # Center for polygons and other shapes
        self.start_point = None     # Start point for rectangle by sides
        self.radius_point = None    # Radius point for arcs
        
        self.cursor_position = None  # Cursor position in logical coordinates
        
        self.show_axes = True       # Flag to show coordinate axes
        
        # Dash line parameters
        self.dash_parameters = {
            'dash_length': 6,
            'dash_gap': 4,
            'dash_space': 3,
            'dot_length': 1,
            'dot_space': 2
        }
        self.dash_auto_mode = False  # Auto dash mode flag
        
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)  # For keyboard events
        
        # For shape highlight
        self.highlighted_shape_index = None
        self.show_grid = True       # Grid display flag
        self.grid_size = 50         # Grid cell size in pixels
        self.grid_subdivisions = 5  # Subdivisions within each major grid cell
        
        # Show snap to grid
        self.snap_to_grid = True  # Enable grid snapping
        self.snap_distance = 8    # Snap distance in pixels
        
        # Enable anti-aliasing for smoother lines
        self.setRenderHints = True
        
        # Context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, position):
        """Show context menu at the given position"""
        contextMenu = QMenu(self)
        
        # Add shape actions
        if self.drawingMode == 'line':
            contextMenu.addAction("Cancel Line", self.cancelCurrentShape)
        elif self.drawingMode == 'circle_center_radius':
            contextMenu.addAction("Cancel Circle", self.cancelCurrentShape)
        elif self.drawingMode == 'rectangle_sides':
            contextMenu.addAction("Cancel Rectangle", self.cancelCurrentShape)
        
        # Add general actions
        contextMenu.addSeparator()
        contextMenu.addAction("Undo Last Shape (Z)", lambda: self.pressEscapeKey())
        contextMenu.addAction("Toggle Grid (G)", lambda: self.toggleGrid())
        contextMenu.addAction("Toggle Snap to Grid", lambda: self.toggleSnapToGrid())
        
        contextMenu.exec(self.mapToGlobal(position))

    def toggleSnapToGrid(self):
        """Toggle snap to grid feature"""
        self.snap_to_grid = not self.snap_to_grid
        self.update()

    def cancelCurrentShape(self):
        """Cancel current shape"""
        self.points.clear()
        self.current_shape = None
        self.temp_point = None
        self.centerPoint = None
        self.radius_point = None
        self.start_point = None
        self.numSides = 0
        self.update()
        
    def pressEscapeKey(self):
        """Simulate Escape key press"""
        self.keyPressEvent(Qt.Key_Escape)
    
    def create_pen(self):
        pen = QPen()
        pen.setColor(self.currentColor)
        pen.setWidthF(self.lineThickness)
        pen.setCosmetic(False)
        pen.setCapStyle(Qt.RoundCap)  # Round caps for smoother lines
        pen.setJoinStyle(Qt.RoundJoin)  # Round joins for smoother corners

        if self.lineType == 'solid':
            pen.setStyle(Qt.SolidLine)
        elif self.lineType in ['dash', 'dash_dot', 'dash_dot_dot']:
            pen.setStyle(Qt.CustomDashLine)
            pen.setDashPattern(self._compute_dash_pattern())
        else:
            pen.setStyle(Qt.SolidLine)

        return pen

    def drawGrid(self, painter):
        if not self.show_grid:
            return
            
        # Get visible area
        viewRect = self.rect()
        
        # Get all four corners of the visible area
        corners = [
            self.mapToLogicalCoordinates(viewRect.topLeft()),
            self.mapToLogicalCoordinates(viewRect.topRight()),
            self.mapToLogicalCoordinates(viewRect.bottomLeft()),
            self.mapToLogicalCoordinates(viewRect.bottomRight())
        ]
        
        # Find extreme points for grid boundaries
        left = min(corner.x() for corner in corners)
        right = max(corner.x() for corner in corners)
        top = max(corner.y() for corner in corners)
        bottom = min(corner.y() for corner in corners)
        
        # Expand boundaries to fully cover visible area
        margin = self.grid_size * 2
        left = math.floor((left - margin) / self.grid_size) * self.grid_size
        right = math.ceil((right + margin) / self.grid_size) * self.grid_size
        top = math.ceil((top + margin) / self.grid_size) * self.grid_size
        bottom = math.floor((bottom - margin) / self.grid_size) * self.grid_size
        
        # Calculate small grid size
        small_grid_size = self.grid_size / self.grid_subdivisions
        
        # Set up grid pen for minor lines
        gridMinorPen = QPen(self.gridColor)
        gridMinorPen.setWidthF(0.3 / self.scale)
        
        # Set up grid pen for major lines
        gridMajorPen = QPen(self.gridMajorColor)
        gridMajorPen.setWidthF(0.6 / self.scale)
        
        # Draw minor grid lines first (if zoom level permits)
        if self.scale > 0.4:  # Only draw minor grid when zoomed in enough
            painter.setPen(gridMinorPen)
            
            # Minor vertical lines
            x = left
            while x <= right:
                for i in range(1, self.grid_subdivisions):
                    minor_x = x + i * small_grid_size
                    painter.drawLine(QPointF(minor_x, bottom), QPointF(minor_x, top))
                x += self.grid_size
                
            # Minor horizontal lines
            y = bottom
            while y <= top:
                for i in range(1, self.grid_subdivisions):
                    minor_y = y + i * small_grid_size
                    painter.drawLine(QPointF(left, minor_y), QPointF(right, minor_y))
                y += self.grid_size
        
        # Draw major grid lines
        painter.setPen(gridMajorPen)
        
        # Vertical major lines
        x = left
        while x <= right:
            painter.drawLine(QPointF(x, bottom), QPointF(x, top))
            x += self.grid_size
            
        # Horizontal major lines
        y = bottom
        while y <= top:
            painter.drawLine(QPointF(left, y), QPointF(right, y))
            y += self.grid_size

    # Highlight a shape
    def highlightShape(self, index):
        self.highlighted_shape_index = index
        self.repaint()  # Use repaint() for immediate redraw

    def setDrawingMode(self, mode):
        # If switching from Bezier spline, reset its state
        if self.drawingMode == 'spline_bezier' and self.current_shape:
            if isinstance(self.current_shape, BezierSpline):
                self.current_shape.is_editing = False
                self.current_shape.editing_index = None
                self.current_shape.highlight_index = None
                # Add spline to shape list if not already added
                if len(self.current_shape.points) >= 3 and self.current_shape not in self.shapes:
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
        
        # Clear all temporary data
        self.points.clear()
        self.current_shape = None
        self.temp_point = None
        self.centerPoint = None
        self.radius_point = None
        self.start_point = None
        self.numSides = 0
        
        # Set new mode
        self.drawingMode = mode
        self.update()
        
        # Update status bar
        if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
            self.parent.statusBar.showMessage(f"Drawing mode: {self.get_drawing_mode_text()}")

    # Drawing method
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing
        painter.setRenderHint(QPainter.SmoothPixmapTransform)  # Smooth transform
        
        # Fill background with gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.backgroundColor)
        gradient.setColorAt(1, QColor(240, 240, 245))  # Slightly darker at bottom
        painter.fillRect(self.rect(), gradient)
        
        painter.save()

        # Apply transformations: offset, scale, rotation
        painter.translate(self.width() / 2 + self.offset.x(), self.height() / 2 + self.offset.y())
        painter.scale(self.scale, self.scale)
        painter.rotate(self.rotation)
        painter.scale(1, -1)  # Invert Y axis to match Cartesian coordinates

        # Save transformation
        self.transform = painter.transform()

        # Draw grid
        self.drawGrid(painter)

        # Draw coordinate axes
        if self.show_axes:
            length = 10000  # Axis length

            # X axis (red)
            xAxisPen = QPen(self.axisXColor)
            xAxisPen.setWidthF(0.8)
            xAxisPen.setCosmetic(True)  # Constant width regardless of zoom
            painter.setPen(xAxisPen)
            painter.drawLine(-length, 0, length, 0)
            
            # Draw X axis arrow
            arrowSize = 10 / self.scale
            arrow_path = QPainterPath()
            arrow_path.moveTo(length, 0)
            arrow_path.lineTo(length - arrowSize, arrowSize/2)
            arrow_path.lineTo(length - arrowSize, -arrowSize/2)
            arrow_path.closeSubpath()
            painter.fillPath(arrow_path, self.axisXColor)
            
            # X axis label
            painter.save()
            painter.scale(1, -1)  # Flip text right-side up
            painter.setPen(self.axisXColor)
            font = QFont("Arial", 10 / self.scale)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QPointF(length - 20, -15 / self.scale), "X")
            painter.restore()

            # Y axis (blue)
            yAxisPen = QPen(self.axisYColor)
            yAxisPen.setWidthF(0.8)
            yAxisPen.setCosmetic(True)
            painter.setPen(yAxisPen)
            painter.drawLine(0, -length, 0, length)
            
            # Draw Y axis arrow
            arrow_path = QPainterPath()
            arrow_path.moveTo(0, length)
            arrow_path.lineTo(arrowSize/2, length - arrowSize)
            arrow_path.lineTo(-arrowSize/2, length - arrowSize)
            arrow_path.closeSubpath()
            painter.fillPath(arrow_path, self.axisYColor)
            
            # Y axis label
            painter.save()
            painter.scale(1, -1)  # Flip text right-side up
            painter.setPen(self.axisYColor)
            font = QFont("Arial", 10 / self.scale)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QPointF(15 / self.scale, -length + 20), "Y")
            painter.restore()
            
            # Draw origin dot
            painter.setBrush(QColor(50, 50, 50))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), 2 / self.scale, 2 / self.scale)

        # Draw saved shapes
        for index, shape in enumerate(self.shapes):
            if index == self.highlighted_shape_index:
                # If shape is highlighted, draw it with a glow effect
                # First draw a slightly blurred, wider version for the glow
                glow_pen = QPen(self.selectionColor)
                glow_pen.setWidthF(shape.line_thickness + 3)
                glow_pen.setCosmetic(True)
                painter.save()
                painter.setPen(glow_pen)
                shape.draw(painter)
                painter.restore()
                
                # Then draw the shape normally
                painter.save()
                shape_pen = QPen(self.selectionColor)
                shape_pen.setWidthF(shape.line_thickness + 1)
                painter.setPen(shape_pen)
                shape.draw(painter)
                painter.restore()
            else:
                shape.draw(painter)

        # Draw current shape (not yet finalized)
        if self.current_shape:
            # Use a dashed style for preview
            temp_pen = QPen()
            temp_pen.setWidthF(self.lineThickness)
            temp_pen.setStyle(Qt.DashLine)
            temp_pen.setColor(self.currentColor)
            self.current_shape.draw(painter, pen=temp_pen)
        else:
            # Draw temporary shapes during creation
            temp_pen = QPen()
            temp_pen.setWidthF(self.lineThickness)
            temp_pen.setStyle(Qt.DashLine)
            temp_pen.setColor(self.currentColor)
            
            # Different drawing modes
            if self.drawingMode == 'line' and self.points and self.temp_point:
                # Line preview
                temp_line = Line(self.points[0], self.temp_point, self.lineType, self.lineThickness,
                                 dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                 color=self.currentColor)
                temp_line.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'circle_center_radius' and self.centerPoint and self.temp_point:
                # Circle preview
                radius = math.hypot(self.temp_point.x() - self.centerPoint.x(),
                                   self.temp_point.y() - self.centerPoint.y())
                temp_circle = Circle(self.centerPoint, radius, self.lineType, self.lineThickness,
                                    dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                    color=self.currentColor)
                temp_circle.draw(painter, pen=temp_pen)
                
                # Draw radius line
                radius_pen = QPen(QColor(180, 180, 180))
                radius_pen.setWidthF(0.5)
                radius_pen.setStyle(Qt.DotLine)
                painter.setPen(radius_pen)
                painter.drawLine(self.centerPoint, self.temp_point)

            elif self.drawingMode == 'rectangle_sides' and self.start_point and self.temp_point:
                # Rectangle preview
                rect = QRectF(self.start_point, self.temp_point).normalized()
                temp_rect = Rectangle(rect, self.lineType, self.lineThickness,
                                     dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                     color=self.currentColor)
                temp_rect.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'rectangle_center' and self.centerPoint and self.temp_point:
                # Center rectangle preview
                width = abs(self.temp_point.x() - self.centerPoint.x()) * 2
                height = abs(self.temp_point.y() - self.centerPoint.y()) * 2
                topLeft = QPointF(self.centerPoint.x() - width / 2, self.centerPoint.y() - height / 2)
                rect = QRectF(topLeft, QSizeF(width, height))
                temp_rect = Rectangle(rect.normalized(), self.lineType, self.lineThickness,
                                     dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                     color=self.currentColor)
                temp_rect.draw(painter, pen=temp_pen)
                
                # Draw center lines
                center_pen = QPen(QColor(180, 180, 180))
                center_pen.setWidthF(0.5)
                center_pen.setStyle(Qt.DotLine)
                painter.setPen(center_pen)
                dx = abs(self.temp_point.x() - self.centerPoint.x())
                dy = abs(self.temp_point.y() - self.centerPoint.y())
                
                # Horizontal and vertical centerlines
                painter.drawLine(QPointF(self.centerPoint.x() - dx, self.centerPoint.y()),
                                QPointF(self.centerPoint.x() + dx, self.centerPoint.y()))
                painter.drawLine(QPointF(self.centerPoint.x(), self.centerPoint.y() - dy),
                                QPointF(self.centerPoint.x(), self.centerPoint.y() + dy))

            elif self.drawingMode == 'polygon' and self.points:
                # Polygon preview
                points = self.points.copy()
                if self.temp_point:
                    points.append(self.temp_point)
                if len(points) > 1:
                    temp_polygon = Polygon(points, self.lineType, self.lineThickness,
                                          dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                          color=self.currentColor)
                    temp_polygon.draw(painter, pen=temp_pen)

            elif self.drawingMode in ['spline_bezier', 'spline_segments'] and self.points:
                # Spline preview
                points = self.points.copy()
                if self.temp_point:
                    points.append(self.temp_point)

                if self.drawingMode == 'spline_bezier':
                    temp_spline = BezierSpline(points, self.lineType, self.lineThickness,
                                              dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                              color=self.currentColor)
                else:
                    temp_spline = SegmentSpline(points, self.lineType, self.lineThickness,
                                               dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                               color=self.currentColor)
                temp_spline.draw(painter, pen=temp_pen)

            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed'] and self.centerPoint and self.temp_point:
                # Regular polygon preview
                radius_point = self.temp_point
                radius = math.hypot(radius_point.x() - self.centerPoint.x(),
                                   radius_point.y() - self.centerPoint.y())
                
                # Draw helper circle
                circle_pen = QPen(QColor(180, 180, 180))
                circle_pen.setWidthF(0.5)
                circle_pen.setStyle(Qt.DotLine)
                painter.setPen(circle_pen)
                rect = QRectF(self.centerPoint.x() - radius, self.centerPoint.y() - radius,
                             2 * radius, 2 * radius)
                painter.drawEllipse(rect)
                
                # Draw radius line
                painter.drawLine(self.centerPoint, radius_point)
                
                if self.numSides > 0:
                    # Calculate polygon vertices
                    polygon_points = self.calculate_regular_polygon(self.centerPoint, radius_point, self.numSides,
                                                                   self.drawingMode)
                    temp_polygon = Polygon(polygon_points, self.lineType, self.lineThickness,
                                          dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                          color=self.currentColor)
                    temp_polygon.draw(painter, pen=temp_pen)

            elif self.drawingMode == 'circle_three_points' and len(self.points) == 2 and self.temp_point:
                # Three-point circle preview
                points = self.points + [self.temp_point]
                temp_circle = CircleByThreePoints(points, self.lineType, self.lineThickness,
                                                 dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                                 color=self.currentColor)
                temp_circle.draw(painter, pen=temp_pen)
                
                # Draw construction lines between points
                line_pen = QPen(QColor(180, 180, 180))
                line_pen.setWidthF(0.5)
                line_pen.setStyle(Qt.DotLine)
                painter.setPen(line_pen)
                for i in range(len(points)):
                    painter.drawLine(points[i], points[(i + 1) % len(points)])

            elif self.drawingMode == 'arc_three_points' and len(self.points) == 2 and self.temp_point:
                # Three-point arc preview
                points = self.points + [self.temp_point]
                temp_arc = ArcByThreePoints(points, self.lineType, self.lineThickness,
                                           dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                           color=self.currentColor)
                temp_arc.draw(painter, pen=temp_pen)
                
                # Draw construction lines between points
                line_pen = QPen(QColor(180, 180, 180))
                line_pen.setWidthF(0.5)
                line_pen.setStyle(Qt.DotLine)
                painter.setPen(line_pen)
                for i in range(len(points)-1):
                    painter.drawLine(points[i], points[i+1])

            elif self.drawingMode == 'arc_radius_chord' and self.centerPoint and self.radius_point and self.temp_point:
                # Arc by radius and chord preview
                temp_arc = ArcByRadiusChord(self.centerPoint, self.radius_point, self.temp_point,
                                           self.lineType, self.lineThickness,
                                           dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                           color=self.currentColor)
                temp_arc.draw(painter, pen=temp_pen)
                
                # Draw construction lines
                line_pen = QPen(QColor(180, 180, 180))
                line_pen.setWidthF(0.5)
                line_pen.setStyle(Qt.DotLine)
                painter.setPen(line_pen)
                painter.drawLine(self.centerPoint, self.radius_point)
                painter.drawLine(self.centerPoint, self.temp_point)

        painter.restore()  # Restore painter state after drawing shapes

        # Add UI overlay elements
        painter.save()
        painter.resetTransform()  # Reset transformations
        
        # Get a contrasting color for UI text based on background
        text_color = QColor(50, 50, 50)  # Default dark gray
        
        # Display cursor coordinates
        if self.cursor_position:
            x = self.cursor_position.x()
            y = self.cursor_position.y()
            
            # Format based on coordinate system
            if self.inputCoordinateSystem == 'cartesian':
                coord_text = f"X: {x:.2f}, Y: {y:.2f}"
            else:
                r = math.hypot(x, y)
                theta = math.degrees(math.atan2(y, x))
                coord_text = f"R: {r:.2f}, θ: {theta:.2f}°"

            # Draw a background panel for better readability
            font = QFont("Arial", 9)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.horizontalAdvance(coord_text)
            text_height = metrics.height()
            
            # Position in bottom right corner
            rect = self.rect()
            x_pos = rect.right() - text_width - 15
            y_pos = rect.bottom() - 15
            
            # Draw semi-transparent background
            panel_rect = QRectF(x_pos - 5, y_pos - text_height, text_width + 10, text_height + 5)
            painter.fillRect(panel_rect, QColor(255, 255, 255, 180))
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.drawRect(panel_rect)
            
            # Draw text
            painter.setPen(text_color)
            painter.drawText(int(x_pos), int(y_pos), coord_text)

        # Display current mode, line type and thickness
        mode_text = f"Mode: {self.get_drawing_mode_text()} | Line: {self.get_line_type_text()} | Thickness: {self.lineThickness} | Input: {self.get_input_coordinate_system_text()}"
        
        # Position at bottom center
        font = QFont("Arial", 9)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(mode_text)
        text_height = metrics.height()
        
        x_pos = (self.width() - text_width) / 2
        y_pos = self.height() - 12
        
        # Draw semi-transparent background panel
        panel_rect = QRectF(x_pos - 5, y_pos - text_height, text_width + 10, text_height + 5)
        painter.fillRect(panel_rect, QColor(255, 255, 255, 180))
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawRect(panel_rect)
        
        # Draw text
        painter.setPen(text_color)
        painter.drawText(int(x_pos), int(y_pos), mode_text)
        
        # Display selected object information
        if self.highlighted_shape_index is not None:
            if 0 <= self.highlighted_shape_index < len(self.shapes):
                highlight_text = f"Selected: Object {self.highlighted_shape_index + 1}"
                highlight_text_width = metrics.horizontalAdvance(highlight_text)
                
                # Position in top left
                highlight_x_pos = 15
                highlight_y_pos = 25
                
                # Draw panel
                panel_rect = QRectF(highlight_x_pos - 5, highlight_y_pos - text_height, 
                                   highlight_text_width + 10, text_height + 5)
                painter.fillRect(panel_rect, QColor(255, 255, 255, 180))
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawRect(panel_rect)
                
                # Draw text
                painter.setPen(text_color)
                painter.drawText(int(highlight_x_pos), int(highlight_y_pos), highlight_text)
                
                # Add small indicator for snap status
                if self.snap_to_grid:
                    snap_text = "Snap: ON"
                else:
                    snap_text = "Snap: OFF"
                    
                snap_width = metrics.horizontalAdvance(snap_text)
                snap_panel = QRectF(highlight_x_pos - 5, highlight_y_pos + 5, 
                                  snap_width + 10, text_height + 5)
                painter.fillRect(snap_panel, QColor(255, 255, 255, 180))
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawRect(snap_panel)
                
                painter.setPen(text_color)
                painter.drawText(int(highlight_x_pos), int(highlight_y_pos + 20), snap_text)

        painter.restore()

    # Get drawing mode text
    def get_drawing_mode_text(self):
        mode_translation = {
            'line': 'Line',
            'circle_center_radius': 'Circle (Center-Radius)',
            'circle_three_points': 'Circle (3 Points)',
            'arc_three_points': 'Arc (3 Points)',
            'arc_radius_chord': 'Arc (Radius-Chord)',
            'polygon': 'Polygon',
            'polygon_inscribed': 'Inscribed Polygon',
            'polygon_circumscribed': 'Circumscribed Polygon',
            'rectangle_sides': 'Rectangle (Sides)',
            'rectangle_center': 'Rectangle (Center)',
            'spline_bezier': 'Bezier Spline',
            'spline_segments': 'Segment Spline'
        }
        return mode_translation.get(self.drawingMode, 'Unknown')

    # Get line type text
    def get_line_type_text(self):
        line_type_translation = {
            'solid': 'Solid',
            'dash': 'Dashed',
            'dash_dot': 'Dash-Dot',
            'dash_dot_dot': 'Dash-Dot-Dot'
        }
        return line_type_translation.get(self.lineType, 'Unknown')

    # Get input coordinate system text
    def get_input_coordinate_system_text(self):
        return 'Cartesian' if self.inputCoordinateSystem == 'cartesian' else 'Polar'

    # Mouse press event handler
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Convert screen coordinates to logical coordinates
            logicalPos = self.mapToLogicalCoordinates(event.pos())
            
            # Apply grid snapping if enabled
            if self.snap_to_grid:
                logicalPos = self.snapToGrid(logicalPos)
                
            coord = self.getCoordinate(logicalPos)

            self.temp_point = coord  # Update temporary point
            self.cursor_position = coord  # Update cursor position

            # Handle based on current drawing mode
            if self.drawingMode == 'line':
                if not self.points:
                    self.points = [coord]
                else:
                    self.points.append(coord)
                    if len(self.points) == 2:
                        self.current_shape = Line(self.points[0], self.points[1], 
                                            self.lineType, self.lineThickness,
                                            dash_parameters=self.dash_parameters, 
                                            dash_auto_mode=self.dash_auto_mode,
                                            color=self.currentColor)
                        self.shapes.append(self.current_shape)
                        self.shapeAdded.emit()
                        self.current_shape = None
                        self.points.clear()
                        self.temp_point = None
                        self.update()

            elif self.drawingMode == 'circle_center_radius':
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    radius = math.hypot(coord.x() - self.centerPoint.x(),
                                   coord.y() - self.centerPoint.y())
                    self.current_shape = Circle(self.centerPoint, radius, 
                                           self.lineType, self.lineThickness,
                                           dash_parameters=self.dash_parameters, 
                                           dash_auto_mode=self.dash_auto_mode,
                                           color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'rectangle_sides':
                if not self.current_shape:
                    self.start_point = coord
                    self.current_shape = Rectangle(QRectF(coord, coord), 
                                             self.lineType, self.lineThickness,
                                             dash_parameters=self.dash_parameters, 
                                             dash_auto_mode=self.dash_auto_mode,
                                             color=self.currentColor)
                else:
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.start_point = None
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'circle_three_points':
                self.points.append(coord)
                if len(self.points) == 3:
                    self.current_shape = CircleByThreePoints(
                        self.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.points.clear()

            # For arc by three points:
            elif self.drawingMode == 'arc_three_points':
                self.points.append(coord)
                if len(self.points) == 3:
                    self.current_shape = ArcByThreePoints(
                        self.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.points.clear()

            # For arc by radius and chord:
            elif self.drawingMode == 'arc_radius_chord':
                if self.centerPoint is None:
                    self.centerPoint = coord
                elif self.radius_point is None:
                    self.radius_point = coord
                else:
                    self.current_shape = ArcByRadiusChord(
                        self.centerPoint, 
                        self.radius_point, 
                        coord,
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.radius_point = None

            elif self.drawingMode == 'polygon':
                self.points.append(coord)
                self.update()

            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed']:
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    if self.numSides == 0:
                        # Request number of sides from user
                        self.numSides, ok = QInputDialog.getInt(self, "Number of Sides", "Enter number of sides:", 3, 3, 100, 1)
                        if not ok:
                            self.centerPoint = None
                            self.numSides = 0
                            return
                    # Calculate polygon vertices and add it
                    polygon_points = self.calculate_regular_polygon(self.centerPoint, coord, self.numSides,
                                                                self.drawingMode)
                    self.current_shape = Polygon(polygon_points, self.lineType, self.lineThickness,
                                            dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                            color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.numSides = 0
                    self.temp_point = None
                    self.update()

            elif self.drawingMode == 'rectangle_center':
                if self.centerPoint is None:
                    self.centerPoint = coord
                else:
                    # Create and add rectangle
                    width = abs(coord.x() - self.centerPoint.x()) * 2
                    height = abs(coord.y() - self.centerPoint.y()) * 2
                    topLeft = QPointF(self.centerPoint.x() - width / 2, self.centerPoint.y() - height / 2)
                    rect = QRectF(topLeft, QSizeF(width, height))
                    self.current_shape = Rectangle(rect.normalized(), self.lineType, self.lineThickness,
                                             dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                             color=self.currentColor)
                    self.shapes.append(self.current_shape)
                    self.shapeAdded.emit()
                    self.current_shape = None
                    self.centerPoint = None
                    self.temp_point = None
                    self.update()
            elif self.drawingMode == 'spline_bezier':
                # Check if user is trying to grab a control point of existing spline
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Add check for attribute existence
                    if not hasattr(self.current_shape, 'is_completed'):
                        self.current_shape.is_completed = False
                    
                    if not self.current_shape.is_completed:
                        clicked_point_index = self.current_shape.get_closest_point(coord)
                        if clicked_point_index is not None:
                            self.current_shape.editing_index = clicked_point_index
                            return

                # If no current shape or previous was completed,
                # start a new spline
                if not self.current_shape or not self.points:
                    self.points = [coord]
                    self.current_shape = BezierSpline(self.points.copy(), self.lineType, self.lineThickness,
                                               dash_parameters=self.dash_parameters, 
                                               dash_auto_mode=self.dash_auto_mode,
                                               color=self.currentColor)
                    # Make sure attribute exists on new object
                    if not hasattr(self.current_shape, 'is_completed'):
                        self.current_shape.is_completed = False
                else:
                    # Add point to existing spline
                    self.points.append(coord)
                    self.current_shape.points = self.points.copy()

            elif self.drawingMode == 'spline_segments':
                self.points.append(coord)
                self.update()

            self.update()

        elif event.button() == Qt.RightButton:
            # Handle completion of polygon or spline drawing
            if self.drawingMode == 'polygon' and len(self.points) >= 3:
                self.current_shape = Polygon(self.points.copy(), self.lineType, self.lineThickness,
                                        dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                        color=self.currentColor)
                self.shapes.append(self.current_shape)
                self.shapeAdded.emit()
                self.current_shape = None
                self.points.clear()
                self.temp_point = None
                self.update()

            elif self.drawingMode == 'spline_bezier' and len(self.points) >= 3:
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Mark spline as completed
                    self.current_shape.is_completed = True
                    self.current_shape.is_editing = False
                    # Create new spline with current points
                    new_spline = BezierSpline(
                        self.current_shape.points.copy(), 
                        self.lineType, 
                        self.lineThickness,
                        dash_parameters=self.dash_parameters, 
                        dash_auto_mode=self.dash_auto_mode,
                        color=self.currentColor
                    )
                    new_spline.is_completed = True  # Important: mark new spline as completed
                    new_spline.is_editing = False   # And turn off editing mode
                    self.shapes.append(new_spline)
                    self.shapeAdded.emit()
                
                # Reset all states for next construction
                self.current_shape = None
                self.points = []
                self.temp_point = None
                self.update()

            elif self.drawingMode == 'spline_segments' and len(self.points) >= 2:
                self.current_shape = SegmentSpline(self.points.copy(), self.lineType, self.lineThickness,
                                              dash_parameters=self.dash_parameters, dash_auto_mode=self.dash_auto_mode,
                                              color=self.currentColor)
                self.shapes.append(self.current_shape)
                self.shapeAdded.emit()
                self.current_shape = None
                self.points.clear()
                self.temp_point = None
                self.update()
            else:
                # Cancel current drawing
                self.points.clear()
                self.current_shape = None
                self.temp_point = None
                self.update()
        elif event.button() == Qt.MiddleButton:
            # Start panning
            self.panning = True
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            self.lastPanPoint = event.pos()

    # Snap point to grid
    def snapToGrid(self, point):
        if not self.snap_to_grid:
            return point
            
        # Get grid cell size
        cell_size = self.grid_size
        
        # Calculate nearest grid point
        x = round(point.x() / cell_size) * cell_size
        y = round(point.y() / cell_size) * cell_size
        
        return QPointF(x, y)

    # Mouse move event handler
    def mouseMoveEvent(self, event):
        if self.panning:
            # Handle panning
            delta = event.pos() - self.lastPanPoint
            self.offset += delta
            self.lastPanPoint = event.pos()
            self.update()
        elif self.drawingMode:
            # Convert screen coordinates to logical coordinates
            logicalPos = self.mapToLogicalCoordinates(event.pos())
            
            # Apply grid snapping if enabled
            if self.snap_to_grid:
                coord = self.snapToGrid(logicalPos)
            else:
                coord = self.getCoordinate(logicalPos)
                
            self.temp_point = coord  # Update temporary point
            self.cursor_position = coord  # Update cursor position

            # Update current shape based on drawing mode
            if self.drawingMode == 'line' and self.points:
                if len(self.points) == 1:
                    self.current_shape = Line(self.points[0], coord, self.lineType, self.lineThickness,
                                         dash_parameters=self.dash_parameters, 
                                         dash_auto_mode=self.dash_auto_mode,
                                         color=self.currentColor)
            elif self.drawingMode == 'circle_center_radius' and self.centerPoint:
                radius = math.hypot(coord.x() - self.centerPoint.x(), coord.y() - self.centerPoint.y())
                self.current_shape = Circle(self.centerPoint, radius, self.lineType, self.lineThickness,
                                       dash_parameters=self.dash_parameters, 
                                       dash_auto_mode=self.dash_auto_mode,
                                       color=self.currentColor)
            elif self.drawingMode == 'rectangle_sides' and self.start_point:
                rect = QRectF(self.start_point, coord).normalized()
                self.current_shape = Rectangle(rect, self.lineType, self.lineThickness,
                                         dash_parameters=self.dash_parameters, 
                                         dash_auto_mode=self.dash_auto_mode,
                                         color=self.currentColor)

            elif self.drawingMode == 'rectangle_center' and self.centerPoint:
                pass  # Handled in paintEvent

            elif self.drawingMode == 'spline_bezier':
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    # Check if dragging a point
                    if self.current_shape.editing_index is not None:
                        # Update position of dragged point
                        self.current_shape.points[self.current_shape.editing_index] = coord
                        self.points = self.current_shape.points  # Update point list
                    
                    # Update highlight for nearest point
                    self.current_shape.highlight_index = self.current_shape.get_closest_point(coord)

            elif self.drawingMode in ['polygon', 'spline_segments']:
                pass  # Handled in paintEvent
            elif self.drawingMode in ['polygon_inscribed', 'polygon_circumscribed'] and self.centerPoint:
                pass  # Handled in paintEvent
            elif self.drawingMode == 'arc_radius_chord' and self.centerPoint and self.radius_point:
                pass  # Handled in paintEvent

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            # End panning
            self.panning = False
            self.setCursor(QCursor(Qt.ArrowCursor))
        elif event.button() == Qt.LeftButton:
            if self.drawingMode == 'spline_bezier':
                if self.current_shape and isinstance(self.current_shape, BezierSpline):
                    self.current_shape.editing_index = None

    # Mouse wheel event handler for zooming
    def wheelEvent(self, event):
        # Calculate zoom center in scene coordinates
        center_pos = self.mapToLogicalCoordinates(event.position().toPoint())
        
        # Old scale
        old_scale = self.scale
        
        # Adjust scale by wheel delta
        delta = event.angleDelta().y() / 120
        self.scale += delta * 0.1
        
        # Limit minimum scale
        if self.scale < 0.1:
            self.scale = 0.1
            
        # Limit maximum scale
        if self.scale > 10.0:
            self.scale = 10.0
        
        # Adjust offset to keep center point under cursor
        if old_scale != self.scale:
            # Calculate the difference in logical coordinates
            scale_factor = self.scale / old_scale
            
            # Convert logical center to screen coordinates
            screen_center = event.position().toPoint()
            
            # Calculate new logical center after scale change
            new_center = self.mapToLogicalCoordinates(screen_center)
            
            # Calculate the offset to maintain the center
            offset_x = (center_pos.x() - new_center.x()) * self.scale
            offset_y = (center_pos.y() - new_center.y()) * self.scale
            
            # Apply offset adjustment (note the y-axis is inverted)
            self.offset += QPoint(offset_x, -offset_y)
        
        self.update()

    # Convert screen coordinates to logical coordinates
    def mapToLogicalCoordinates(self, pos):
        if hasattr(self, 'transform'):
            inverse_transform, ok = self.transform.inverted()
            if ok:
                logical_pos = inverse_transform.map(pos)
                return logical_pos
            else:
                QMessageBox.warning(self, "Error", "Could not invert transformation.")
                return QPointF()
        else:
            return QPointF(pos)

    # Get coordinates based on coordinate system
    def getCoordinate(self, pos):
        if self.coordinateSystem == 'cartesian':
            return pos
        elif self.coordinateSystem == 'polar':
            r = math.hypot(pos.x(), pos.y())
            theta = math.atan2(pos.y(), pos.x())
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            return QPointF(x, y)

    # Calculate regular polygon vertices (inscribed or circumscribed)
    def calculate_regular_polygon(self, center, radius_point, num_sides, mode):
        radius = math.hypot(radius_point.x() - center.x(), radius_point.y() - center.y())
        points = []
        angle_step = 2 * math.pi / num_sides
        start_angle = math.atan2(radius_point.y() - center.y(), radius_point.x() - center.x())
        if mode == 'polygon_inscribed':
            vertex_radius = radius
        elif mode == 'polygon_circumscribed':
            vertex_radius = radius / math.cos(math.pi / num_sides)
        else:
            vertex_radius = radius
        for i in range(num_sides):
            angle = start_angle + i * angle_step
            x = center.x() + vertex_radius * math.cos(angle)
            y = center.y() + vertex_radius * math.sin(angle)
            points.append(QPointF(x, y))
        return points

    def rotate(self, angle):
        self.rotation += angle
        self.update()

    def zoomIn(self):
        self.scale *= 1.1  # Increase scale by 10%
        self.update()

    def zoomOut(self):
        self.scale /= 1.1  # Decrease scale by 10%
        self.update()

    def toggleGrid(self):
        self.show_grid = not self.show_grid
        self.update()

    # Key press handler
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            self.show_grid = not self.show_grid
            self.update()

        if event.key() == Qt.Key_Escape:
            # Cancel current construction
            self.points.clear()
            self.current_shape = None
            self.temp_point = None
            self.centerPoint = None
            self.radius_point = None
            self.start_point = None
            self.numSides = 0
            # Reset spline editing state
            if isinstance(self.current_shape, BezierSpline):
                self.current_shape.is_editing = False
                self.current_shape.editing_index = None
                self.current_shape.highlight_index = None
            self.update()
            if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar.showMessage('Current construction canceled')

        if event.key() == Qt.Key_Z:
            if self.shapes:
                self.shapes.pop()
            self.update()
            if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar.showMessage('Previous construction undone')
            self.zPressed.emit()

        if event.key() == Qt.Key_V:
            self.handle_manual_input()
        #Ctrl + arrows
        elif event.key() == Qt.Key_Right and event.modifiers() & Qt.ControlModifier:
            self.rotation += 5  # Clockwise rotation
            self.update()
            if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar.showMessage('Clockwise rotation')
        elif event.key() == Qt.Key_Left and event.modifiers() & Qt.ControlModifier:
            self.rotation -= 5  # Counter-clockwise rotation
            self.update()
            if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar.showMessage('Counter-clockwise rotation')
        elif event.key() == Qt.Key_M:
            self.show_axes = not self.show_axes  # Toggle axes display
            self.update()
        elif event.key() == Qt.Key_C:
            self.inputCoordinateSystem = 'cartesian'
            QMessageBox.information(self, "Input Coordinate System", "Coordinates will be entered in Cartesian system.")
        elif event.key() == Qt.Key_P:
            self.inputCoordinateSystem = 'polar'
            QMessageBox.information(self, "Input Coordinate System", "Coordinates will be entered in Polar system.")
        elif event.key() == Qt.Key_S:
            self.snap_to_grid = not self.snap_to_grid
            msg = "Grid snapping enabled" if self.snap_to_grid else "Grid snapping disabled"
            if hasattr(self, 'parent') and hasattr(self.parent, 'statusBar'):
                self.parent.statusBar.showMessage(msg)
            self.update()
        else:
            super().keyPressEvent(event)
            
    def _compute_dash_pattern(self):
        """Helper method to create dash line pattern"""
        pattern = []
        if self.lineType == 'dash':
            pattern = [10, 5]
        elif self.lineType == 'dash_dot':
            pattern = [10, 5, 2, 5]
        elif self.lineType == 'dash_dot_dot':
            pattern = [10, 5, 2, 5, 2, 5]
        return pattern
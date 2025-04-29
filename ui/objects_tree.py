from PySide6.QtWidgets import (QDockWidget, QTreeWidget, QTreeWidgetItem, QMenu, 
                            QInputDialog, QMessageBox, QVBoxLayout, QColorDialog,
                            QWidget, QLabel, QPushButton, QHBoxLayout, QFrame, 
                            QScrollArea, QSizePolicy, QToolButton)
from PySide6.QtGui import QAction, QColor, QBrush, QIcon, QPixmap, QPainter, QPen, QFont, QFontMetrics
from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF, QSize, QEvent, QTimer
from PySide6.QtWidgets import QTreeWidgetItemIterator

from core.line import Line
from core.circle import Circle, CircleByThreePoints
from core.arc import ArcByThreePoints, ArcByRadiusChord
from core.polygon import Polygon
from core.rectangle import Rectangle
from core.spline import BezierSpline, SegmentSpline

class ModernToolButton(QToolButton):
    """Custom styled tool button for the tree view"""
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setMinimumHeight(28)

class ObjectTree(QDockWidget):
    """Redesigned tree view for construction objects"""
    def __init__(self, parent, canvas):
        super().__init__("Object Explorer", parent)
        self.parent = parent
        self.canvas = canvas
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setMinimumWidth(280)

        # Create main widget
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(4)
        
        # Create header with title and buttons
        self.createHeader()
        
        # Create search box (placeholder for future implementation)
        # self.createSearchBox()
        
        # Create tree widget
        self.createTreeWidget()
        
        # Connect signals
        self.connectSignals()
        
        # Set widget
        self.setWidget(self.main_widget)
        
        # Initialize styles based on current theme
        is_dark_theme = parent.is_dark_theme if hasattr(parent, 'is_dark_theme') else False
        self.updateThemeStyles(is_dark_theme)
        
        # Update tree
        self.updateConstructionTree()
        
        # Set object name for stylesheet targeting
        self.setObjectName("ObjectTree")

    def createHeader(self):
        """Create header with title and buttons"""
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title_label = QLabel("Object Explorer")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        
        # Spacer to push buttons to the right
        header_layout.addStretch()
        
        # Create button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        
        # Create buttons
        expand_btn = ModernToolButton("Expand All")
        expand_btn.setToolTip("Expand all tree nodes")
        expand_btn.clicked.connect(lambda: self.treeWidget.expandAll())
        
        collapse_btn = ModernToolButton("Collapse All")
        collapse_btn.setToolTip("Collapse all tree nodes")
        collapse_btn.clicked.connect(lambda: self.treeWidget.collapseAll())
        
        # Add buttons to layout
        button_layout.addWidget(expand_btn)
        button_layout.addWidget(collapse_btn)
        
        # Add button container to header
        header_layout.addWidget(button_container)
        
        # Add header to main layout
        self.main_layout.addWidget(header_frame)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setObjectName("HeaderSeparator")
        self.main_layout.addWidget(separator)

    def createTreeWidget(self):
        """Create and configure the tree widget"""
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setFont(QFont("Segoe UI", 10))
        self.treeWidget.setUniformRowHeights(True)
        self.treeWidget.setAnimated(True)
        self.treeWidget.setIndentation(20)
        self.treeWidget.setSelectionMode(QTreeWidget.SingleSelection)
        
        # Add tree widget to main layout
        self.main_layout.addWidget(self.treeWidget)

    def connectSignals(self):
        """Connect signals for tree widget and canvas interaction"""
        self.canvas.shapeAdded.connect(self.updateConstructionTree)
        self.canvas.shapeRemoved.connect(self.updateConstructionTree)
        self.canvas.zPressed.connect(self.updateConstructionTree)
        
        self.treeWidget.itemClicked.connect(self.onTreeItemClicked)
        self.treeWidget.itemDoubleClicked.connect(self.onTreeItemDoubleClicked)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.onTreeContextMenu)

    def updateThemeStyles(self, is_dark_theme):
        """Update styles based on light/dark theme"""
        self.is_dark_theme = is_dark_theme
        
        if is_dark_theme:
            # Dark theme styles
            self.setStyleSheet("""
                QDockWidget {
                    font-family: 'Segoe UI';
                    font-size: 12px;
                    font-weight: bold;
                    color: #f0f0f0;
                    border: none;
                }
                QDockWidget::title {
                    background: #2d2d2d;
                    padding: 8px;
                    border-bottom: 1px solid #3d3d3d;
                }
                
                #ObjectTree #HeaderFrame {
                    background-color: #2d2d2d;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 4px;
                }
                
                #ObjectTree #HeaderSeparator {
                    color: #3d3d3d;
                    background-color: #3d3d3d;
                    height: 1px;
                }
                
                QTreeWidget {
                    background-color: #1e1e1e;
                    alternate-background-color: #252525;
                    color: #f0f0f0;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 4px;
                }
                
                QTreeWidget::item {
                    color: #f0f0f0;
                    padding: 4px 2px;
                    border-bottom: 1px solid #333333;
                    min-height: 24px;
                }
                
                QTreeWidget::item:selected {
                    background-color: #0078d7;
                    color: white;
                    border-radius: 2px;
                }
                
                QTreeWidget::item:hover:!selected {
                    background-color: #3d3d3d;
                    border-radius: 2px;
                }
                
                QToolButton {
                    background-color: #3a3a3a;
                    color: #f0f0f0;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 2px;
                }
                
                QToolButton:hover {
                    background-color: #444444;
                    border-color: #666666;
                }
                
                QToolButton:pressed {
                    background-color: #0078d7;
                    color: white;
                }
                
                QMenu {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 2px;
                }
                
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #f0f0f0;
                }
                
                QMenu::item:selected {
                    background-color: #0078d7;
                    color: white;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #3d3d3d;
                    margin: 4px 10px;
                }
            """)
        else:
            # Light theme styles
            self.setStyleSheet("""
                QDockWidget {
                    font-family: 'Segoe UI';
                    font-size: 12px;
                    font-weight: bold;
                    color: #333333;
                    border: none;
                }
                QDockWidget::title {
                    background: #f0f0f0;
                    padding: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                #ObjectTree #HeaderFrame {
                    background-color: #f5f5f5;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 4px;
                }
                
                #ObjectTree #HeaderSeparator {
                    color: #e0e0e0;
                    background-color: #e0e0e0;
                    height: 1px;
                }
                
                QTreeWidget {
                    background-color: white;
                    alternate-background-color: #f8f8f8;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 4px;
                }
                
                QTreeWidget::item {
                    color: #333333;
                    padding: 4px 2px;
                    border-bottom: 1px solid #f0f0f0;
                    min-height: 24px;
                }
                
                QTreeWidget::item:selected {
                    background-color: #0078d7;
                    color: white;
                    border-radius: 2px;
                }
                
                QTreeWidget::item:hover:!selected {
                    background-color: #f0f0f0;
                    border-radius: 2px;
                }
                
                QToolButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    margin: 2px;
                }
                
                QToolButton:hover {
                    background-color: #e8e8e8;
                    border-color: #c0c0c0;
                }
                
                QToolButton:pressed {
                    background-color: #0078d7;
                    color: white;
                }
                
                QMenu {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 2px;
                }
                
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #333333;
                }
                
                QMenu::item:selected {
                    background-color: #0078d7;
                    color: white;
                }
                
                QMenu::separator {
                    height: 1px;
                    background-color: #e0e0e0;
                    margin: 4px 10px;
                }
            """)

    def saveExpandState(self):
        """Save expanded state of tree items"""
        expanded_states = {}
        
        # First save states of existing items
        iterator = QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            expanded_states[item.text(0)] = item.isExpanded()
            iterator += 1
        return expanded_states

    def restoreExpandState(self, expanded_states):
        """Restore expanded state of tree items"""
        if not expanded_states:  # If no saved states
            return
            
        iterator = QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            # If item existed previously, restore its state
            if item.text(0) in expanded_states:
                item.setExpanded(expanded_states[item.text(0)])
            else:
                # Keep new items collapsed
                item.setExpanded(False)
            iterator += 1

    def updateConstructionTree(self):
        """Update tree with current shapes"""
        # Save expanded states
        expanded_states = self.saveExpandState()

        self.treeWidget.clear()
        
        # Dictionary of English-to-display name mappings
        shape_names = {
            'Line': 'Line',
            'Circle': 'Circle',
            'Rectangle': 'Rectangle',
            'Polygon': 'Polygon',
            'CircleByThreePoints': 'Circle by 3 Points',
            'ArcByThreePoints': 'Arc by 3 Points',
            'ArcByRadiusChord': 'Arc by Radius-Chord',
            'BezierSpline': 'Bezier Curve',
            'SegmentSpline': 'Segment Curve'
        }

        # Dictionary of colors for different shape types
        shape_colors = {
            'Line': '#0078d7',           # Blue
            'Circle': '#107c41',         # Green
            'Rectangle': '#d83b01',      # Orange
            'Polygon': '#8764b8',        # Purple
            'CircleByThreePoints': '#107c41',  # Green
            'ArcByThreePoints': '#e74856',     # Red
            'ArcByRadiusChord': '#e74856',     # Red
            'BezierSpline': '#8764b8',         # Purple
            'SegmentSpline': '#8764b8'         # Purple
        }
        
        # Dictionary for line type display names
        line_type_names = {
            'solid': 'Solid',
            'dash': 'Dashed',
            'dash_dot': 'Dash-Dot',
            'dash_dot_dot': 'Dash-Dot-Dot'
        }
        
        # Check current theme
        is_dark_theme = self.is_dark_theme
        
        # Add shapes to tree
        for index, shape in enumerate(self.canvas.shapes):
            shape_type = type(shape).__name__
            # Use display name from dictionary
            shape_name = shape_names.get(shape_type, shape_type)
            item_text = f"{index + 1}: {shape_name}"
            
            # Create main item
            tree_item = QTreeWidgetItem([item_text])
            tree_item.setData(0, Qt.UserRole, {'index': index})
            
            # Set color and style for item
            color = QColor(shape_colors.get(shape_type, '#757575'))
            
            # Set text color based on theme
            if is_dark_theme:
                tree_item.setForeground(0, QColor('#f0f0f0'))  # White text for dark theme
                # Create color indicator in the text
                tree_item.setIcon(0, self.createColorIcon(color, is_dark_theme))
            else:
                tree_item.setForeground(0, QColor('#333333'))  # Dark text for light theme
                # Create color indicator in the text
                tree_item.setIcon(0, self.createColorIcon(color, is_dark_theme))
                
            font = QFont("Segoe UI", 10, QFont.Bold)
            tree_item.setFont(0, font)
            
            # Highlight selected item
            if index == self.canvas.highlighted_shape_index:
                self.treeWidget.setCurrentItem(tree_item)
            
            self.treeWidget.addTopLevelItem(tree_item)

            # Function to create child item with formatting
            def create_child_item(parent, text, index=None, property_name=None, is_editable=True):
                item = QTreeWidgetItem([text])
                if is_editable and index is not None:
                    item.setData(0, Qt.UserRole, {'index': index, 'property': property_name})
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                parent.addChild(item)
                # Set normal font for child items
                item.setFont(0, QFont("Segoe UI", 9))
                if is_dark_theme:
                    item.setForeground(0, QColor('#f0f0f0'))  # White text for dark theme
                return item
            
            # Add line style information
            if hasattr(shape, 'line_type'):
                line_type_text = line_type_names.get(shape.line_type, shape.line_type)
                style_item = create_child_item(tree_item,
                    f"Style: {line_type_text}",
                    index, 'line_type')
                
                # Add style icon
                style_item.setIcon(0, self.createLineStyleIcon(shape.line_type, is_dark_theme))
            
            # Add line thickness information
            if hasattr(shape, 'line_thickness'):
                create_child_item(tree_item,
                    f"Thickness: {shape.line_thickness:.2f}",
                    index, 'line_thickness')
            
            # Add line color information
            if hasattr(shape, 'color') and shape.color:
                color_item = create_child_item(tree_item,
                    f"Color: {shape.color.name()}",
                    index, 'color')
                
                # Create color indicator
                color_item.setIcon(0, self.createColorIcon(shape.color, is_dark_theme))
                
                # If color is dark, make text white
                if shape.color.red() + shape.color.green() + shape.color.blue() < 380:
                    color_item.setForeground(0, QColor(255, 255, 255))

            # Add information based on shape type
            if isinstance(shape, Line):
                create_child_item(tree_item, 
                    f"Start: ({shape.start_point.x():.2f}, {shape.start_point.y():.2f})",
                    index, 'start_point')
                create_child_item(tree_item,
                    f"End: ({shape.end_point.x():.2f}, {shape.end_point.y():.2f})",
                    index, 'end_point')
                create_child_item(tree_item,
                    f"Length: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, Circle):
                create_child_item(tree_item,
                    f"Center: ({shape.center.x():.2f}, {shape.center.y():.2f})",
                    index, 'center')
                create_child_item(tree_item,
                    f"Radius: {shape.radius:.2f}",
                    index, 'radius')
                create_child_item(tree_item,
                    f"Circumference: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, Rectangle):
                rect = shape.rect
                topLeft = rect.topLeft()
                create_child_item(tree_item,
                    f"Top-left: ({topLeft.x():.2f}, {topLeft.y():.2f})",
                    index, 'top_left')
                create_child_item(tree_item,
                    f"Width: {rect.width():.2f}",
                    index, 'width')
                create_child_item(tree_item,
                    f"Height: {rect.height():.2f}",
                    index, 'height')
                create_child_item(tree_item,
                    f"Perimeter: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, Polygon):
                for i, p in enumerate(shape.points):
                    create_child_item(tree_item,
                        f"Vertex {i + 1}: ({p.x():.2f}, {p.y():.2f})",
                        index, f'point_{i}')
                create_child_item(tree_item,
                    f"Perimeter: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, CircleByThreePoints):
                for i, p in enumerate(shape.points):
                    create_child_item(tree_item,
                        f"Point {i + 1}: ({p.x():.2f}, {p.y():.2f})",
                        index, f'point_{i}')
                create_child_item(tree_item,
                    f"Circumference: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, ArcByThreePoints):
                for i, p in enumerate(shape.points):
                    create_child_item(tree_item,
                        f"Point {i + 1}: ({p.x():.2f}, {p.y():.2f})",
                        index, f'point_{i}')
                create_child_item(tree_item,
                    f"Arc Length: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, ArcByRadiusChord):
                create_child_item(tree_item,
                    f"Center: ({shape.center.x():.2f}, {shape.center.y():.2f})",
                    index, 'center')
                create_child_item(tree_item,
                    f"Radius Point: ({shape.radius_point.x():.2f}, {shape.radius_point.y():.2f})",
                    index, 'radius_point')
                create_child_item(tree_item,
                    f"Chord Point: ({shape.chord_point.x():.2f}, {shape.chord_point.y():.2f})",
                    index, 'chord_point')
                create_child_item(tree_item,
                    f"Arc Length: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, BezierSpline):
                for i, p in enumerate(shape.points):
                    create_child_item(tree_item,
                        f"Control Point {i + 1}: ({p.x():.2f}, {p.y():.2f})",
                        index, f'control_point_{i}')
                create_child_item(tree_item,
                    f"Curve Length: {shape.get_total_length():.2f}",
                    is_editable=False)

            elif isinstance(shape, SegmentSpline):
                for i, p in enumerate(shape.points):
                    create_child_item(tree_item,
                        f"Point {i + 1}: ({p.x():.2f}, {p.y():.2f})",
                        index, f'point_{i}')
                create_child_item(tree_item,
                    f"Curve Length: {shape.get_total_length():.2f}",
                    is_editable=False)

            else:
                create_child_item(tree_item, "No additional information", is_editable=False)

        # Restore item states
        if len(self.canvas.shapes) == 1 and not expanded_states:
            # If first element, expand all
            self.treeWidget.expandAll()
        else:
            # Otherwise restore saved state
            self.restoreExpandState(expanded_states)

    def createColorIcon(self, color, is_dark_theme):
        """Create a small color icon for tree items"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw color circle
        painter.setPen(QPen(QColor('#808080' if is_dark_theme else '#d0d0d0'), 1))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(2, 2, 12, 12)
        
        painter.end()
        return QIcon(pixmap)

    def createLineStyleIcon(self, line_type, is_dark_theme):
        """Create an icon representing line style"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set pen color based on theme
        pen_color = QColor('#f0f0f0' if is_dark_theme else '#333333')
        
        # Set pen style based on line type
        if line_type == 'solid':
            pen = QPen(pen_color, 2, Qt.SolidLine)
        elif line_type == 'dash':
            pen = QPen(pen_color, 2, Qt.DashLine)
        elif line_type == 'dash_dot':
            pen = QPen(pen_color, 2, Qt.DashDotLine)
        elif line_type == 'dash_dot_dot':
            pen = QPen(pen_color, 2, Qt.DashDotDotLine)
        else:
            pen = QPen(pen_color, 2, Qt.SolidLine)
        
        painter.setPen(pen)
        painter.drawLine(2, 8, 14, 8)
        
        painter.end()
        return QIcon(pixmap)

    def onTreeItemClicked(self, item):
        """Handle tree item click"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            # Check index is within shape list
            if 0 <= index < len(self.canvas.shapes):
                # Set highlighted shape index
                self.canvas.highlighted_shape_index = index
                # Force canvas redraw
                self.canvas.repaint()
                
                # Update status bar
                shape = self.canvas.shapes[index]
                shape_type = type(shape).__name__
                # Dictionary for English-to-display name mapping
                shape_names = {
                    'Line': 'Line',
                    'Circle': 'Circle',
                    'Rectangle': 'Rectangle',
                    'Polygon': 'Polygon',
                    'CircleByThreePoints': 'Circle by 3 Points',
                    'ArcByThreePoints': 'Arc by 3 Points',
                    'ArcByRadiusChord': 'Arc by Radius-Chord',
                    'BezierSpline': 'Bezier Curve',
                    'SegmentSpline': 'Segment Curve'
                }
                shape_name = shape_names.get(shape_type, shape_type)
                message = f"Selected: {index + 1}: {shape_name}"
                if hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar.showMessage(message)

    def onTreeItemDoubleClicked(self, item, column):
        """Handle tree item double click"""
        data = item.data(0, Qt.UserRole)
        if data is not None:
            index = data.get('index')
            property_name = data.get('property')
            if index is not None and property_name is not None:
                if 0 <= index < len(self.canvas.shapes):
                    shape = self.canvas.shapes[index]
                    self.editShapeProperty(shape, property_name)
                    self.canvas.update()
                    self.updateConstructionTree()

    def onTreeContextMenu(self, position):
        """Show context menu for tree items"""
        item = self.treeWidget.itemAt(position)
        if item:
            data = item.data(0, Qt.UserRole)
            if data is not None and 'index' in data and 'property' not in data:
                menu = QMenu()
                
                # Add main actions
                edit_action = QAction('Edit Properties', self)
                edit_action.triggered.connect(lambda checked=False, i=item: self.editShape(i))
                
                delete_action = QAction('Delete', self)
                delete_action.triggered.connect(lambda checked=False, i=item: self.deleteShape(i))
                
                # Add transform actions
                transform_menu = QMenu('Transform', self)
                
                rotate_action = QAction('Rotate', self)
                rotate_action.triggered.connect(lambda checked=False, i=item: self.rotateShape(i))
                transform_menu.addAction(rotate_action)
                
                # Add style actions
                style_menu = QMenu('Style', self)
                
                color_action = QAction('Change Color', self)
                color_action.triggered.connect(lambda checked=False, i=item: self.changeShapeColor(i))
                style_menu.addAction(color_action)
                
                thickness_action = QAction('Change Thickness', self)
                thickness_action.triggered.connect(lambda checked=False, i=item: self.changeShapeThickness(i))
                style_menu.addAction(thickness_action)
                
                line_type_menu = QMenu('Line Type', self)
                
                # Add line type options
                for line_type, label in {'solid': 'Solid', 'dash': 'Dashed', 
                                        'dash_dot': 'Dash-Dot', 'dash_dot_dot': 'Dash-Dot-Dot'}.items():
                    line_action = QAction(label, self)
                    line_action.triggered.connect(
                        lambda checked=False, i=item, lt=line_type: self.changeLineType(i, lt))
                    line_type_menu.addAction(line_action)
                
                style_menu.addMenu(line_type_menu)
                
                # Add all actions to menu
                menu.addAction(edit_action)
                menu.addAction(delete_action)
                menu.addSeparator()
                menu.addMenu(transform_menu)
                menu.addMenu(style_menu)
                
                menu.exec(self.treeWidget.viewport().mapToGlobal(position))

    def changeLineType(self, item, line_type):
        """Change shape line type"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                shape = self.canvas.shapes[index]
                if hasattr(shape, 'line_type'):
                    shape.line_type = line_type
                    self.canvas.update()
                    self.updateConstructionTree()

    def changeShapeColor(self, item):
        """Change shape color"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                shape = self.canvas.shapes[index]
                
                # Use modern color dialog
                if hasattr(shape, 'color') and shape.color:
                    current_color = shape.color
                    color = QColorDialog.getColor(current_color, self, "Select Color")
                    
                    if color.isValid():
                        shape.color = color
                        self.canvas.update()
                        self.updateConstructionTree()

    def changeShapeThickness(self, item):
        """Change shape line thickness"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                shape = self.canvas.shapes[index]
                
                if hasattr(shape, 'line_thickness'):
                    thickness, ok = QInputDialog.getDouble(
                        self, 
                        "Line Thickness", 
                        "Enter line thickness:", 
                        shape.line_thickness, 
                        0.1, 10.0, 1
                    )
                    
                    if ok:
                        shape.line_thickness = thickness
                        self.canvas.update()
                        self.updateConstructionTree()

    def rotateShape(self, item):
        """Rotate selected shape"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                shape = self.canvas.shapes[index]
                
                # Request rotation angle
                angle, ok = QInputDialog.getDouble(
                    self, 
                    "Rotate Shape",
                    "Enter rotation angle in degrees\n(positive = counter-clockwise):",
                    0,  # value
                    -360,  # minValue
                    360,   # maxValue
                    1      # decimals
                )
                if not ok:
                    return
                    
                # Determine rotation center
                if hasattr(shape, 'center'):
                    center = shape.center
                elif hasattr(shape, 'points') and shape.points:
                    # For polygons and splines use center of mass
                    x_sum = sum(p.x() for p in shape.points)
                    y_sum = sum(p.y() for p in shape.points)
                    center = QPointF(x_sum / len(shape.points), y_sum / len(shape.points))
                elif hasattr(shape, 'start_point') and hasattr(shape, 'end_point'):
                    # For lines use midpoint
                    center = QPointF(
                        (shape.start_point.x() + shape.end_point.x()) / 2,
                        (shape.start_point.y() + shape.end_point.y()) / 2
                    )
                elif hasattr(shape, 'rect'):
                    # For rectangles use center
                    center = shape.rect.center()
                else:
                    return
                    
                # Perform rotation
                shape.rotate_around_point(angle, center)
                self.canvas.update()  # Ensure canvas redraw
                self.updateConstructionTree()  # Update tree

    def editShape(self, item):
        """Edit shape properties"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                shape = self.canvas.shapes[index]
                # First, allow editing general properties
                self.editGeneralShapeProperties(shape)
                # Then call specific editing method
                if isinstance(shape, Line):
                    self.editLineShape(shape)
                elif isinstance(shape, Circle):
                    self.editCircleShape(shape)
                elif isinstance(shape, Rectangle):
                    self.editRectangleShape(shape)
                elif isinstance(shape, Polygon):
                    self.editPolygonShape(shape)
                elif isinstance(shape, CircleByThreePoints):
                    self.editCircleByThreePointsShape(shape)
                elif isinstance(shape, ArcByThreePoints):
                    self.editArcByThreePointsShape(shape)
                elif isinstance(shape, ArcByRadiusChord):
                    self.editArcByRadiusChordShape(shape)
                elif isinstance(shape, BezierSpline):
                    self.editBezierSplineShape(shape)
                elif isinstance(shape, SegmentSpline):
                    self.editSegmentSplineShape(shape)
                else:
                    QMessageBox.information(self, "Edit", "Editing this shape type is not supported.")
                # Update canvas and tree
                self.canvas.update()
                self.updateConstructionTree()

    def deleteShape(self, item):
        """Delete selected shape"""
        data = item.data(0, Qt.UserRole)
        if data is not None and 'index' in data:
            index = data['index']
            if 0 <= index < len(self.canvas.shapes):
                item_text = item.text(0)  # Save item text
                
                # Ask for confirmation
                confirm = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    f"Are you sure you want to delete {item_text}?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if confirm == QMessageBox.Yes:
                    del self.canvas.shapes[index]
                    self.canvas.highlighted_shape_index = None
                    self.canvas.shapeRemoved.emit()
                    self.canvas.update()
                    self.parent.statusBar.showMessage(f"Deleted: {item_text}")

    def editGeneralShapeProperties(self, shape):
        """Edit general shape properties like line type and thickness"""
        # Edit line type
        line_types = ['Solid', 'Dashed', 'Dash-Dot', 'Dash-Dot-Dot']
        line_type_keys = ['solid', 'dash', 'dash_dot', 'dash_dot_dot']
        current_line_type_index = line_type_keys.index(shape.line_type)
        line_type, ok = QInputDialog.getItem(self, "Line Type", "Select line type:", line_types, current_line_type_index, False)
        if ok and line_type:
            shape.line_type = line_type_keys[line_types.index(line_type)]

        thickness, ok = QInputDialog.getDouble(self, "Line Thickness", "Enter line thickness:", shape.line_thickness, 0.1, 10.0)
        if ok:
            shape.line_thickness = thickness

    def editShapeProperty(self, shape, property_name):
        """Edit a specific property of a shape"""
        if property_name == 'line_type':
            line_types = ['Solid', 'Dashed', 'Dash-Dot', 'Dash-Dot-Dot']
            line_type_keys = ['solid', 'dash', 'dash_dot', 'dash_dot_dot']
            current_line_type_index = line_type_keys.index(shape.line_type)
            line_type, ok = QInputDialog.getItem(self, "Line Type", "Select line type:", line_types, current_line_type_index, False)
            if ok and line_type:
                shape.line_type = line_type_keys[line_types.index(line_type)]
        
        elif property_name == 'line_thickness':
            thickness, ok = QInputDialog.getDouble(self, "Line Thickness", "Enter line thickness:", shape.line_thickness, 0.1, 10.0)
            if ok:
                shape.line_thickness = thickness
        
        elif property_name == 'color':
            # Use color dialog
            if hasattr(shape, 'color') and shape.color:
                color = QColorDialog.getColor(shape.color, self, "Select Color")
                if color.isValid():
                    shape.color = color
        
        elif isinstance(shape, Line):
            self.editLineShapeProperty(shape, property_name)
        elif isinstance(shape, Circle):
            self.editCircleShapeProperty(shape, property_name)
        elif isinstance(shape, Rectangle):
            self.editRectangleShapeProperty(shape, property_name)
        elif isinstance(shape, Polygon):
            self.editPolygonShapeProperty(shape, property_name)
        elif isinstance(shape, CircleByThreePoints):
            self.editCircleByThreePointsShapeProperty(shape, property_name)
        elif isinstance(shape, ArcByThreePoints):
            self.editArcByThreePointsShapeProperty(shape, property_name)
        elif isinstance(shape, ArcByRadiusChord):
            self.editArcByRadiusChordShapeProperty(shape, property_name)
        elif isinstance(shape, BezierSpline):
            self.editBezierSplineShapeProperty(shape, property_name)
        elif isinstance(shape, SegmentSpline):
            self.editSegmentSplineShapeProperty(shape, property_name)
        else:
            QMessageBox.information(self, "Edit", "Editing this property is not supported.")

    # Line properties
    def editLineShapeProperty(self, shape, property_name):
        if property_name == 'start_point':
            x, ok1 = QInputDialog.getDouble(self, "Edit Line Start", "Start X:", value=shape.start_point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, "Edit Line Start", "Start Y:", value=shape.start_point.y())
            if not ok2:
                return
            shape.start_point = QPointF(x, y)
        elif property_name == 'end_point':
            x, ok1 = QInputDialog.getDouble(self, "Edit Line End", "End X:", value=shape.end_point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, "Edit Line End", "End Y:", value=shape.end_point.y())
            if not ok2:
                return
            shape.end_point = QPointF(x, y)

    # Circle properties
    def editCircleShapeProperty(self, shape, property_name):
        if property_name == 'center':
            x, ok1 = QInputDialog.getDouble(self, "Edit Circle Center", "Center X:", value=shape.center.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, "Edit Circle Center", "Center Y:", value=shape.center.y())
            if not ok2:
                return
            shape.center = QPointF(x, y)
        elif property_name == 'radius':
            radius, ok = QInputDialog.getDouble(self, "Edit Parameters", "Enter radius:", shape.radius, 0.1, 1000.0, 1)
            if not ok:
                return
            shape.radius = radius

    # Rectangle properties
    def editRectangleShapeProperty(self, shape, property_name):
        rect = shape.rect
        if property_name == 'top_left':
            x, ok1 = QInputDialog.getDouble(self, "Edit Rectangle", "Top-left X:", value=rect.topLeft().x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, "Edit Rectangle", "Top-left Y:", value=rect.topLeft().y())
            if not ok2:
                return
            rect.moveTopLeft(QPointF(x, y))
            shape.rect = rect
        elif property_name == 'width':
            width, ok = QInputDialog.getDouble(self, "Edit Rectangle", "Width:", value=rect.width())
            if not ok:
                return
            rect.setWidth(width)
            shape.rect = rect
        elif property_name == 'height':
            height, ok = QInputDialog.getDouble(self, "Edit Rectangle", "Height:", value=rect.height())
            if not ok:
                return
            rect.setHeight(height)
            shape.rect = rect

    # Polygon properties
    def editPolygonShapeProperty(self, shape, property_name):
        if property_name.startswith('point_'):
            try:
                point_index = int(property_name.split('_')[1])
            except ValueError:
                return
            if 0 <= point_index < len(shape.points):
                point = shape.points[point_index]
                x, ok1 = QInputDialog.getDouble(
                    self, f"Edit Vertex {point_index + 1}", "X:", value=point.x())
                if not ok1:
                    return
                y, ok2 = QInputDialog.getDouble(
                    self, f"Edit Vertex {point_index + 1}", "Y:", value=point.y())
                if not ok2:
                    return
                shape.points[point_index] = QPointF(x, y)

    # CircleByThreePoints properties
    def editCircleByThreePointsShapeProperty(self, shape, property_name):
        if property_name.startswith('point_'):
            try:
                point_index = int(property_name.split('_')[1])
            except ValueError:
                return
            if 0 <= point_index < 3:
                point = shape.points[point_index]
                x, ok1 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "X:", value=point.x())
                if not ok1:
                    return
                y, ok2 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "Y:", value=point.y())
                if not ok2:
                    return
                shape.points[point_index] = QPointF(x, y)

    # ArcByThreePoints properties
    def editArcByThreePointsShapeProperty(self, shape, property_name):
        if property_name.startswith('point_'):
            try:
                point_index = int(property_name.split('_')[1])
            except ValueError:
                return
            if 0 <= point_index < 3:
                point = shape.points[point_index]
                x, ok1 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "X:", value=point.x())
                if not ok1:
                    return
                y, ok2 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "Y:", value=point.y())
                if not ok2:
                    return
                shape.points[point_index] = QPointF(x, y)

    # ArcByRadiusChord properties
    def editArcByRadiusChordShapeProperty(self, shape, property_name):
        if property_name == 'center':
            x, ok1 = QInputDialog.getDouble(
                self, "Edit Arc Center", "Center X:", value=shape.center.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(
                self, "Edit Arc Center", "Center Y:", value=shape.center.y())
            if not ok2:
                return
            shape.center = QPointF(x, y)
        elif property_name == 'radius_point':
            x, ok1 = QInputDialog.getDouble(
                self, "Edit Radius Point", "X:", value=shape.radius_point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(
                self, "Edit Radius Point", "Y:", value=shape.radius_point.y())
            if not ok2:
                return
            shape.radius_point = QPointF(x, y)
        elif property_name == 'chord_point':
            x, ok1 = QInputDialog.getDouble(
                self, "Edit Chord Point", "X:", value=shape.chord_point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(
                self, "Edit Chord Point", "Y:", value=shape.chord_point.y())
            if not ok2:
                return
            shape.chord_point = QPointF(x, y)

    # BezierSpline properties
    def editBezierSplineShapeProperty(self, shape, property_name):
        if property_name.startswith('control_point_'):
            try:
                point_index = int(property_name.split('_')[2])
            except ValueError:
                return
            if 0 <= point_index < len(shape.points):
                point = shape.points[point_index]
                x, ok1 = QInputDialog.getDouble(
                    self, f"Edit Control Point {point_index + 1}", "X:", value=point.x())
                if not ok1:
                    return
                y, ok2 = QInputDialog.getDouble(
                    self, f"Edit Control Point {point_index + 1}", "Y:", value=point.y())
                if not ok2:
                    return
                shape.points[point_index] = QPointF(x, y)

    # SegmentSpline properties
    def editSegmentSplineShapeProperty(self, shape, property_name):
        if property_name.startswith('point_'):
            try:
                point_index = int(property_name.split('_')[1])
            except ValueError:
                return
            if 0 <= point_index < len(shape.points):
                point = shape.points[point_index]
                x, ok1 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "X:", value=point.x())
                if not ok1:
                    return
                y, ok2 = QInputDialog.getDouble(
                    self, f"Edit Point {point_index + 1}", "Y:", value=point.y())
                if not ok2:
                    return
                shape.points[point_index] = QPointF(x, y)

    # Implement editShape methods for shape-specific editing
    def editLineShape(self, shape):
        # Edit start point
        start_x, ok1 = QInputDialog.getDouble(self, "Edit Line", "Start X:", value=shape.start_point.x())
        if not ok1:
            return
        start_y, ok2 = QInputDialog.getDouble(self, "Edit Line", "Start Y:", value=shape.start_point.y())
        if not ok2:
            return
        # Edit end point
        end_x, ok3 = QInputDialog.getDouble(self, "Edit Line", "End X:", value=shape.end_point.x())
        if not ok3:
            return
        end_y, ok4 = QInputDialog.getDouble(self, "Edit Line", "End Y:", value=shape.end_point.y())
        if not ok4:
            return
        # Update shape
        shape.start_point = QPointF(start_x, start_y)
        shape.end_point = QPointF(end_x, end_y)

    def editCircleShape(self, shape):
        center_x, ok1 = QInputDialog.getDouble(self, "Edit Circle", "Center X:", value=shape.center.x())
        if not ok1:
            return
        center_y, ok2 = QInputDialog.getDouble(self, "Edit Circle", "Center Y:", value=shape.center.y())
        if not ok2:
            return
        radius, ok3 = QInputDialog.getDouble(self, "Edit Circle", "Radius:", value=shape.radius, minValue=0.1)
        if not ok3:
            return
        # Update shape
        shape.center = QPointF(center_x, center_y)
        shape.radius = radius

    def editRectangleShape(self, shape):
        rect = shape.rect
        top_left_x, ok1 = QInputDialog.getDouble(self, "Edit Rectangle", "Top-left X:", value=rect.topLeft().x())
        if not ok1:
            return
        top_left_y, ok2 = QInputDialog.getDouble(self, "Edit Rectangle", "Top-left Y:", value=rect.topLeft().y())
        if not ok2:
            return
        width, ok3 = QInputDialog.getDouble(self, "Edit Rectangle", "Width:", value=rect.width(), minValue=0.1)
        if not ok3:
            return
        height, ok4 = QInputDialog.getDouble(self, "Edit Rectangle", "Height:", value=rect.height(), minValue=0.1)
        if not ok4:
            return
        # Update rect
        shape.rect = QRectF(QPointF(top_left_x, top_left_y), QSizeF(width, height))

    def editPolygonShape(self, shape):
        for i in range(len(shape.points)):
            point = shape.points[i]
            coord_str = f"{point.x():.2f} {point.y():.2f}"
            coord_input, ok = QInputDialog.getText(self, "Edit Polygon", f"Vertex {i+1} (X Y):", text=coord_str)
            if not ok:
                return
            try:
                x_str, y_str = coord_input.strip().split()
                x = float(x_str)
                y = float(y_str)
                shape.points[i] = QPointF(x, y)
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Invalid input. Please enter two numbers separated by space.")
                return

    def editCircleByThreePointsShape(self, shape):
        # Allow editing all three points
        for i in range(3):
            point = shape.points[i]
            x, ok1 = QInputDialog.getDouble(self, f"Edit Point {i + 1}", "X:", value=point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, f"Edit Point {i + 1}", "Y:", value=point.y())
            if not ok2:
                return
            shape.points[i] = QPointF(x, y)

    def editArcByThreePointsShape(self, shape):
        # Allow editing all three points
        for i in range(3):
            point = shape.points[i]
            x, ok1 = QInputDialog.getDouble(self, f"Edit Point {i + 1}", "X:", value=point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(self, f"Edit Point {i + 1}", "Y:", value=point.y())
            if not ok2:
                return
            shape.points[i] = QPointF(x, y)

    def editArcByRadiusChordShape(self, shape):
        # Allow editing center, radius_point, and chord_point
        self.editArcByRadiusChordShapeProperty(shape, 'center')
        self.editArcByRadiusChordShapeProperty(shape, 'radius_point')
        self.editArcByRadiusChordShapeProperty(shape, 'chord_point')

    def editBezierSplineShape(self, shape):
        # Allow editing all control points
        for i in range(len(shape.points)):
            point = shape.points[i]
            x, ok1 = QInputDialog.getDouble(
                self, f"Edit Control Point {i + 1}", "X:", value=point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(
                self, f"Edit Control Point {i + 1}", "Y:", value=point.y())
            if not ok2:
                return
            shape.points[i] = QPointF(x, y)

    def editSegmentSplineShape(self, shape):
        # Allow editing all points
        for i in range(len(shape.points)):
            point = shape.points[i]
            x, ok1 = QInputDialog.getDouble(
                self, f"Edit Point {i + 1}", "X:", value=point.x())
            if not ok1:
                return
            y, ok2 = QInputDialog.getDouble(
                self, f"Edit Point {i + 1}", "Y:", value=point.y())
            if not ok2:
                return
            shape.points[i] = QPointF(x, y)
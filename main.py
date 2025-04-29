import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QInputDialog, QStatusBar, QDockWidget, 
                             QMessageBox, QFileDialog, QLabel, QToolBar, QStyle, QMenu,
                             QComboBox, QSpinBox, QColorDialog, QHBoxLayout, QWidget, QPushButton)
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QImage, QPainter, QBrush, QLinearGradient
from PySide6.QtCore import Qt, QSize, QPoint, QRect
from ui.canvas import Canvas
from ui.objects_tree import ObjectTree
from dxf_handler import save_to_dxf_advanced, read_from_dxf

# Constants for string values
COORD_SYSTEMS = {'cartesian': 'Cartesian', 'polar': 'Polar'}
LINE_TYPES = {'solid': 'Solid', 'dash': 'Dashed', 'dash_dot': 'Dash-Dot', 'dash_dot_dot': 'Dash-Dot-Dot'}
DRAWING_MODES = {
    'line': 'Line',
    'circle_center_radius': 'Circle: Center-Radius',
    'circle_three_points': 'Circle: 3 Points',
    'arc_three_points': 'Arc: 3 Points',
    'arc_radius_chord': 'Arc: Radius-Chord',
    'polygon': 'Polygon: Freeform',
    'polygon_inscribed': 'Polygon: Inscribed',
    'polygon_circumscribed': 'Polygon: Circumscribed',
    'rectangle_sides': 'Rectangle: By Sides',
    'rectangle_center': 'Rectangle: From Center',
    'spline_bezier': 'Spline: Bezier',
    'spline_segments': 'Spline: Segmented'
}

GROUPED_DRAWING_MODES = {
    "Arc": ['arc_three_points', 'arc_radius_chord'],
    "Circle": ['circle_center_radius', 'circle_three_points'],
    "Rectangle": ['rectangle_sides', 'rectangle_center'],
    "Polygon": ['polygon', 'polygon_inscribed', 'polygon_circumscribed'],
    "Spline": ['spline_bezier', 'spline_segments']
}

class ModernButton(QPushButton):
    """Custom button with modern styling"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self.setMinimumWidth(100)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Button state
        is_down = self.isDown()
        is_hover = self.underMouse()
        is_enabled = self.isEnabled()
        
        # Base colors
        if not is_enabled:
            bg_color = QColor(220, 220, 220)
            text_color = QColor(150, 150, 150)
        elif is_down:
            bg_color = QColor(42, 130, 218)
            text_color = QColor(255, 255, 255)
        elif is_hover:
            bg_color = QColor(70, 150, 230)
            text_color = QColor(255, 255, 255)
        else:
            bg_color = QColor(65, 125, 185)
            text_color = QColor(255, 255, 255)
        
        # Draw rounded rectangle
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 6, 6)
        
        # Draw text
        painter.setPen(QColor(40, 40, 40))
        painter.drawText(rect, Qt.AlignCenter, self.text())
        
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueprint Studio")
        self.setGeometry(100, 100, 1600, 1000)
        self.is_dark_theme = True  # Dark theme by default
        self.current_file = None  # Track the current file
        self.initUI()
        
    def initUI(self):
        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.createToolBar()
        # self.createMenus()
        self.createStatusBar()
        self.createConstructionTree()
        self.applyTheme()
        self.menuBar().setVisible(False)

    def createToolBar(self):
        # Main toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        
        # File actions
        new_action = QAction("New", self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.newFile)
        self.toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.openDxfFile)
        self.toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.saveFile)
        self.toolbar.addAction(save_action)
        
        self.toolbar.addSeparator()
        
        # Drawing mode selector
        drawing_mode_label = QLabel("Mode: ")
        self.toolbar.addWidget(drawing_mode_label)
        
        self.drawing_mode_combo = QComboBox()
        for mode, label in DRAWING_MODES.items():
            self.drawing_mode_combo.addItem(label, mode)
        self.drawing_mode_combo.currentIndexChanged.connect(self.onDrawingModeChanged)
        self.toolbar.addWidget(self.drawing_mode_combo)
        
        self.toolbar.addSeparator()
        
        # Line type selector
        line_type_label = QLabel("Line Type: ")
        self.toolbar.addWidget(line_type_label)
        
        self.line_type_combo = QComboBox()
        for line_type, label in LINE_TYPES.items():
            self.line_type_combo.addItem(label, line_type)
        self.line_type_combo.currentIndexChanged.connect(self.onLineTypeChanged)
        self.toolbar.addWidget(self.line_type_combo)
        
        # Line thickness
        thickness_label = QLabel("  Thickness: ")
        self.toolbar.addWidget(thickness_label)
        
        self.thickness_spinner = QSpinBox()
        self.thickness_spinner.setRange(1, 10)
        self.thickness_spinner.setValue(int(self.canvas.lineThickness))
        self.thickness_spinner.valueChanged.connect(self.onThicknessChanged)
        self.toolbar.addWidget(self.thickness_spinner)
        
        # Color picker
        self.toolbar.addSeparator()
        color_label = QLabel("Color: ")
        self.toolbar.addWidget(color_label)
        
        self.color_button = QPushButton()
        self.color_button.setFixedSize(24, 24)
        self.color_button.setStyleSheet(f"background-color: {self.canvas.currentColor.name()}; border: 1px solid #888;")
        self.color_button.clicked.connect(self.chooseColor)
        self.toolbar.addWidget(self.color_button)
        
        # Grid controls
        self.toolbar.addSeparator()
        grid_toggle = QAction("Toggle Grid", self)
        grid_toggle.triggered.connect(self.toggleGrid)
        self.toolbar.addAction(grid_toggle)
        
        # Coordinate system toggle
        self.toolbar.addSeparator()
        coord_label = QLabel("Coordinates: ")
        self.toolbar.addWidget(coord_label)
        
        self.coord_system_combo = QComboBox()
        for system, label in COORD_SYSTEMS.items():
            self.coord_system_combo.addItem(label, system)
        self.coord_system_combo.currentIndexChanged.connect(self.onCoordSystemChanged)
        self.toolbar.addWidget(self.coord_system_combo)
        
        # Theme toggle
        self.toolbar.addSeparator()
        theme_action = QAction("Toggle Theme", self)
        theme_action.triggered.connect(self.toggleTheme)
        self.toolbar.addAction(theme_action)

    def onDrawingModeChanged(self, index):
        mode = self.drawing_mode_combo.currentData()
        self.canvas.setDrawingMode(mode)
        self.statusBar.showMessage(f"Drawing mode: {DRAWING_MODES[mode]}")

    def onLineTypeChanged(self, index):
        line_type = self.line_type_combo.currentData()
        self.canvas.lineType = line_type
        self.statusBar.showMessage(f"Line type: {LINE_TYPES[line_type]}")

    def onThicknessChanged(self, value):
        self.canvas.lineThickness = value
        self.statusBar.showMessage(f"Line thickness: {value}")

    def onCoordSystemChanged(self, index):
        mode = self.coord_system_combo.currentData()
        self.setCoordinateSystem(mode)

    def setGridSize(self):
        size, ok = QInputDialog.getInt(
            self, 
            "Grid Size",
            "Enter grid cell size:",
            value=self.canvas.grid_size,
            minValue=10,
            maxValue=200
        )
        if ok:
            self.canvas.grid_size = size
            self.canvas.update()
            self.statusBar.showMessage(f"Grid size set to: {size}")

    def applyTheme(self):
        if self.is_dark_theme:
            # Dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #f0f0f0;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                    border-bottom: 1px solid #3d3d3d;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    color: #f0f0f0;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                    border: 1px solid #3d3d3d;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #f0f0f0;
                }
                QMenu::item:selected {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QToolBar {
                    background-color: #2d2d2d;
                    border: none;
                    spacing: 3px;
                    padding: 3px;
                }
                QToolBar::separator {
                    width: 1px;
                    background-color: #3d3d3d;
                    margin: 0 6px;
                }
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 3px;
                }
                QToolButton:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #555555;
                }
                QToolButton:pressed {
                    background-color: #444444;
                }
                QComboBox {
                    background-color: #383838;
                    color: #f0f0f0;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 120px;
                }
                QComboBox::drop-down {
                    width: 20px;
                    border: none;
                    background-color: #444444;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #383838;
                    color: #f0f0f0;
                    selection-background-color: #555555;
                    selection-color: #ffffff;
                }
                QStatusBar {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                    border-top: 1px solid #3d3d3d;
                }
                QLabel {
                    color: #f0f0f0;
                }
                QSpinBox {
                    background-color: #383838;
                    color: #f0f0f0;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 16px;
                    border-radius: 2px;
                    background-color: #444444;
                    margin: 1px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #555555;
                }
                QDockWidget {
                    color: #f0f0f0;
                    border: 1px solid #3d3d3d;
                }
                QDockWidget::title {
                    background-color: #2d2d2d;
                    padding: 8px;
                    color: #f0f0f0;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-bottom: 1px solid #e0e0e0;
                }
                QMenuBar::item {
                    padding: 8px 12px;
                    background-color: transparent;
                    color: #333333;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #e8e8e8;
                    color: #333333;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #e0e0e0;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 8px 25px;
                    border-radius: 4px;
                    margin: 2px 4px;
                    color: #333333;
                }
                QMenu::item:selected {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QToolBar {
                    background-color: #f0f0f0;
                    border: none;
                    spacing: 3px;
                    padding: 3px;
                }
                QToolBar::separator {
                    width: 1px;
                    background-color: #e0e0e0;
                    margin: 0 6px;
                }
                QToolButton {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 4px;
                    padding: 3px;
                }
                QToolButton:hover {
                    background-color: #e8e8e8;
                    border: 1px solid #d0d0d0;
                }
                QToolButton:pressed {
                    background-color: #d8d8d8;
                }
                QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    min-width: 120px;
                }
                QComboBox::drop-down {
                    width: 20px;
                    border: none;
                    background-color: #f0f0f0;
                }
                QComboBox::down-arrow {
                    width: 12px;
                    height: 12px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #333333;
                    selection-background-color: #e8e8e8;
                    selection-color: #333333;
                }
                QStatusBar {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-top: 1px solid #e0e0e0;
                }
                QLabel {
                    color: #333333;
                }
                QSpinBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 16px;
                    border-radius: 2px;
                    background-color: #f0f0f0;
                    margin: 1px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #e8e8e8;
                }
                QDockWidget {
                    color: #333333;
                    border: 1px solid #e0e0e0;
                }
                QDockWidget::title {
                    background-color: #f0f0f0;
                    padding: 8px;
                    color: #333333;
                }
            """)

    def createMenus(self):
        mainMenu = self.menuBar()

        # Create File menu
        fileMenu = mainMenu.addMenu('File')
        
        # New action
        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Create a new file')
        newAction.triggered.connect(self.newFile)
        fileMenu.addAction(newAction)
        
        # Open DXF action
        openDxfAction = QAction('Open DXF...', self)
        openDxfAction.setShortcut('Ctrl+O')
        openDxfAction.setStatusTip('Open a DXF file')
        openDxfAction.triggered.connect(self.openDxfFile)
        fileMenu.addAction(openDxfAction)
        
        # Save action
        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Save file')
        saveAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveAction)
        
        # Save As action
        saveAsAction = QAction('Save As...', self)
        saveAsAction.setShortcut('Ctrl+Shift+S')
        saveAsAction.setStatusTip('Save file as...')
        saveAsAction.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveAsAction)
        
        fileMenu.addSeparator()
        
        # Exit action
        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit the application')
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        # Add View menu
        viewMenu = mainMenu.addMenu('View')
        
        # Grid toggle button
        gridAction = QAction('Show/Hide Grid', self)
        gridAction.setStatusTip("Toggle grid display")
        gridAction.triggered.connect(self.toggleGrid)
        viewMenu.addAction(gridAction)

        # Grid size button
        gridSizeAction = QAction('Grid Size', self)
        gridSizeAction.setStatusTip("Change grid cell size")
        gridSizeAction.triggered.connect(self.setGridSize)
        viewMenu.addAction(gridSizeAction)
        
        viewMenu.addSeparator()
        
        # Theme toggle button
        themeAction = QAction('Toggle Theme', self)
        themeAction.setStatusTip("Switch between light and dark theme")
        themeAction.triggered.connect(self.toggleTheme)
        viewMenu.addAction(themeAction)
        
        # Create Drawing menu
        drawingMenu = mainMenu.addMenu('Draw')
        self.createDrawingObjectsMenu(drawingMenu)
        
        # Create Settings menu
        settingsMenu = mainMenu.addMenu('Settings')
        self.createLineSettingsMenu(settingsMenu)
        self.createShapeSettingsMenu(settingsMenu)
        self.createCoordinateSystemMenu(settingsMenu)

    def toggleGrid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.update()
        grid_state = "enabled" if self.canvas.show_grid else "disabled"
        self.statusBar.showMessage(f"Grid {grid_state}")

    def toggleTheme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.applyTheme()

        if hasattr(self, 'constructionTree'):
            self.constructionTree.updateThemeStyles(self.is_dark_theme)

        theme_name = "dark" if self.is_dark_theme else "light"
        self.statusBar.showMessage(f"Theme switched to {theme_name}")

    def createDrawingObjectsMenu(self, menu):
        # Adding individual modes
        for mode, label in DRAWING_MODES.items():
            if not any(mode in group for group in GROUPED_DRAWING_MODES.values()):
                action = QAction(label, self)
                action.setStatusTip(f"Drawing mode: {label}")
                action.triggered.connect(lambda checked, m=mode: self.setDrawingMode(m))
                menu.addAction(action)

        # Adding modes by groups
        for group_name, modes in GROUPED_DRAWING_MODES.items():
            groupMenu = menu.addMenu(group_name)
            for mode in modes:
                action = QAction(DRAWING_MODES[mode], self)
                action.setStatusTip(f"Drawing mode: {DRAWING_MODES[mode]}")
                action.triggered.connect(lambda checked, m=mode: self.setDrawingMode(m))
                groupMenu.addAction(action)

    def createLineSettingsMenu(self, menu):
        lineSettingsMenu = menu.addMenu('Line Type')
        for line_type, label in LINE_TYPES.items():
            action = QAction(label, self)
            action.setStatusTip(f"Set {label.lower()}")
            action.triggered.connect(lambda checked, lt=line_type: self.setLineType(lt))
            lineSettingsMenu.addAction(action)

    def createShapeSettingsMenu(self, menu):
        shapeSettingsMenu = menu.addMenu('Shape Settings')
        
        # Color button
        colorAction = QAction('Select Color', self)
        colorAction.setStatusTip("Choose color for new shapes")
        colorAction.triggered.connect(self.chooseColor)
        shapeSettingsMenu.addAction(colorAction)
        
        # Line thickness button
        lineThicknessAction = QAction('Line Thickness', self)
        lineThicknessAction.setStatusTip("Change line thickness")
        lineThicknessAction.triggered.connect(self.setLineThickness)
        shapeSettingsMenu.addAction(lineThicknessAction)
    
    def chooseColor(self):
        """
        Opens a color dialog for selecting CAD-compatible colors
        """
        color = QColorDialog.getColor(self.canvas.currentColor, self, "Select Color")
        if color.isValid():
            self.canvas.currentColor = color
            # Update color button background
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #888;")
            self.statusBar.showMessage(f"Line color changed to {color.name()}")

    def createCoordinateSystemMenu(self, menu):
        coordinateSystemMenu = menu.addMenu('Coordinate System')

        # Create action for "Polar"
        polarAction = QAction('Polar', self)
        polarAction.setStatusTip("Switch to Polar coordinate system")
        polarAction.triggered.connect(lambda: self.setCoordinateSystem('polar'))
        coordinateSystemMenu.addAction(polarAction)
        
        # Create action for "Cartesian"
        cartesianAction = QAction('Cartesian', self)
        cartesianAction.setStatusTip("Switch to Cartesian coordinate system")
        cartesianAction.triggered.connect(lambda: self.setCoordinateSystem('cartesian'))
        coordinateSystemMenu.addAction(cartesianAction)

    def createConstructionTree(self):
        if not self.findChild(QDockWidget, "Object Tree"):
            self.constructionTree = ObjectTree(self, self.canvas)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.constructionTree)

    def createStatusBar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Add file name label to status bar
        self.statusBar.addPermanentWidget(QLabel("| "))
        
        self.fileNameLabel = QLabel("New file")
        self.statusBar.addPermanentWidget(self.fileNameLabel)
        
        self.statusBar.addPermanentWidget(QLabel(" | "))
        
        # Add coordinate system indicator
        self.coordSystemLabel = QLabel("Cartesian")
        self.statusBar.addPermanentWidget(self.coordSystemLabel)

        # Initial status message
        self.statusBar.showMessage("Ready")

    def handleManualInput(self):
        self.canvas.handle_manual_input()

    def setCoordinateSystem(self, mode):
        self.canvas.inputCoordinateSystem = mode
        self.coordSystemLabel.setText(COORD_SYSTEMS[mode])
        self.statusBar.showMessage(f"Coordinate system switched to {COORD_SYSTEMS[mode]}")

        # Show information dialog about the selected coordinate system
        if mode == 'cartesian':
            QMessageBox.information(self, "Input Coordinate System", "Coordinates will be entered in Cartesian system.")
        else:
            QMessageBox.information(self, "Input Coordinate System", "Coordinates will be entered in Polar system.")

    def setDrawingMode(self, mode):
        self.canvas.setDrawingMode(mode)
        # Update the combobox to match
        index = self.drawing_mode_combo.findData(mode)
        if index >= 0:
            self.drawing_mode_combo.setCurrentIndex(index)
        self.statusBar.showMessage(f"Drawing mode: {DRAWING_MODES[mode]}")

    def setLineType(self, line_type):
        self.canvas.lineType = line_type
        # Update the combobox to match
        index = self.line_type_combo.findData(line_type)
        if index >= 0:
            self.line_type_combo.setCurrentIndex(index)
        self.statusBar.showMessage(f"Line type set to: {LINE_TYPES[line_type]}")

    def setLineThickness(self):
        """
        Shows a dialog to select standard ISO line thickness
        """
        # Standard ISO line thickness values in mm
        standard_thicknesses = [
            0.00, 0.05, 0.09,  # Very thin
            0.13, 0.15, 0.18, 0.20, 0.25,  # Thin
            0.30, 0.35, 0.40, 0.50,  # Medium
            0.70,  # Thick
            1.00   # Very thick
        ]
        
        # Find the closest standard value to current thickness
        current_thickness = self.canvas.lineThickness
        closest_thickness = min(standard_thicknesses, key=lambda x: abs(x - current_thickness))
        current_index = standard_thicknesses.index(closest_thickness)
        
        # Create descriptive labels for each thickness
        thickness_labels = []
        for t in standard_thicknesses:
            if t <= 0.09:
                category = "Very thin"
            elif t <= 0.25:
                category = "Thin"
            elif t <= 0.50:
                category = "Medium"
            elif t <= 0.70:
                category = "Thick"
            else:
                category = "Very thick"
            thickness_labels.append(f"{t:.2f} mm ({category})")
        
        # Show thickness selection dialog
        thickness, ok = QInputDialog.getItem(
            self, 
            "Line Thickness", 
            "Select standard ISO line thickness:", 
            thickness_labels, 
            current_index, 
            False
        )
        
        if ok:
            # Extract thickness value from selected label
            selected_thickness = float(thickness.split()[0])
            self.canvas.lineThickness = selected_thickness
            # Update the spinner
            self.thickness_spinner.setValue(int(selected_thickness) if selected_thickness >= 1 else 1)
            self.statusBar.showMessage(f"Line thickness set to: {selected_thickness} mm")

    # New file handling methods
    def newFile(self):
        # Check if there are unsaved changes
        if self.canvas.shapes and self.confirmSaveChanges():
            # Save current file if user wants to
            self.saveFile()
            
        # Clear canvas
        self.canvas.shapes.clear()
        self.canvas.update()
        self.constructionTree.updateConstructionTree()
        
        # Reset current file
        self.current_file = None
        self.fileNameLabel.setText("New file")
        self.statusBar.showMessage("New file created")
    
    def openDxfFile(self):
        # Check if there are unsaved changes
        if self.canvas.shapes and self.confirmSaveChanges():
            # Save current file if user wants to
            self.saveFile()
        
        # Open file dialog
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Open DXF File", 
            "", 
            "DXF Files (*.dxf);;All Files (*)", 
            options=options
        )
        
        if filename:
            try:
                # Clear current shapes
                self.canvas.shapes.clear()
                
                # Load shapes from DXF file
                loaded_shapes = read_from_dxf(filename, self.canvas)
                
                # Add loaded shapes to canvas
                if loaded_shapes:
                    self.canvas.shapes.extend(loaded_shapes)
                    self.canvas.update()
                    self.constructionTree.updateConstructionTree()
                    
                    # Update current file
                    self.current_file = filename
                    self.fileNameLabel.setText(f"{self.getFileNameFromPath(filename)}")
                    self.statusBar.showMessage(f"File loaded: {filename}")
                else:
                    QMessageBox.warning(self, "Load Error", "Could not load shapes from file.")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"An error occurred while loading the file:\n{str(e)}")
    
    def saveFile(self):
        # If no current file, use save as
        if not self.current_file:
            return self.saveFileAs()
        
        # Save to current file
        try:
            success = save_to_dxf_advanced(self.canvas.shapes, self.current_file)
            if success:
                self.statusBar.showMessage(f"File saved: {self.current_file}")
                return True
            else:
                QMessageBox.warning(self, "Save Error", "Could not save file.")
                return False
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving the file:\n{str(e)}")
            return False
    
    def saveFileAs(self):
        # Open file dialog
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save As DXF File", 
            "", 
            "DXF Files (*.dxf)", 
            options=options
        )
        
        if filename:
            # Add .dxf extension if not present
            if not filename.lower().endswith('.dxf'):
                filename += '.dxf'
                
            # Save to file
            try:
                success = save_to_dxf_advanced(self.canvas.shapes, filename)
                if success:
                    self.current_file = filename
                    self.fileNameLabel.setText(f"{self.getFileNameFromPath(filename)}")
                    self.statusBar.showMessage(f"File saved: {filename}")
                    return True
                else:
                    QMessageBox.warning(self, "Save Error", "Could not save file.")
                    return False
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"An error occurred while saving the file:\n{str(e)}")
                return False
        
        return False
    
    def confirmSaveChanges(self):
        """Ask the user whether to save changes to the current file"""
        reply = QMessageBox.question(
            self, 
            "Unsaved Changes", 
            "Save changes to the current file?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            return True
        elif reply == QMessageBox.Discard:
            return False
        else:  # Cancel
            return None
    
    def getFileNameFromPath(self, path):
        """Extract just the file name from a path"""
        import os
        return os.path.basename(path)
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.canvas.shapes and self.confirmSaveChanges():
            if self.saveFile():
                event.accept()
            else:
                # If save failed, ask if they want to quit anyway
                reply = QMessageBox.question(
                    self, 
                    "Save Error", 
                    "Could not save file. Exit without saving?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()
        else:
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application-wide style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
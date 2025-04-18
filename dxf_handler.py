import ezdxf
import math
from PySide6.QtCore import QPointF, QRectF
from core.line import Line
from core.circle import Circle, CircleByThreePoints
from core.arc import ArcByThreePoints, ArcByRadiusChord
from core.polygon import Polygon
from core.rectangle import Rectangle
from core.spline import BezierSpline, SegmentSpline

def save_to_dxf(shapes, filename):
    """
    Saves the given shapes to a DXF file
    
    Args:
        shapes: List of geometry objects
        filename: Path to save the DXF file
    """
    # Create a new DXF document
    doc = ezdxf.new('R2010')  # AutoCAD 2010 format
    msp = doc.modelspace()  # Get the model space
    
    # Convert each shape to its corresponding DXF entity
    for shape in shapes:
        if isinstance(shape, Line):
            # Add line entity
            msp.add_line(
                (shape.start_point.x(), shape.start_point.y()), 
                (shape.end_point.x(), shape.end_point.y()),
                dxfattribs=get_dxf_attributes(shape)
            )
            
        elif isinstance(shape, Circle):
            # Add circle entity
            msp.add_circle(
                (shape.center.x(), shape.center.y()),
                shape.radius,
                dxfattribs=get_dxf_attributes(shape)
            )
            
        elif isinstance(shape, CircleByThreePoints):
            # Calculate circle parameters and add circle entity
            center, radius = shape.calculate_circle()
            if center and radius:
                msp.add_circle(
                    (center.x(), center.y()),
                    radius,
                    dxfattribs=get_dxf_attributes(shape)
                )
            
        elif isinstance(shape, ArcByThreePoints):
            # Calculate arc parameters and add arc entity
            center, radius, start_angle, span_angle = shape.calculate_arc()
            if center and radius:
                # Convert angles from degrees to radians
                start_angle_rad = math.radians(start_angle)
                end_angle_rad = math.radians(start_angle + span_angle)
                
                msp.add_arc(
                    (center.x(), center.y()),
                    radius,
                    math.degrees(start_angle_rad),
                    math.degrees(end_angle_rad),
                    dxfattribs=get_dxf_attributes(shape)
                )
            
        elif isinstance(shape, ArcByRadiusChord):
            # Calculate arc parameters and add arc entity
            radius, start_angle, span_angle = shape.calculate_arc()
            
            # Convert angles from degrees to radians
            start_angle_rad = math.radians(start_angle)
            end_angle_rad = math.radians(start_angle + span_angle)
            
            msp.add_arc(
                (shape.center.x(), shape.center.y()),
                radius,
                math.degrees(start_angle_rad),
                math.degrees(end_angle_rad),
                dxfattribs=get_dxf_attributes(shape)
            )
            
        elif isinstance(shape, Rectangle):
            # Add rectangle as a polyline
            rect = shape.rect
            points = [
                (rect.topLeft().x(), rect.topLeft().y()),
                (rect.topRight().x(), rect.topRight().y()),
                (rect.bottomRight().x(), rect.bottomRight().y()),
                (rect.bottomLeft().x(), rect.bottomLeft().y()),
                (rect.topLeft().x(), rect.topLeft().y())
            ]
            msp.add_lwpolyline(points, dxfattribs=get_dxf_attributes(shape))
            
        elif isinstance(shape, Polygon):
            # Add polygon as a polyline
            points = [(point.x(), point.y()) for point in shape.points]
            if points:
                # Close the polygon by adding the first point again
                points.append(points[0])
                msp.add_lwpolyline(points, dxfattribs=get_dxf_attributes(shape))
                
        elif isinstance(shape, BezierSpline):
            # Convert Bezier spline to polyline with many segments
            if len(shape.points) >= 2:
                t_values = [i / shape.num_segments for i in range(shape.num_segments + 1)]
                polyline_points = []
                for t in t_values:
                    point = shape.bezier_point(t)
                    polyline_points.append((point.x(), point.y()))
                
                msp.add_lwpolyline(polyline_points, dxfattribs=get_dxf_attributes(shape))
                
        elif isinstance(shape, SegmentSpline):
            # Add segment spline as a polyline
            spline_points = shape.generate_spline_points()
            if spline_points:
                points = [(point.x(), point.y()) for point in spline_points]
                msp.add_lwpolyline(points, dxfattribs=get_dxf_attributes(shape))
    
    # Save the DXF document
    doc.saveas(filename)
    return True

def get_dxf_attributes(shape):
    """
    Converts shape attributes to DXF attributes
    
    Args:
        shape: The geometry object
        
    Returns:
        Dictionary of DXF attributes
    """
    attributes = {}
    
    # Convert color
    if hasattr(shape, 'color'):
        # Convert QColor to AutoCAD color index (approximate)
        color_index = convert_qcolor_to_aci(shape.color)
        attributes['color'] = color_index
    
    # Convert line type
    if hasattr(shape, 'line_type'):
        line_type = shape.line_type
        if line_type != 'solid':
            # Create or use the appropriate line type
            if line_type == 'dash':
                attributes['linetype'] = 'DASHED'
            elif line_type == 'dash_dot':
                attributes['linetype'] = 'DASHDOT'
            elif line_type == 'dash_dot_dot':
                attributes['linetype'] = 'DASHDOT2'
    
    # Convert line thickness
    if hasattr(shape, 'line_thickness'):
        # DXF uses lineweight in 100ths of mm
        # Convert from application units to 100ths of mm (approximate)
        attributes['lineweight'] = int(shape.line_thickness * 10)
    
    return attributes

def convert_qcolor_to_aci(qcolor):
    """
    Converts a QColor to AutoCAD Color Index (ACI)
    
    Args:
        qcolor: QColor object
        
    Returns:
        Integer representing the closest AutoCAD Color Index
    """
    # This is a simplified conversion
    # AutoCAD uses a color index from 1 to 255
    # For now, we'll use a simple algorithm to find the closest match
    
    r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
    
    # Special cases
    if r == 0 and g == 0 and b == 0:
        return 0  # Black (or ByBlock)
    if r == 255 and g == 0 and b == 0:
        return 1  # Red
    if r == 255 and g == 255 and b == 0:
        return 2  # Yellow
    if r == 0 and g == 255 and b == 0:
        return 3  # Green
    if r == 0 and g == 255 and b == 255:
        return 4  # Cyan
    if r == 0 and g == 0 and b == 255:
        return 5  # Blue
    if r == 255 and g == 0 and b == 255:
        return 6  # Magenta
    if r == 255 and g == 255 and b == 255:
        return 7  # White
    
    # For other colors, return a reasonable default
    return 7

def read_from_dxf(filename, canvas):
    """
    Reads shapes from a DXF file and adds them to the canvas
    
    Args:
        filename: Path to the DXF file
        canvas: Canvas object to add shapes to
        
    Returns:
        List of loaded shapes
    """
    try:
        # Load the DXF document
        doc = ezdxf.readfile(filename)
        
        # Get the model space
        msp = doc.modelspace()
        
        # Create a list to store the loaded shapes
        loaded_shapes = []
        
        # Process all entities in the model space
        for entity in msp:
            # Convert DXF entity to application's geometry
            shape = convert_dxf_to_shape(entity, canvas)
            if shape:
                loaded_shapes.append(shape)
        
        return loaded_shapes
        
    except ezdxf.DXFError as e:
        print(f"DXF Error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error reading DXF file: {str(e)}")
        return []

def convert_dxf_to_shape(entity, canvas):
    """
    Converts a DXF entity to the corresponding application geometry
    
    Args:
        entity: DXF entity object
        canvas: Canvas object for attribute reference
        
    Returns:
        Geometry object or None if conversion is not supported
    """
    # Get common attributes
    shape_attributes = extract_dxf_attributes(entity, canvas)
    
    if entity.dxftype() == 'LINE':
        # Convert LINE entity to Line
        start_point = QPointF(entity.dxf.start[0], entity.dxf.start[1])
        end_point = QPointF(entity.dxf.end[0], entity.dxf.end[1])
        
        return Line(
            start_point, 
            end_point, 
            shape_attributes['line_type'], 
            shape_attributes['line_thickness'],
            dash_parameters=canvas.dash_parameters,
            dash_auto_mode=canvas.dash_auto_mode,
            color=shape_attributes['color']
        )
        
    elif entity.dxftype() == 'CIRCLE':
        # Convert CIRCLE entity to Circle
        center = QPointF(entity.dxf.center[0], entity.dxf.center[1])
        radius = entity.dxf.radius
        
        return Circle(
            center, 
            radius, 
            shape_attributes['line_type'], 
            shape_attributes['line_thickness'],
            dash_parameters=canvas.dash_parameters,
            dash_auto_mode=canvas.dash_auto_mode,
            color=shape_attributes['color']
        )
        
    elif entity.dxftype() == 'ARC':
        # Convert ARC entity to ArcByRadiusChord
        center = QPointF(entity.dxf.center[0], entity.dxf.center[1])
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        
        # Calculate points on arc
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        # Create points for ArcByRadiusChord
        radius_point = QPointF(
            center.x() + radius * math.cos(start_rad),
            center.y() + radius * math.sin(start_rad)
        )
        chord_point = QPointF(
            center.x() + radius * math.cos(end_rad),
            center.y() + radius * math.sin(end_rad)
        )
        
        return ArcByRadiusChord(
            center, 
            radius_point, 
            chord_point, 
            shape_attributes['line_type'], 
            shape_attributes['line_thickness'],
            dash_parameters=canvas.dash_parameters,
            dash_auto_mode=canvas.dash_auto_mode,
            color=shape_attributes['color']
        )
        
    elif entity.dxftype() == 'LWPOLYLINE':
        # Get polyline vertices
        vertices = list(entity.vertices())
        points = [QPointF(v[0], v[1]) for v in vertices]
        
        if len(points) < 2:
            return None
            
        # Check if this is a rectangle (4 points, closed)
        if len(points) == 5 and entity.closed:
            # Check if points form a rectangle
            if is_rectangle(points[:-1]):  # Ignore last point (duplicate of first for closed polyline)
                min_x = min(p.x() for p in points[:-1])
                min_y = min(p.y() for p in points[:-1])
                max_x = max(p.x() for p in points[:-1])
                max_y = max(p.y() for p in points[:-1])
                
                rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
                
                return Rectangle(
                    rect, 
                    shape_attributes['line_type'], 
                    shape_attributes['line_thickness'],
                    dash_parameters=canvas.dash_parameters,
                    dash_auto_mode=canvas.dash_auto_mode,
                    color=shape_attributes['color']
                )
        
        # Otherwise treat as a polygon
        return Polygon(
            points[:-1] if entity.closed and points[0] == points[-1] else points, 
            shape_attributes['line_type'], 
            shape_attributes['line_thickness'],
            dash_parameters=canvas.dash_parameters,
            dash_auto_mode=canvas.dash_auto_mode,
            color=shape_attributes['color']
        )
        
    elif entity.dxftype() == 'SPLINE':
        # Convert SPLINE entity to BezierSpline
        control_points = [QPointF(p[0], p[1]) for p in entity.control_points]
        
        return BezierSpline(
            control_points, 
            shape_attributes['line_type'], 
            shape_attributes['line_thickness'],
            dash_parameters=canvas.dash_parameters,
            dash_auto_mode=canvas.dash_auto_mode,
            color=shape_attributes['color']
        )
    
    # If we can't convert the entity, return None
    return None

def is_rectangle(points):
    """Check if 4 points form a rectangle"""
    if len(points) != 4:
        return False
        
    # Check if all angles are 90 degrees (or 270 degrees)
    for i in range(4):
        p1 = points[i]
        p2 = points[(i + 1) % 4]
        p3 = points[(i + 2) % 4]
        
        # Calculate vectors
        v1 = (p2.x() - p1.x(), p2.y() - p1.y())
        v2 = (p3.x() - p2.x(), p3.y() - p2.y())
        
        # Calculate dot product (should be 0 for perpendicular vectors)
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        # Allow for some floating-point error
        if abs(dot_product) > 1e-10:
            return False
            
    return True

def extract_dxf_attributes(entity, canvas):
    """
    Extract attributes from a DXF entity
    
    Args:
        entity: DXF entity object
        canvas: Canvas object for default attributes
        
    Returns:
        Dictionary of attributes compatible with application
    """
    attributes = {
        'line_type': 'solid',
        'line_thickness': canvas.lineThickness,
        'color': canvas.currentColor
    }
    
    # Get color if available
    if hasattr(entity.dxf, 'color') and entity.dxf.color != 256:  # 256 is "ByLayer"
        # Convert color index to QColor
        attributes['color'] = convert_aci_to_qcolor(entity.dxf.color)
    
    # Get line type if available
    if hasattr(entity.dxf, 'linetype'):
        linetype = entity.dxf.linetype
        if linetype == 'DASHED':
            attributes['line_type'] = 'dash'
        elif linetype == 'DASHDOT':
            attributes['line_type'] = 'dash_dot'
        elif linetype in ['DASHDOT2', 'DIVIDE']:
            attributes['line_type'] = 'dash_dot_dot'
    
    # Get line thickness if available
    if hasattr(entity.dxf, 'lineweight') and entity.dxf.lineweight != -1:  # -1 is "ByLayer"
        # DXF uses lineweight in 100ths of mm
        # Convert to application units (approximate)
        attributes['line_thickness'] = entity.dxf.lineweight / 10
    
    return attributes

def convert_aci_to_qcolor(aci):
    """
    Convert AutoCAD Color Index (ACI) to QColor
    
    Args:
        aci: AutoCAD Color Index
        
    Returns:
        QColor object
    """
    from PySide6.QtGui import QColor
    
    # Standard AutoCAD Color Index to RGB mapping
    aci_to_rgb = {
        0: (0, 0, 0),     # Black (ByBlock)
        1: (255, 0, 0),   # Red
        2: (255, 255, 0), # Yellow
        3: (0, 255, 0),   # Green
        4: (0, 255, 255), # Cyan
        5: (0, 0, 255),   # Blue
        6: (255, 0, 255), # Magenta
        7: (255, 255, 255), # White
        8: (128, 128, 128), # Gray
        9: (192, 192, 192), # Light Gray
        # More colors could be added here
    }
    
    # Default to black if color not found
    r, g, b = aci_to_rgb.get(aci, (0, 0, 0))
    
    return QColor(r, g, b)
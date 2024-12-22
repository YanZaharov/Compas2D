from math import factorial

def binomial_coefficient(n, k):
    """Вычисляет биномиальный коэффициент."""
    return factorial(n) // (factorial(k) * factorial(n - k))

def bezier_point(t, points):
    """Вычисляет точку на кривой Безье по параметру t."""
    n = len(points) - 1
    x, y = 0, 0
    for i in range(n + 1):
        binom = binomial_coefficient(n, i)
        factor = (1 - t) ** (n - i) * t ** i
        x += binom * factor * points[i].x()
        y += binom * factor * points[i].y()
    return x, y

def generate_bezier_path(points, num_segments=100):
    """Создает путь для кривой Безье."""
    if len(points) < 2:
        return None

    from PyQt5.QtGui import QPainterPath

    path = QPainterPath(points[0])
    t_values = [i / num_segments for i in range(num_segments + 1)]
    
    for t in t_values:
        x, y = bezier_point(t, points)
        path.lineTo(x, y)
    
    return path

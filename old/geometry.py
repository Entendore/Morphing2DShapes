import numpy as np

def _interpolate_polygon(corners, n_points):
    """Arc-length parameterization for polygons."""
    dists = np.cumsum(np.sqrt(np.sum(np.diff(corners, axis=0)**2, axis=1)))
    dists = np.insert(dists, 0, 0)
    if dists[-1] == 0:
        return np.tile(corners[0], (n_points, 1))
    dists /= dists[-1]
    t = np.linspace(0, 1, n_points)
    x = np.interp(t, dists, corners[:, 0])
    y = np.interp(t, dists, corners[:, 1])
    return np.column_stack([x, y])

def generate_circle(n=100, radius=1.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.column_stack([radius * np.cos(t), radius * np.sin(t)])

def generate_polygon(n=100, radius=1.0, sides=6):
    angles = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    corners = np.column_stack([radius * np.cos(angles), radius * np.sin(angles)])
    corners = np.vstack([corners, corners[0]])
    return _interpolate_polygon(corners, n)

def generate_star(n=100, radius=1.0, points=5):
    outer = radius
    inner = 0.4 * radius  # Maintain aspect ratio
    angles = np.linspace(0, 2 * np.pi, points * 2, endpoint=False)
    radii = np.tile([outer, inner], points)
    corners = np.column_stack([radii * np.cos(angles), radii * np.sin(angles)])
    corners = np.vstack([corners, corners[0]])
    return _interpolate_polygon(corners, n)

# FIX: Changed 'scale' argument to 'radius' to match registry standard
def generate_heart(n=100, radius=1.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t)**3
    y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
    # Normalize using the radius
    x = x / np.max(np.abs(x)) * radius
    y = y / np.max(np.abs(y)) * radius
    return np.column_stack([x, y])

def generate_blob(n=100, radius=1.0, seed=42):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = radius + rng.uniform(-0.2, 0.2, n) * radius
    return np.column_stack([r * np.cos(t), r * np.sin(t)])

def catmull_rom_smooth(points, density=3):
    """Apply Catmull-Rom spline smoothing."""
    if len(points) < 4: return points
    result = [points[0]]
    for i in range(len(points) - 3):
        p0, p1, p2, p3 = points[i:i+4]
        for t in np.linspace(0, 1, density, endpoint=False):
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + 
                      (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + 
                      (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + 
                      (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + 
                      (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            result.append([x, y])
    result.append(points[-1])
    return np.array(result)

SHAPE_REGISTRY = {
    "Circle": generate_circle, 
    "Polygon": generate_polygon, 
    "Star": generate_star,
    "Heart": generate_heart, 
    "Blob": generate_blob
}
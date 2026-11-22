import numpy as np
from geometry import _interpolate_polygon

def resample_shape(shape, n):
    """Ensure shape has exactly n points via arc-length parameterization."""
    if shape is None or len(shape) == 0:
        from geometry import generate_circle
        return generate_circle(n, 1.0)
    if len(shape) == n: return shape.copy()
    if not np.allclose(shape[0], shape[-1]):
        shape = np.vstack([shape, shape[0]])
    return _interpolate_polygon(shape, n)

def morph_linear(s1, s2, t): 
    return (1 - t) * s1 + t * s2

def morph_ease_in_out(s1, s2, t):
    e = 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) ** 2
    return morph_linear(s1, s2, e)

def morph_elastic(s1, s2, t):
    if t == 0: return s1
    if t == 1: return s2
    c4 = (2 * np.pi) / 3
    if t < 0.5:
        e = -pow(2, 20 * t - 10) * np.sin((20 * t - 11.125) * c4)
    else:
        e = pow(2, -20 * t + 10) * np.sin((20 * t - 11.125) * c4) / 2 + 1
    return morph_linear(s1, s2, e)

def morph_sequence(shapes, t, morph_fn=morph_linear):
    """Morph through N shapes with potentially different resolutions."""
    if not shapes: return None
    if len(shapes) == 1: return shapes[0].copy()
    
    n_segments = len(shapes) - 1
    segment = min(int(t * n_segments), n_segments - 1)
    local_t = (t * n_segments) - segment
    local_t = np.clip(local_t, 0, 1)
    
    s1 = shapes[segment]
    s2 = shapes[segment + 1]
    
    # If shapes have different point counts, resample both to the HIGHER count
    # This ensures detail is preserved when morphing from simple to complex shapes
    target_pts = max(s1.shape[0], s2.shape[0])
    
    s1_resampled = resample_shape(s1, target_pts)
    s2_resampled = resample_shape(s2, target_pts)
    
    return morph_fn(s1_resampled, s2_resampled, local_t)

MORPH_MODES = {
    "Linear": morph_linear, 
    "Ease In-Out": morph_ease_in_out, 
    "Elastic": morph_elastic
}
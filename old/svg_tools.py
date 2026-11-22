import re
import numpy as np
import xml.etree.ElementTree as ET
from morphing import resample_shape

def parse_svg_content(svg_content, n_points=120):
    """Extract points from SVG paths/polygons and normalize."""
    try: root = ET.fromstring(svg_content)
    except ET.ParseError: return None

    all_coords = []
    # Regex for path commands and numbers
    token_re = re.compile(r'([MLCQHVZmlcqhvz])|([+-]?\d*\.?\d+(?:e[+-]?\d+)?)')
    
    for elem in root.iter():
        tag = elem.tag.split('}')[-1].lower()
        d = elem.get('d', '')
        
        if tag == 'path' and d:
            tokens = [t[0] if t[0] else float(t[1]) for t in token_re.findall(d)]
            pts = []
            i = 0
            cur_x, cur_y = 0.0, 0.0
            start_x, start_y = 0.0, 0.0
            
            while i < len(tokens):
                cmd = tokens[i]
                i += 1
                is_rel = isinstance(cmd, str) and cmd.islower()
                if isinstance(cmd, str): cmd = cmd.upper()
                else: cmd, i = 'L', i-1 # Implicit L
                
                try:
                    if cmd == 'M':
                        cur_x, cur_y = tokens[i], tokens[i+1]; i += 2
                        if is_rel and pts: cur_x += pts[-1][0]; cur_y += pts[-1][1]
                        start_x, start_y = cur_x, cur_y
                        pts.append((cur_x, cur_y))
                    elif cmd == 'L':
                        x, y = tokens[i], tokens[i+1]; i += 2
                        cur_x, cur_y = (cur_x+x, cur_y+y) if is_rel else (x, y)
                        pts.append((cur_x, cur_y))
                    elif cmd == 'C':
                        # Bezier approximation
                        x1, y1, x2, y2, x, y = tokens[i:i+6]; i += 6
                        if is_rel: x1+=cur_x; y1+=cur_y; x2+=cur_x; y2+=cur_y; x+=cur_x; y+=cur_y
                        # Approximate with 10 segments
                        for t in np.linspace(0, 1, 10):
                            xt = (1-t)**3*cur_x + 3*(1-t)**2*t*x1 + 3*(1-t)*t**2*x2 + t**3*x
                            yt = (1-t)**3*cur_y + 3*(1-t)**2*t*y1 + 3*(1-t)*t**2*y2 + t**3*y
                            pts.append((xt, yt))
                        cur_x, cur_y = x, y
                    elif cmd == 'Z' and pts:
                        if not (abs(pts[-1][0]-start_x)<1e-5 and abs(pts[-1][1]-start_y)<1e-5):
                            pts.append((start_x, start_y))
                except IndexError: break
            all_coords.extend(pts)
            
        elif tag in ('polygon', 'polyline'):
            coords = re.findall(r'[+-]?\d*\.?\d+', elem.get('points', ''))
            pts = [(float(coords[j]), float(coords[j+1])) for j in range(0, len(coords)-1, 2)]
            all_coords.extend(pts)
            
    if len(all_coords) < 3: return None
    
    arr = np.array(all_coords)
    center = np.mean(arr, axis=0); arr -= center
    max_r = np.max(np.sqrt(np.sum(arr**2, axis=1)))
    if max_r > 0: arr /= (max_r / 0.8)
    return resample_shape(arr, n_points)

def export_shape_to_svg(points, filename):
    if points is None or len(points) == 0: return
    scale, offset = 200, 200
    pts_svg = [(p[0]*scale + offset, -p[1]*scale + offset) for p in points]
    path_d = f"M {pts_svg[0][0]:.2f} {pts_svg[0][1]:.2f} " + \
             "".join(f"L {x:.2f} {y:.2f} " for x, y in pts_svg[1:]) + "Z"
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
  <path d="{path_d}" fill="none" stroke="#2c3e50" stroke-width="2"/>
</svg>'''
    with open(filename, 'w', encoding='utf-8') as f: f.write(svg)
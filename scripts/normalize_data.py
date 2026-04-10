import json
import csv
import os


def ring_area(ring):
    """Approximate ring area via shoelace formula in lon/lat plane."""
    if not ring or len(ring) < 3:
        return 0.0
    area = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        area += (x1 * y2) - (x2 * y1)
    return abs(area) * 0.5


def polygon_area(coords):
    """Polygon area = outer ring - inner rings."""
    if not coords:
        return 0.0
    outer = ring_area(coords[0])
    holes = sum(ring_area(r) for r in coords[1:])
    return max(outer - holes, 0.0)


def feature_area(geometry):
    if not geometry:
        return 0.0
    gtype = geometry.get('type')
    coords = geometry.get('coordinates', [])
    if gtype == 'Polygon':
        return polygon_area(coords)
    if gtype == 'MultiPolygon':
        return sum(polygon_area(poly) for poly in coords)
    return 0.0

def process_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    features = data.get('features', [])
    
    # Calculate total 2019 and 2025 stops
    total_2019 = sum(f['properties'].get('total_stops_2019', 0) for f in features)
    total_2025 = sum(f['properties'].get('total_stops_2025', 0) for f in features)
    
    rows = []
    for f in features:
        props = f['properties']
        geom = f.get('geometry', {})
        area_value = feature_area(geom)
        # Higher fill-sort-key draws above lower keys; negating area places smaller polygons on top.
        props['z_sort'] = -area_value
        
        # Normalize
        if total_2019 > 0 and total_2025 > 0:
            props['normed_2019'] = props.get('total_stops_2019', 0) / total_2019
            props['normed_2025'] = props.get('total_stops_2025', 0) / total_2025
            props['normed_diff'] = props['normed_2025'] - props['normed_2019']
        else:
            props['normed_2019'] = 0
            props['normed_2025'] = 0
            props['normed_diff'] = 0
            
        # Remove raw values from properties to keep them private
        props.pop('total_stops_2019', None)
        props.pop('total_stops_2025', None)
        props.pop('raw_diff', None)
        
        rows.append(props.copy())
        
    # Overwrite GeoJSON without raw values
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':')) # compact format
    print(f"Updated GeoJSON (removed raw values): {filepath}")
        
    if not rows:
        return
        
    # Write to CSV
    csv_filepath = filepath.replace('.geojson', '_normalized.csv')
    
    # Collect all unique fieldnames
    fieldnames = []
    for r in rows:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)
                
    with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Created CSV: {csv_filepath}")

if __name__ == '__main__':
    files = [
        '../static/data/dc_districts.geojson',
        '../static/data/sf_districts.geojson',
        '../docs/data/dc_districts.geojson',
        '../docs/data/sf_districts.geojson'
    ]
    
    # Adjust path if run directly from workspace root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for relative_path in files:
        filepath = os.path.join(base_dir, relative_path)
        process_file(filepath)

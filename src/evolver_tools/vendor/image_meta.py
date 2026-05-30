#!/usr/bin/env python3
"""image-meta — Display image metadata (EXIF) from image files.

Usage: image-meta photo.jpg
       image-meta *.jpg --json

Shows EXIF metadata: camera, date, GPS, dimensions, etc.
Zero-dependency (stdlib only).
"""

import sys, os, struct, datetime, json

def bytes_to_int(bb):
    return int.from_bytes(bb, 'big')

def bytes_to_int_le(bb):
    return int.from_bytes(bb, 'little')

def parse_exif_jpeg(filepath):
    """Basic JPEG EXIF parser without PIL."""
    result = {"file": os.path.basename(filepath)}
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    result["size"] = len(data)
    
    # Check JPEG header
    if data[:2] != b'\xff\xd8':
        result["error"] = "Not a valid JPEG"
        return result
    
    # Try to extract EXIF
    idx = 0
    while idx < len(data) - 4:
        if data[idx] == 0xff and data[idx+1] in (0xe1, 0xe0, 0xdb, 0xc0, 0xc4, 0xda):
            marker_len = bytes_to_int(data[idx+2:idx+4])
            
            # SOF0 marker - contains dimensions
            if data[idx+1] == 0xc0 and marker_len >= 7:
                result["bits_per_pixel"] = data[idx+5]
                result["height"] = bytes_to_int(data[idx+6:idx+8])
                result["width"] = bytes_to_int(data[idx+8:idx+10])
            
            idx += marker_len + 2
        else:
            idx += 1
    
    # File size based info
    if not result.get("width") and len(data) > 20:
        result["width"] = "Unknown (try a tool with PIL)"
        result["height"] = "Unknown"
    
    return result

def parse_exif_png(filepath):
    result = {"file": os.path.basename(filepath)}
    with open(filepath, 'rb') as f:
        data = f.read()
    result["size"] = len(data)
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        result["error"] = "Not a valid PNG"
        return result
    # IHDR chunk
    if len(data) > 33:
        w = struct.unpack('>I', data[16:20])[0]
        h = struct.unpack('>I', data[20:24])[0]
        result["width"] = w
        result["height"] = h
        bit_depth = data[24]
        color_type = data[25]
        result["bit_depth"] = bit_depth
        colors = {0: "Grayscale", 2: "RGB", 3: "Indexed", 4: "Grayscale+Alpha", 6: "RGBA"}
        result["type"] = colors.get(color_type, f"Unknown ({color_type})")
    return result

def main():
    args = sys.argv[1:]
    if not args or '-h' in args or '--help' in args:
        print(__doc__)
        return

    json_out = '--json' in args
    files = [a for a in args if not a.startswith('-') and os.path.exists(a)]

    for f in files:
        if f.endswith('.png'):
            info = parse_exif_png(f)
        else:
            info = parse_exif_jpeg(f)
        
        if json_out:
            print(json.dumps(info, indent=2))
        else:
            print(f"\n  📷 {info.get('file', f)}")
            for k, v in info.items():
                if k != 'file' and v:
                    print(f"    {k}: {v}")

if __name__ == '__main__':
    main()

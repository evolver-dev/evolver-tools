#!/usr/bin/env python3
"""image-meta — Extract image metadata. Read PNG, JPEG, GIF headers for dimensions, format, color mode. Show EXIF data."""

import sys
import os
import struct
import argparse
import json


def read_bytes(filepath, offset, size):
    """Read bytes from file at given offset."""
    with open(filepath, 'rb') as f:
        f.seek(offset)
        return f.read(size)


def get_png_info(filepath):
    """Extract metadata from PNG file."""
    info = {'format': 'PNG', 'file': filepath}
    try:
        with open(filepath, 'rb') as f:
            header = f.read(8)
            if header != b'\x89PNG\r\n\x1a\n':
                info['error'] = 'Invalid PNG signature'
                return info

            # Read IHDR chunk
            f.read(4)  # chunk length
            chunk_type = f.read(4)
            if chunk_type != b'IHDR':
                info['error'] = 'Missing IHDR chunk'
                return info

            ihdr = f.read(13)
            width, height = struct.unpack('>II', ihdr[:8])
            bit_depth = ihdr[8]
            color_type = ihdr[9]
            compression = ihdr[10]
            filter_method = ihdr[11]
            interlace = ihdr[12]

            color_map = {0: 'Grayscale', 2: 'RGB', 3: 'Indexed', 4: 'Grayscale+Alpha', 6: 'RGBA'}
            interlace_map = {0: 'None', 1: 'Adam7'}

            info['width'] = width
            info['height'] = height
            info['bit_depth'] = bit_depth
            info['color_type'] = color_map.get(color_type, f'Unknown ({color_type})')
            info['color_mode'] = info['color_type']
            info['compression'] = compression
            info['filter_method'] = filter_method
            info['interlace'] = interlace_map.get(interlace, f'Unknown ({interlace})')
    except Exception as e:
        info['error'] = str(e)
    return info


def get_jpeg_info(filepath):
    """Extract metadata from JPEG file."""
    info = {'format': 'JPEG', 'file': filepath}
    try:
        with open(filepath, 'rb') as f:
            header = f.read(2)
            if header != b'\xff\xd8':
                info['error'] = 'Invalid JPEG SOI marker'
                return info

            exif_data = None
            while True:
                marker_bytes = f.read(2)
                if len(marker_bytes) < 2:
                    break

                marker = struct.unpack('>H', marker_bytes)[0]

                if marker == 0xffd9:
                    break

                if marker == 0xffd8:
                    continue

                if marker in (0xff01, 0xffd0, 0xffd1, 0xffd2, 0xffd3, 0xffd4, 0xffd5, 0xffd6, 0xffd7, 0xffd8, 0xffd9):
                    continue

                seg_size_bytes = f.read(2)
                if len(seg_size_bytes) < 2:
                    break
                seg_size = struct.unpack('>H', seg_size_bytes)[0] - 2

                if marker == 0xffe0:
                    data = f.read(seg_size)
                    if data[:5] == b'JFIF\x00':
                        info['jfif_version'] = f"{data[5]}.{data[6]}"
                        info['density'] = f"{struct.unpack('>H', data[7:9])[0]}x{struct.unpack('>H', data[9:11])[0]}"

                elif marker == 0xffe1:
                    data = f.read(seg_size)
                    if data[:6] == b'Exif\x00\x00':
                        exif_data = data[6:]

                elif marker == 0xffc0 or marker == 0xffc1 or marker == 0xffc2:
                    data = f.read(seg_size)
                    precision = data[0]
                    height = struct.unpack('>H', data[1:3])[0]
                    width = struct.unpack('>H', data[3:5])[0]
                    num_components = data[5]
                    info['width'] = width
                    info['height'] = height
                    info['precision'] = precision
                    info['components'] = num_components
                    color_names = {1: 'Grayscale', 3: 'YCbCr (Color)', 4: 'CMYK'}
                    info['color_mode'] = color_names.get(num_components, f'{num_components} components')
                    info['color_type'] = info['color_mode']

                elif marker == 0xffdb:
                    f.read(seg_size)

                elif marker == 0xfffe:
                    data = f.read(seg_size)
                    info['comment'] = data.decode('latin-1', errors='replace')

                else:
                    if seg_size > 0:
                        f.read(seg_size)

            if exif_data:
                exif_info = parse_exif(exif_data)
                if exif_info:
                    info['exif'] = exif_info

    except Exception as e:
        info['error'] = str(e)
    return info


def parse_exif(data):
    """Parse basic EXIF data from JPEG."""
    exif = {}
    try:
        tiff_header = struct.unpack('<H', data[:2])[0]
        if tiff_header == 0x4949:
            byte_order = '<'
        elif tiff_header == 0x4d4d:
            byte_order = '>'
        else:
            return exif

        offset = struct.unpack(byte_order + 'I', data[4:8])[0]
        if offset > len(data) - 2:
            return exif

        num_tags = struct.unpack(byte_order + 'H', data[offset:offset+2])[0]
        offset += 2

        tags = {
            0x010f: 'Make',
            0x0110: 'Model',
            0x0112: 'Orientation',
            0x011a: 'XResolution',
            0x011b: 'YResolution',
            0x0128: 'ResolutionUnit',
            0x0132: 'DateTime',
            0x0213: 'YCbCrPositioning',
            0x8769: 'ExifOffset',
            0x8822: 'ExposureProgram',
            0x829a: 'ExposureTime',
            0x829d: 'FNumber',
            0x920a: 'Flash',
            0x9207: 'MeteringMode',
            0xa002: 'PixelXDimension',
            0xa003: 'PixelYDimension',
        }

        for i in range(min(num_tags, 100)):
            tag_offset = offset + i * 12
            if tag_offset + 12 > len(data):
                break
            tag_id = struct.unpack(byte_order + 'H', data[tag_offset:tag_offset+2])[0]
            tag_type = struct.unpack(byte_order + 'H', data[tag_offset+2:tag_offset+4])[0]
            tag_count = struct.unpack(byte_order + 'I', data[tag_offset+4:tag_offset+8])[0]
            tag_value = data[tag_offset+8:tag_offset+12]

            if tag_id in tags:
                if tag_type == 2:  # ASCII
                    val_offset = struct.unpack(byte_order + 'I', tag_value)[0]
                    if val_offset + tag_count <= len(data):
                        exif[tags[tag_id]] = data[val_offset:val_offset+tag_count-1].decode('latin-1', errors='replace')
                elif tag_type == 3:  # SHORT
                    exif[tags[tag_id]] = struct.unpack(byte_order + 'H', tag_value[:2])[0]
                elif tag_type == 4:  # LONG
                    exif[tags[tag_id]] = struct.unpack(byte_order + 'I', tag_value)[0]
                elif tag_type == 5:  # RATIONAL
                    val_offset = struct.unpack(byte_order + 'I', tag_value)[0]
                    if val_offset + 8 <= len(data):
                        num = struct.unpack(byte_order + 'I', data[val_offset:val_offset+4])[0]
                        den = struct.unpack(byte_order + 'I', data[val_offset+4:val_offset+8])[0]
                        if den:
                            exif[tags[tag_id]] = f"{num}/{den} = {num/den:.4f}"

    except Exception:
        pass
    return exif


def get_gif_info(filepath):
    """Extract metadata from GIF file."""
    info = {'format': 'GIF', 'file': filepath}
    try:
        with open(filepath, 'rb') as f:
            header = f.read(6)
            if header[:3] != b'GIF':
                info['error'] = 'Invalid GIF signature'
                return info

            version = header[3:6].decode('ascii')
            info['version'] = f"GIF{version}"

            lsd = f.read(7)
            width, height = struct.unpack('<HH', lsd[:4])
            packed = lsd[4]
            bg_color = lsd[5]
            aspect_ratio = lsd[6]

            has_gct = (packed >> 7) & 1
            color_res = ((packed >> 4) & 0x07) + 1
            gct_size = 1 << ((packed & 0x07) + 1) if has_gct else 0

            info['width'] = width
            info['height'] = height
            info['color_resolution'] = f"{color_res} bits"
            info['global_color_table'] = has_gct == 1
            info['global_colors'] = gct_size
            info['background_color'] = bg_color
            info['color_mode'] = 'Indexed'
            info['color_type'] = 'Indexed'
    except Exception as e:
        info['error'] = str(e)
    return info


def print_info(info, show_all=True, as_json=False):
    """Print image metadata."""
    if as_json:
        print(json.dumps(info, indent=2, default=str))
        return

    if 'error' in info:
        print(f"\033[91mError: {info['error']}\033[0m", file=sys.stderr)
        return

    print(f"\n\033[1m{info.get('file', '')}\033[0m")
    print(f"  \033[33mFormat:\033[0m    {info.get('format', '?')}")

    if 'width' in info and 'height' in info:
        print(f"  \033[33mDimensions:\033[0m {info['width']} × {info['height']} px")

    if 'color_mode' in info:
        print(f"  \033[33mColor:\033[0m     {info['color_mode']}")

    for key in ['bit_depth', 'precision', 'components', 'version', 'jfif_version',
                'density', 'interlace', 'compression', 'filter_method',
                'color_resolution', 'global_colors']:
        if key in info:
            label = key.replace('_', ' ').title()
            print(f"  \033[33m{label}:\033[0m {info[key]}")

    if 'exif' in info and show_all:
        print(f"\n  \033[1mEXIF Data:\033[0m")
        for exif_key, exif_val in info['exif'].items():
            print(f"    \033[90m{exif_key}:\033[0m {exif_val}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract image metadata (PNG, JPEG, GIF).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  image-meta photo.jpg
  image-meta --all image.png
  image-meta --json image.gif
        """,
    )
    parser.add_argument('file', help='Image file')
    parser.add_argument('--all', '-a', action='store_true', help='Show all metadata including EXIF')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(args.file)[1].lower()

    try:
        if ext in ('.png',):
            info = get_png_info(args.file)
        elif ext in ('.jpg', '.jpeg', '.jpe'):
            info = get_jpeg_info(args.file)
        elif ext in ('.gif',):
            info = get_gif_info(args.file)
        else:
            print(f"Unsupported format: {ext}. Supported: .png, .jpg, .jpeg, .gif", file=sys.stderr)
            sys.exit(1)

        print_info(info, show_all=args.all, as_json=args.json)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)



# === Auto-registration metadata ===
TOOL_META = {
    "name": "image-meta",
    "func": "main",
    "desc": 'Image metadata (EXIF) viewer',
}

if __name__ == '__main__':
    main()

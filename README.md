# Rumi Leaf 3D Model

This project generates a 3D printable STL file of a leaf from an image, using shadows and vein patterns to create realistic surface detail.

## What it does

The Python script (`generate_leaf_stl.py`) converts a 2D leaf image into a 3D model by:
- Converting the image to a height map (darker areas like veins become depressions)
- Enhancing vein structure using edge detection
- Creating a watertight mesh suitable for 3D printing
- Adding a flat base for print stability

## Usage

```bash
uv run python generate_leaf_stl.py
```

This generates `rumi-leaf.stl` from `green-leaf.png`.

## Output

- **Mesh**: 141K vertices, 283K triangles
- **Watertight**: Yes
- **Default size**: 100mm × 100mm × ~5mm
- **Base thickness**: 1mm

## Customization

Edit the parameters in `generate_leaf_stl.py`:
- `scale_xy`: Overall size in mm (default: 100.0)
- `scale_z`: Height variation in mm (default: 5.0)
- `base_thickness`: Base thickness in mm (default: 1.0)

## Dependencies

All dependencies are managed via `uv`:
- PIL (Pillow) - Image processing
- NumPy - Numerical operations
- SciPy - Image filtering and enhancement
- Trimesh - 3D mesh operations

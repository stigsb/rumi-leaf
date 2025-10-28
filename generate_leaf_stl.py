#!/usr/bin/env python3
"""
Simple watertight leaf mesh generator.
Creates a rectangular base with modulated top surface.
"""

import numpy as np
from PIL import Image
import scipy.ndimage as ndimage
import trimesh

def load_and_process_image(image_path):
    """Load image and convert to grayscale height map."""
    img = Image.open(image_path).convert('RGBA')
    img_array = np.array(img)
    alpha = img_array[:, :, 3] / 255.0

    # Convert to grayscale
    rgb = img_array[:, :, :3]
    gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    gray = gray / 255.0

    # Invert so veins are lower
    height_map = 1.0 - gray
    height_map *= alpha

    return height_map, alpha

def enhance_veins(height_map, alpha):
    """Enhance vein structure."""
    # Increased smoothing for a smoother surface
    smoothed = ndimage.gaussian_filter(height_map, sigma=3.5)
    grad_x = ndimage.sobel(smoothed, axis=1)
    grad_y = ndimage.sobel(smoothed, axis=0)
    gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
    gradient_magnitude = gradient_magnitude / gradient_magnitude.max()
    # Reduced vein depth for smoother appearance
    enhanced = height_map - gradient_magnitude * 0.2
    enhanced *= alpha
    # Additional smoothing pass
    enhanced = ndimage.gaussian_filter(enhanced, sigma=1.5)
    enhanced *= alpha
    return enhanced

def create_watertight_mesh(height_map, alpha, scale_xy=100.0, scale_z=3.5, base_thickness=1.0):
    """Create a watertight mesh only for the leaf shape (no background square)."""
    h, w = height_map.shape

    # Downsample
    step = 3
    h_small, w_small = h // step, w // step

    # Alpha threshold to determine if a cell is part of the leaf
    alpha_threshold = 0.3

    # Create downsampled alpha map
    alpha_small = np.zeros((h_small, w_small))
    for i in range(h_small):
        for j in range(w_small):
            orig_i = min(i * step, h - 1)
            orig_j = min(j * step, w - 1)
            alpha_small[i, j] = alpha[orig_i, orig_j]

    # Calculate scales
    dx = scale_xy / w_small
    dy = scale_xy / h_small

    # Create vertices only for points that are part of the leaf
    vertices = []
    vertex_idx = {}

    for i in range(h_small):
        for j in range(w_small):
            if alpha_small[i, j] > alpha_threshold:
                # Map to original image coordinates
                orig_i = min(i * step, h - 1)
                orig_j = min(j * step, w - 1)

                # Position
                x = (j - w_small/2) * dx
                y = (i - h_small/2) * dy
                z_top = height_map[orig_i, orig_j] * scale_z

                # Store top vertex
                top_idx = len(vertices)
                vertices.append([x, y, z_top])
                vertex_idx[(i, j, 'top')] = top_idx

                # Store bottom vertex
                bottom_idx = len(vertices)
                vertices.append([x, y, -base_thickness])
                vertex_idx[(i, j, 'bottom')] = bottom_idx

    faces = []

    # Helper to check if a cell should have geometry
    def is_leaf_cell(i, j):
        return (i >= 0 and i < h_small and j >= 0 and j < w_small and
                alpha_small[i, j] > alpha_threshold)

    # Create faces only where all 4 corners are part of the leaf
    for i in range(h_small - 1):
        for j in range(w_small - 1):
            # Check if all 4 corners exist
            if (is_leaf_cell(i, j) and is_leaf_cell(i, j+1) and
                is_leaf_cell(i+1, j) and is_leaf_cell(i+1, j+1)):

                # Get all 8 vertices (4 top, 4 bottom)
                v00_t = vertex_idx[(i, j, 'top')]
                v01_t = vertex_idx[(i, j+1, 'top')]
                v10_t = vertex_idx[(i+1, j, 'top')]
                v11_t = vertex_idx[(i+1, j+1, 'top')]

                v00_b = vertex_idx[(i, j, 'bottom')]
                v01_b = vertex_idx[(i, j+1, 'bottom')]
                v10_b = vertex_idx[(i+1, j, 'bottom')]
                v11_b = vertex_idx[(i+1, j+1, 'bottom')]

                # Top surface (2 triangles)
                faces.append([v00_t, v01_t, v11_t])
                faces.append([v00_t, v11_t, v10_t])

                # Bottom surface (2 triangles, reversed)
                faces.append([v00_b, v11_b, v01_b])
                faces.append([v00_b, v10_b, v11_b])

    # Create edge walls by checking each quad's edges
    for i in range(h_small - 1):
        for j in range(w_small - 1):
            curr_quad = (is_leaf_cell(i, j) and is_leaf_cell(i, j+1) and
                        is_leaf_cell(i+1, j) and is_leaf_cell(i+1, j+1))

            if not curr_quad:
                continue

            # Get vertex indices for this quad
            v00_t = vertex_idx[(i, j, 'top')]
            v01_t = vertex_idx[(i, j+1, 'top')]
            v10_t = vertex_idx[(i+1, j, 'top')]
            v11_t = vertex_idx[(i+1, j+1, 'top')]

            v00_b = vertex_idx[(i, j, 'bottom')]
            v01_b = vertex_idx[(i, j+1, 'bottom')]
            v10_b = vertex_idx[(i+1, j, 'bottom')]
            v11_b = vertex_idx[(i+1, j+1, 'bottom')]

            # Check each edge and add wall if it's a boundary
            # Top edge (i, j) -> (i, j+1)
            if i == 0 or not (is_leaf_cell(i-1, j) and is_leaf_cell(i-1, j+1)):
                faces.append([v00_b, v01_t, v00_t])
                faces.append([v00_b, v01_b, v01_t])

            # Bottom edge (i+1, j) -> (i+1, j+1)
            if i == h_small - 2 or not (is_leaf_cell(i+2, j) and is_leaf_cell(i+2, j+1)):
                faces.append([v10_b, v10_t, v11_t])
                faces.append([v10_b, v11_t, v11_b])

            # Left edge (i, j) -> (i+1, j)
            if j == 0 or not (is_leaf_cell(i, j-1) and is_leaf_cell(i+1, j-1)):
                faces.append([v00_b, v10_t, v00_t])
                faces.append([v00_b, v10_b, v10_t])

            # Right edge (i, j+1) -> (i+1, j+1)
            if j == w_small - 2 or not (is_leaf_cell(i, j+2) and is_leaf_cell(i+1, j+2)):
                faces.append([v01_b, v01_t, v11_t])
                faces.append([v01_b, v11_t, v11_b])

    vertices = np.array(vertices)
    faces = np.array(faces)

    # Create mesh
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    # Fill any holes to ensure watertightness
    if not mesh.is_watertight:
        trimesh.repair.fill_holes(mesh)

    return mesh

def main():
    input_image = 'green-leaf.png'
    output_stl = 'rumi-leaf.stl'

    print(f"Loading image: {input_image}")
    height_map, alpha = load_and_process_image(input_image)

    print("Enhancing vein structure...")
    enhanced_map = enhance_veins(height_map, alpha)

    print("Generating watertight 3D mesh...")
    leaf_mesh = create_watertight_mesh(
        enhanced_map,
        alpha,
        scale_xy=100.0,
        scale_z=3.5,
        base_thickness=1.0
    )

    print(f"Mesh: {len(leaf_mesh.vertices)} vertices, {len(leaf_mesh.faces)} faces")
    print(f"Watertight: {leaf_mesh.is_watertight}")
    print(f"Bounds: {leaf_mesh.bounds}")

    print(f"Exporting to {output_stl}...")
    leaf_mesh.export(output_stl)

    print("Done!")

if __name__ == '__main__':
    main()

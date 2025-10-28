#!/usr/bin/env python3
"""
Disc Floret Generator

Creates a 3D model of a flower disc floret with individual florets arranged
in a Vogel spiral pattern (golden angle), mimicking natural flower centers.

Can be used as a standalone script or imported as a module.
"""

import argparse
import numpy as np
import trimesh


def create_floret_bump(radius=0.5, height=1.0, resolution=8):
    """
    Create a single floret bump (small sphere/cone hybrid).

    Args:
        radius: Base radius of the bump
        height: Height of the bump
        resolution: Number of segments in the bump

    Returns:
        A trimesh object representing a single floret
    """
    # Create a small sphere for the bump
    sphere = trimesh.creation.icosphere(subdivisions=1, radius=radius)

    # Scale it to be more elongated (taller)
    sphere.apply_scale([1.0, 1.0, height / radius])

    return sphere


def create_convex_disc(radius, base_height, convexity=0.5, radial_segments=8, angular_segments=32):
    """
    Create a convex disc base with a curved surface.

    Args:
        radius: Radius of the disc
        base_height: Height of the disc at the edges
        convexity: Height of the convex curve (0.0 = flat, 1.0 = very convex)
        radial_segments: Number of segments from center to edge
        angular_segments: Number of segments around the circle

    Returns:
        A trimesh object representing the convex disc
    """
    # Start with a cylinder and modify it to be convex
    mesh = trimesh.creation.cylinder(
        radius=radius,
        height=base_height,
        sections=angular_segments
    )

    # Move it so bottom is at z=0
    mesh.apply_translation([0, 0, base_height / 2])

    # Modify vertices to create convex top surface
    vertices = mesh.vertices.copy()

    for i, v in enumerate(vertices):
        x, y, z = v
        r = np.sqrt(x*x + y*y)

        # Only modify top surface vertices
        if z > base_height * 0.99:
            # Calculate convex height based on distance from center
            t = r / radius
            # Parabolic curve: higher at center, lower at edges
            height_multiplier = 1 + convexity * (1 - t * t)
            vertices[i, 2] = base_height * height_multiplier

    mesh.vertices = vertices

    return mesh


def create_disc_floret_mesh(diameter_mm=20.0, base_height=1.0, floret_density=1.0):
    """
    Create a disc floret mesh with individual florets arranged in a spiral pattern.

    Args:
        diameter_mm: Diameter of the disc floret in millimeters (default 20mm = 2cm)
        base_height: Height of the base disc in millimeters
        floret_density: Density multiplier for florets (1.0 = normal, higher = more florets)

    Returns:
        A trimesh object representing the complete disc floret
    """
    radius = diameter_mm / 2.0

    # Golden angle in radians (137.5 degrees)
    # This creates the characteristic spiral pattern seen in nature
    golden_angle = np.pi * (3 - np.sqrt(5))

    # Calculate number of florets based on area and density
    # Increased density for more packed appearance
    area = np.pi * radius * radius
    num_florets = int(area * floret_density * 2.5)

    print(f"Creating disc floret: {diameter_mm}mm diameter, {num_florets} individual florets")

    # Create convex base disc
    convexity = 0.5  # 50% height boost at center
    base = create_convex_disc(radius, base_height, convexity=convexity)

    # Calculate floret size based on disc size
    # Smaller florets for smaller discs, larger for bigger discs
    floret_radius = radius / 25.0
    floret_height = floret_radius * 1.5

    # Create individual florets using Vogel's spiral
    florets = []
    for i in range(num_florets):
        # Vogel's method for evenly distributing points on a disc
        theta = i * golden_angle
        # Use sqrt for even area distribution
        r = radius * 0.9 * np.sqrt(i / num_florets)

        # Add organic variation to position
        position_jitter = floret_radius * 0.4
        x = r * np.cos(theta) + np.random.uniform(-position_jitter, position_jitter)
        y = r * np.sin(theta) + np.random.uniform(-position_jitter, position_jitter)

        # Create floret bump
        floret = create_floret_bump(floret_radius, floret_height)

        # Add organic variation in size (xy) and height (z)
        size_variation = np.random.uniform(0.7, 1.3)
        height_variation = np.random.uniform(0.6, 1.4)
        floret.apply_scale([size_variation, size_variation, height_variation])

        # Add slight random rotation for more organic look
        rotation_angle = np.random.uniform(0, 2 * np.pi)
        rotation_matrix = trimesh.transformations.rotation_matrix(
            rotation_angle, [0, 0, 1]
        )
        floret.apply_transform(rotation_matrix)

        # Position the floret on the convex surface
        # Calculate z based on distance from center (parabolic curve)
        t = r / radius
        z = base_height * (1 + convexity * (1 - t * t))
        floret.apply_translation([x, y, z])

        florets.append(floret)

    # Combine all meshes
    print("Combining all components...")
    all_meshes = [base] + florets
    disc_floret = trimesh.util.concatenate(all_meshes)

    print(f"Disc floret: {len(disc_floret.vertices)} vertices, {len(disc_floret.faces)} faces")

    return disc_floret


def main():
    """Main function for standalone usage."""
    parser = argparse.ArgumentParser(
        description='Generate a disc floret with spiral-arranged bumps'
    )
    parser.add_argument(
        '--diameter',
        type=float,
        default=20.0,
        help='Diameter of the disc floret in millimeters (default: 20mm = 2cm)'
    )
    parser.add_argument(
        '--base-height',
        type=float,
        default=1.0,
        help='Height of the base disc in millimeters (default: 1.0mm)'
    )
    parser.add_argument(
        '--density',
        type=float,
        default=1.0,
        help='Floret density multiplier (default: 1.0)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='disc-floret.stl',
        help='Output STL file (default: disc-floret.stl)'
    )

    args = parser.parse_args()

    # Create the disc floret
    disc_floret = create_disc_floret_mesh(
        diameter_mm=args.diameter,
        base_height=args.base_height,
        floret_density=args.density
    )

    # Export to STL
    print(f"Exporting to {args.output}...")
    disc_floret.export(args.output)

    print("Done!")


if __name__ == '__main__':
    main()

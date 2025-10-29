#!/usr/bin/env python3
"""
Test for generate_medallion_stl.py

Validates that the script runs successfully and produces a valid STL file.
"""

import os
import subprocess
import tempfile
import pytest
import trimesh


def test_generate_medallion_default():
    """Test generating a medallion with default parameters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test_medallion.stl")

        # Run the script
        result = subprocess.run(
            ["python", "generate_medallion_stl.py", "--output", output_file],
            capture_output=True,
            text=True
        )

        # Check the script ran successfully
        assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"

        # Check the output file exists
        assert os.path.exists(output_file), "Output STL file was not created"

        # Load the STL file with trimesh to validate it
        mesh = trimesh.load(output_file)

        # Basic validation checks
        assert mesh is not None, "Failed to load STL file"
        assert len(mesh.vertices) > 0, "Mesh has no vertices"
        assert len(mesh.faces) > 0, "Mesh has no faces"

        # Check that the mesh has reasonable dimensions (5cm diameter = 50mm)
        bounds = mesh.bounds
        extents = mesh.extents

        # Diameter should be approximately 50mm
        max_dimension = max(extents[0], extents[1])
        assert 45 < max_dimension < 55, f"Medallion dimension {max_dimension}mm is not close to expected 50mm"

        # Thickness should be approximately 50/20 = 2.5mm base + convexity (1.5mm) + ridges + leaves
        thickness = extents[2]
        assert 2.0 < thickness < 10.0, f"Medallion thickness {thickness}mm seems incorrect"

        print(f"✓ Default medallion test passed")
        print(f"  Vertices: {len(mesh.vertices)}")
        print(f"  Faces: {len(mesh.faces)}")
        print(f"  Dimensions: {extents[0]:.2f} x {extents[1]:.2f} x {extents[2]:.2f} mm")
        print(f"  Watertight: {mesh.is_watertight}")


def test_generate_medallion_custom_size():
    """Test generating a medallion with custom diameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test_medallion_80mm.stl")

        # Run the script with 80mm diameter
        result = subprocess.run(
            ["python", "generate_medallion_stl.py", "--diameter", "80", "--output", output_file],
            capture_output=True,
            text=True
        )

        # Check the script ran successfully
        assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"

        # Check the output file exists
        assert os.path.exists(output_file), "Output STL file was not created"

        # Load and validate the STL file
        mesh = trimesh.load(output_file)

        assert mesh is not None, "Failed to load STL file"
        assert len(mesh.vertices) > 0, "Mesh has no vertices"
        assert len(mesh.faces) > 0, "Mesh has no faces"

        # Check dimensions for 80mm medallion
        extents = mesh.extents
        max_dimension = max(extents[0], extents[1])
        assert 75 < max_dimension < 85, f"Medallion dimension {max_dimension}mm is not close to expected 80mm"

        # Thickness should be approximately 80/20 = 4mm base + convexity (2.4mm) + ridges + leaves
        thickness = extents[2]
        assert 3.0 < thickness < 15.0, f"Medallion thickness {thickness}mm seems incorrect"

        print(f"✓ Custom size medallion test passed")
        print(f"  Vertices: {len(mesh.vertices)}")
        print(f"  Faces: {len(mesh.faces)}")
        print(f"  Dimensions: {extents[0]:.2f} x {extents[1]:.2f} x {extents[2]:.2f} mm")


def test_stl_file_format():
    """Test that the output is a properly formatted STL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test_format.stl")

        # Run the script
        result = subprocess.run(
            ["python", "generate_medallion_stl.py", "--output", output_file],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check file is not empty
        file_size = os.path.getsize(output_file)
        assert file_size > 0, "STL file is empty"

        # Try to read it as binary STL
        with open(output_file, 'rb') as f:
            header = f.read(80)
            assert len(header) == 80, "Invalid STL header"

        # Load with trimesh and check mesh properties
        mesh = trimesh.load(output_file)

        # Check that normals exist and are valid
        assert mesh.face_normals is not None, "Mesh has no face normals"
        assert len(mesh.face_normals) == len(mesh.faces), "Face normals count mismatch"

        print(f"✓ STL format test passed")
        print(f"  File size: {file_size} bytes")


if __name__ == '__main__':
    # Allow running tests directly
    pytest.main([__file__, '-v'])

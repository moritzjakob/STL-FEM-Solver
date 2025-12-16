# -----------------------------------------------------------------------------
# Mesh Generator Utility
# -----------------------------------------------------------------------------
# Description:
#   This module provides the MeshGenerator class, which is responsible for:
#     - Validating and loading STL geometry files
#     - Creating a 3D tetrahedral mesh using Gmsh
#     - Converting the mesh to a FeniCS-compatible format
#     - Evaluating mesh quality and saving a structured report
# -----------------------------------------------------------------------------

import os
import json
import tempfile
import logging
from typing import Optional

import gmsh
import meshio
import numpy as np


class MeshGenerator:
    """
    MeshGenerator
    -------------
    A utility class for generating and evaluating 3D tetrahedral meshes
    from STL geometry files using Gmsh and MeshIO.

    Main responsibilities:
        - STL file validation
        - 3D mesh generation
        - Mesh quality evaluation
        - Conversion to FeniCS-compatible format
    """

    def __init__(self) -> None:
        """
        Initialize the MeshGenerator instance.

        Sets up an internal logger for reporting mesh generation
        and quality evaluation steps.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MeshGenerator initialized")

    # -------------------------------------------------------------------------
    def generate_mesh_with_gmsh(
        self,
        stl_file: str,
        output_dir: str,
        element_size: Optional[float] = None
    ):
        """
        Generate a 3D tetrahedral mesh from an STL file using Gmsh.

        This method:
          - Validates the STL file
          - Initializes Gmsh and imports the STL geometry
          - Optionally sets a global element size
          - Creates a surface loop and volume
          - Generates and optimizes a 3D mesh
          - Evaluates mesh quality
          - Converts the mesh to a FeniCS-compatible MeshIO object

        Args:
            stl_file (str): Path to the STL file.
            output_dir (str): Directory to save quality reports and output files.
            element_size (float, optional): Target element size in mesh (uniform).

        Returns:
            meshio.Mesh: A MeshIO mesh object containing nodes and tetrahedral cells.

        Raises:
            FileNotFoundError: If the STL file does not exist.
            ValueError: If the file is not an STL file.
            RuntimeError: If mesh generation fails.
        """
        self.logger.info(f"Generating mesh from STL file: {stl_file}")

        # Validate input and output paths
        self._validate_stl_file(stl_file)
        self._ensure_output_dir(output_dir)

        gmsh.initialize()
        gmsh.option.setNumber("Geometry.Tolerance", 1e-6)  # Better merging tolerance

        try:
            # Load STL file into Gmsh
            gmsh.merge(stl_file)
            self.logger.debug(f"STL merged successfully: {stl_file}")

            # Optional global element size
            if element_size is not None:
                gmsh.option.setNumber("Mesh.CharacteristicLengthMin", element_size)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", element_size)
                self.logger.debug(f"Element size set to: {element_size}")

            # Define surface loop and volume
            surfaces = gmsh.model.getEntities(2)
            surface_ids = [s[1] for s in surfaces]
            if len(surface_ids) > 0:
                loop = gmsh.model.geo.addSurfaceLoop(surface_ids)
                gmsh.model.geo.addVolume([loop])
                gmsh.model.geo.synchronize()
                self.logger.debug(f"Surface loop created with {len(surface_ids)} surfaces")

            # Mesh generation
            gmsh.model.mesh.generate(3)
            self.logger.info("Gmsh mesh generation completed")

            # Optional mesh optimization
            gmsh.model.mesh.optimize("Netgen")
            self.logger.debug("Netgen optimization applied")

            # Mesh quality evaluation
            self._evaluate_mesh_quality_with_gmsh(stl_file, output_dir)

            # Export to temporary .msh and read with MeshIO
            with tempfile.NamedTemporaryFile(suffix=".msh", delete=False) as temp_msh:
                gmsh.write(temp_msh.name)
                mesh = meshio.read(temp_msh.name)

        except Exception as e:
            self.logger.error(f"Mesh generation failed: {e}")
            raise RuntimeError(f"Mesh generation failed: {e}") from e

        finally:
            gmsh.finalize()

        self.logger.info(f"Mesh generated successfully with {len(mesh.points)} points")
        return mesh

    # -------------------------------------------------------------------------
    def _validate_stl_file(self, stl_file: str) -> None:
        """
        Validate STL file existence and extension.

        Args:
            stl_file (str): Path to the STL file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file does not have a .stl extension.
        """
        if not os.path.isfile(stl_file):
            self.logger.error(f"STL file not found: {stl_file}")
            raise FileNotFoundError(f"STL file not found: {stl_file}")
        if not stl_file.lower().endswith(".stl"):
            self.logger.error(f"Invalid file format: {stl_file}")
            raise ValueError(f"File must be .stl, got: {stl_file}")

        self.logger.debug(f"STL file validated: {stl_file}")

    # -------------------------------------------------------------------------
    def _ensure_output_dir(self, output_dir: str) -> None:
        """
        Ensure that the output directory exists or create it.

        Args:
            output_dir (str): Path to the output directory.
        """
        os.makedirs(output_dir, exist_ok=True)
        self.logger.debug(f"Output directory ready: {output_dir}")

    # -------------------------------------------------------------------------
    def _evaluate_mesh_quality_with_gmsh(
        self,
        file_name: str,
        output_dir: Optional[str] = None
    ) -> None:
        """
        Evaluate the quality of the generated mesh and save a JSON report.

        Evaluated metrics:
            - Element quality statistics
            - Quality histogram (0.0–1.0)
            - Aspect ratio for tetrahedral elements
            - Counts of illegal and low-quality elements

        Args:
            file_name (str): Original STL file name.
            output_dir (str, optional): Output directory to save the report.

        Raises:
            OSError: If writing the report fails.
        """
        self.logger.info("Evaluating mesh quality")

        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)
        qualities = []

        # Collect element qualities
        for etype, tags, _ in zip(elem_types, elem_tags, elem_node_tags):
            if len(tags) > 0:
                q = gmsh.model.mesh.getElementQualities(tags)
                qualities.extend(q)

        qualities = np.array(qualities)
        num_elements = len(qualities)
        avg_quality = float(np.mean(qualities)) if num_elements > 0 else 0.0
        min_quality = float(np.min(qualities)) if num_elements > 0 else 0.0
        max_quality = float(np.max(qualities)) if num_elements > 0 else 0.0
        illegal_elements = int(np.sum(qualities <= 0))
        low_quality_elements = int(np.sum(qualities < 0.2))

        self.logger.debug(
            f"Mesh quality stats - elements: {num_elements}, "
            f"avg: {avg_quality}, min: {min_quality}, max: {max_quality}"
        )

        # Build quality histogram
        bins = np.linspace(0, 1, 11)
        hist, _ = np.histogram(qualities, bins=bins)
        histogram_data = {
            f"{bins[i]:.1f}-{bins[i+1]:.1f}": int(hist[i]) for i in range(len(hist))
        }

        # Calculate aspect ratios for tetrahedra
        node_coords = np.array(gmsh.model.mesh.getNodes()[1]).reshape(-1, 3)
        aspect_ratios = []

        for etype, nodes_list in zip(elem_types, elem_node_tags):
            if etype == 4:  # Tetrahedra
                nodes_array = np.array(nodes_list, dtype=int).reshape(-1, 4)
                for nodes in nodes_array:
                    idx = nodes - 1
                    A, B, C, D = node_coords[idx]

                    edges = np.array([
                        np.linalg.norm(A - B),
                        np.linalg.norm(A - C),
                        np.linalg.norm(A - D),
                        np.linalg.norm(B - C),
                        np.linalg.norm(B - D),
                        np.linalg.norm(C - D),
                    ])
                    min_edge = np.min(edges)
                    if min_edge > 1e-12:
                        aspect_ratios.append(float(np.max(edges) / min_edge))
                    else:
                        aspect_ratios.append(np.inf)

        avg_aspect = float(np.mean(aspect_ratios)) if aspect_ratios else None
        max_aspect = float(np.max(aspect_ratios)) if aspect_ratios else None

        self.logger.debug(
            f"Aspect ratio stats - avg: {avg_aspect}, max: {max_aspect}"
        )

        # Assemble quality report
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        report = {
            "file": base_name,
            "num_elements": num_elements,
            "average_quality": avg_quality,
            "min_quality": min_quality,
            "max_quality": max_quality,
            "illegal_elements": illegal_elements,
            "low_quality_elements": low_quality_elements,
            "quality_histogram": histogram_data,
            "average_aspect_ratio": avg_aspect,
            "max_aspect_ratio": max_aspect,
        }

        report_path = os.path.join(output_dir, f"{base_name}_mesh_quality.json")
        try:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=4)
            self.logger.info(f"Mesh quality report saved: {report_path}")
        except OSError as e:
            self.logger.error(f"Failed to save mesh quality report: {e}")
            raise



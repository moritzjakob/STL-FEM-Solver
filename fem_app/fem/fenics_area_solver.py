# -----------------------------------------------------------------------------
# FEM Area Solver
# -----------------------------------------------------------------------------
# Description:
#   This module provides the FEMAreaSolver class, which extends FEMBaseSolver
#   to support FEM analyses with area-based loads. It is responsible for:
#     - Marking facets corresponding to the loaded area
#     - Applying traction loads on these facets
#     - Applying Dirichlet boundary conditions
#     - Solving the variational problem
#     - Computing postprocessing and validation data specific to area loads
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
import os

import dolfin as do
import numpy as np

from fem_app.fem.fem_base import FEMBaseSolver


class FEMAreaSolver(FEMBaseSolver):
    """
    FEM solver for area-based loading problems.

    Extends FEMBaseSolver to:
        - Mark area facets based on user-selected geometry.
        - Apply distributed traction loads on these facets.
        - Define Dirichlet boundary conditions on a plane.
        - Assemble and solve the FEM system.
        - Compute validation and verification data.

    Attributes:
        area_markers (do.MeshFunction):
            MeshFunction marking the facets subjected to area loads.
        dirichlet_markers (do.MeshFunction):
            MeshFunction marking boundary facets for Dirichlet BCs.
    """

    def __init__(self) -> None:
        """
        Initialize the area load solver and logger.
        """
        super().__init__()
        self.area_markers: do.MeshFunction | None = None
        self.dirichlet_markers: do.MeshFunction | None = None

        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEMAreaSolver initialized")

    # -------------------------------------------------------------------------
    def generate_and_solve(
        self,
        file_name: str,
        area_facet_vertices: list[list[tuple[float, float, float]]],
        material: str,
        selected_boundary_point: float,
        selected_axis: str,
        boundary_direction: str,
        force_value: float,
        force_direction: tuple[float, float, float],
    ) -> str:
        """
        Full FEM solve workflow for an area-load problem.

        Steps:
            1. Prepare output directory
            2. Generate mesh
            3. Setup function space
            4. Mark loaded area facets
            5. Apply Dirichlet boundary conditions
            6. Apply area loads
            7. Setup material
            8. Define variational problem and assemble system
            9. Solve linear system
            10. Compute postprocessing and validation data
            11. Write output files

        Args:
            file_name: Path to the STL geometry file.
            area_facet_vertices: Vertex coordinates of target loaded facets.
            material: Material name (must be supported by base solver).
            selected_boundary_point: Coordinate of boundary plane for BCs.
            selected_axis: Axis name ("X", "Y", or "Z").
            boundary_direction: "<" or ">" relative position for BC plane.
            force_value: Magnitude of applied traction force.
            force_direction: Force vector direction components.

        Returns:
            str: Path to the generated XDMF output file.

        Raises:
            ValueError: If invalid axis or force direction is provided.
        """
        self.logger.info(f"Starting area-load FEM solve for file: {file_name}")

        self._prepare_output_folder(file_name, "area_load")
        self._generate_mesh(file_name)
        self._setup_function_space()
        self._mark_area_facets(area_facet_vertices)
        self._apply_boundary_conditions(selected_boundary_point, selected_axis, boundary_direction)
        self._apply_area_loads(force_value, force_direction)
        self._setup_material(material)
        self._define_variational_problem()
        self._assemble_system()
        self._solve_linear_system()
        self._compute_postprocessing()
        self._compute_validation_data(
            material,
            selected_boundary_point,
            selected_axis,
            boundary_direction,
            force_value,
            force_direction,
        )
        xdmf_path = self._write_output_files()
        self.logger.info(f"Area-load FEM solve completed. Results written to: {xdmf_path}")
        return xdmf_path

    # -------------------------------------------------------------------------
    def _mark_area_facets(self, area_facet_vertices: list[list[tuple[float, float, float]]]) -> None:
        """
        Mark mesh facets that correspond to the loaded area.

        Uses coordinate matching with a small tolerance. Each facet is compared
        to a set of target facet vertices.

        Args:
            area_facet_vertices: list of facet vertex coordinate sets.

        Raises:
            RuntimeError: If the mesh is not initialized.
        """
        if self.fenics_mesh is None:
            raise RuntimeError("FEniCS mesh not initialized. Call _generate_mesh() first.")

        self.logger.debug("Marking area facets")

        def facet_matches(facet: do.Facet, mesh: do.Mesh, targets: list) -> bool:
            vertices = facet.entities(0)
            facet_coords = [mesh.coordinates()[v] for v in vertices]
            facet_coords_sorted = sorted([tuple(np.round(coord, 6)) for coord in facet_coords])
            for target_facet in targets:
                target_sorted = sorted([tuple(np.round(coord, 6)) for coord in target_facet])
                if facet_coords_sorted == target_sorted:
                    return True
            return False

        self.area_markers = do.MeshFunction(
            "size_t", self.fenics_mesh, self.fenics_mesh.topology().dim() - 1
        )
        self.area_markers.set_all(0)

        count = 0
        for facet in do.facets(self.fenics_mesh):
            if facet_matches(facet, self.fenics_mesh, area_facet_vertices):
                self.area_markers[facet] = 1
                count += 1
                self.logger.debug(
                    f"Marked facet {facet.index()} with vertices: "
                    f"{[self.fenics_mesh.coordinates()[v] for v in facet.entities(0)]}"
                )
        self.ds_area = do.Measure("ds", domain=self.fenics_mesh, subdomain_data=self.area_markers)
        self.logger.debug("Created ds_area measure for loaded facets")
        self.logger.info(f"Marked {count} facet(s) for area loading")

    # -------------------------------------------------------------------------
   
    def _apply_boundary_conditions(
    self,
    selected_boundary_point: float,
    selected_axis: str,
    boundary_direction: str,
    ) -> None:
        """
        Apply Dirichlet BCs and mark the same facets for reaction-force integration.
        Works for arbitrary geometries (planes, curved surfaces, etc.).
        """

        if self.fenics_mesh is None or self.V is None:
            raise RuntimeError("Mesh or function space not initialized.")

        mesh = self.fenics_mesh
        dim = mesh.topology().dim()
        tol = 1e-6  # adaptive tolerance ~half the smallest element size

        self.logger.debug(
            f"Applying boundary conditions: {selected_axis}={selected_boundary_point}, direction={boundary_direction}"
        )

        # Define subdomain: only the plane at selected coordinate
        class BoundaryPlane(do.SubDomain):
            def inside(self, x, on_boundary):
                if not on_boundary:
                    return False
                if selected_axis == "X":
                    return do.near(x[0], selected_boundary_point, tol)
                elif selected_axis == "Y":
                    return do.near(x[1], selected_boundary_point, tol)
                elif selected_axis == "Z":
                    return do.near(x[2], selected_boundary_point, tol)
                else:
                    raise ValueError(f"Invalid axis: {selected_axis}")

        subdomain = BoundaryPlane()

        # Apply the actual Dirichlet BC
        bc = do.DirichletBC(self.V, do.Constant((0.0, 0.0, 0.0)), subdomain)
        self.boundary_conditions = [bc]

        # Mark the same facets used by the BC
        self.dirichlet_markers = do.MeshFunction("size_t", mesh, dim - 1, 0)
        for facet in do.facets(mesh):
            vs = facet.entities(0)
            coords = mesh.coordinates()[vs]
            # require all vertices lie on the subdomain surface
            if all(subdomain.inside(c, True) for c in coords):
                self.dirichlet_markers[facet] = 1

        n_marked = int(np.sum(self.dirichlet_markers.array()))
        if n_marked == 0:
            self.logger.warning("No boundary facets marked for Dirichlet conditions.")
        else:
            self.logger.info(f"{n_marked} facet(s) marked for Dirichlet BC and reaction computation.")

        # Define the ds measure for later integration
        self.ds_dirichlet = do.Measure("ds", domain=mesh, subdomain_data=self.dirichlet_markers)

    # -------------------------------------------------------------------------
    def _assemble_system(self) -> None:
        """
        Assemble the FEM linear system Ax = b with boundary conditions applied.
        """
        if self.a is None or self.L is None:
            raise RuntimeError("Variational problem not defined. Call _define_variational_problem() first.")

        self.logger.debug("Assembling FEM system (A, b)")
        self.A, self.b = do.assemble_system(self.a, self.L, self.boundary_conditions)
        self.logger.info("System assembly completed")

    # -------------------------------------------------------------------------
    def _apply_area_loads(self, force_value: float, force_direction: tuple[float, float, float]) -> None:
        """
        Apply traction load to marked area facets.

        If a total force is specified, this is converted to a uniform traction per unit area
        over all marked facets.

        Args:
            force_value: Magnitude of the applied total force (not per unit area).
            force_direction: 3D direction vector of the force.

        Raises:
            ValueError: If force_direction is zero-length or no area is marked.
        """
        self.logger.debug(f"Applying area load: total force value={force_value}, direction={force_direction}")

        # 1. Compute total loaded area of all facets marked with 1 in self.area_markers.
        if self.area_markers is None:
            self.logger.error("Area markers not initialized. Call _mark_area_facets first.")
            raise RuntimeError("Area markers not initialized.")

        mesh = self.fenics_mesh
        if mesh is None:
            self.logger.error("Mesh not initialized.")
            raise RuntimeError("Mesh not initialized.")

        total_area = 0.0
        marked_facets = []
        for facet in do.facets(mesh):
            if self.area_markers[facet.index()] == 1:
                # Robust area computation
                try:
                    area = facet.measure()
                except AttributeError:
                    vertices = facet.entities(0)
                    coords = self.fenics_mesh.coordinates()[vertices]
                    v1, v2, v3 = coords
                    area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1))
                total_area += area
                marked_facets.append(facet.index())

        if total_area == 0.0:
            self.logger.error("No area is marked for loading. Cannot apply area load.")
            raise ValueError("No area is marked for loading. Cannot apply area load.")

        # 2. Normalize the input force_direction.
        dir_len = np.linalg.norm(force_direction)
        if dir_len == 0:
            self.logger.error("Force direction vector cannot be zero")
            raise ValueError("Force direction vector cannot be zero")
        normalized_dir = [d / dir_len for d in force_direction]

        # 3. Convert force_value (total force) to traction magnitude by dividing by total area.
        traction_magnitude = force_value / total_area

        # 4. Multiply the traction magnitude by the normalized direction vector to get traction vector.
        traction_vector = [traction_magnitude * d for d in normalized_dir]

        # 5. Set self.f_vec to that vector as a dolfin.Constant.
        self.f_vec = do.Constant(tuple(traction_vector))

        self.logger.warning(
            f"Area load applied: total force = {force_value}, "
            f"total loaded area = {total_area}, "
            f"traction vector = {traction_vector}, "
            f"marked facets = {marked_facets}"
        )

    # -------------------------------------------------------------------------
    def _compute_validation_data(
        self,
        material: str,
        selected_boundary_point: float,
        selected_axis: str,
        boundary_direction: str,
        force_value: float,
        force_direction: tuple[float, float, float],
    ) -> None:
        """
        Compute and save additional validation data for area load simulations.

        Data includes:
            - Total strain energy
            - Displacement extremes
            - Max Von Mises stress
            - Facet loads
            - Solver log

        Raises:
            RuntimeError: If postprocessing fields are not available.
        """
        if self.u_solution is None or self.von_mises_proj is None or self._sigma is None:
            raise RuntimeError("Solution or postprocessing not computed.")

        self.logger.debug("Computing validation data for area load case")

        u = self.u_solution
        mesh = self.fenics_mesh
        sigma = self._sigma
        epsilon = self._epsilon

        # Collect area load facets
        area_forces = []
        for facet in do.facets(mesh):
            if self.area_markers[facet.index()] == 1:
                vertices = facet.entities(0)
                facet_coords = [mesh.coordinates()[v] for v in vertices]
                area_forces.append({
                    "facet_vertices": [[float(c) for c in vertex] for vertex in facet_coords],
                    "force_magnitude": float(force_value),
                    "force_direction": (
                        [float(d) / np.linalg.norm(force_direction) for d in force_direction]
                        if np.linalg.norm(force_direction) != 0 else [0.0, 0.0, 0.0]
                    ),
                    "input_direction": list(map(float, force_direction))
                })

        # Total strain energy
        energy = float(do.assemble(0.5 * do.inner(sigma(u), epsilon(u)) * do.dx))
        self.logger.debug(f"Total strain energy: {energy}")

        # External work of traction
        W_ext = do.assemble(do.dot(self.f_vec, self.u_solution) * self.ds_area(1))

        U = float(do.assemble(0.5 * do.inner(self._sigma(self.u_solution),
                                            self._epsilon(self.u_solution)) * do.dx))

        rel_err = abs(U - 0.5*W_ext) / max(1.0, abs(U))
        self.logger.warning(f"Energy check: U={U:.6e}, 0.5*W_ext={0.5*W_ext:.6e}, rel_err={rel_err:.3e}")

        # Displacement and stress extrema
        max_disp = float(np.max(u.vector().get_local()))
        min_disp = float(np.min(u.vector().get_local()))
        max_vm = float(np.max(self.von_mises_proj.vector().get_local()))
        self.logger.debug(f"Displacement min/max: {min_disp}/{max_disp}")
        self.logger.debug(f"Max Von Mises stress: {max_vm}")

        # Validation data structure
        validation_data = {
            "file": self.base_name,
            "solver": {
                "type": self.solver_type,
                "preconditioner": self.preconditioner
            },
            "num_dofs": self.V.dim(),
            "energy_total_strain": energy,
            "max_displacement": max_disp,
            "min_displacement": min_disp,
            "max_von_mises": max_vm,
            "material": material,
            "boundary_conditions": {
                "selected_axis": selected_axis,
                "selected_boundary_point": selected_boundary_point,
                "boundary_direction": boundary_direction
            },
            "area_forces": area_forces,
            "solver_log": self.solver_output
        }

        report_path = os.path.join(self.output_dir, f"{self.base_name}_area_load_validation.json")
        try:
            with open(report_path, "w") as f_json:
                json.dump(validation_data, f_json, indent=4)
            self.logger.info(f"Validation data saved to {report_path}")
        except OSError as e:
            self.logger.error(f"Failed to save validation data: {e}")








# -----------------------------------------------------------------------------
# FEM Point Solver
# -----------------------------------------------------------------------------
# Description:
#   This module provides the FEMPointSolver class, which extends FEMBaseSolver
#   to support FEM analyses with point forces. It is responsible for:
#     - Applying Dirichlet boundary conditions on a plane
#     - Applying concentrated nodal loads
#     - Solving the FEM system
#     - Postprocessing and computing validation data
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
import os

import dolfin as do
import numpy as np

from fem_app.fem.fem_base import FEMBaseSolver


class FEMPointSolver(FEMBaseSolver):
    """
    FEM solver for point load problems.

    Extends FEMBaseSolver to:
        - Apply concentrated point loads at mesh nodes
        - Define Dirichlet boundary conditions on a plane.
        - Assemble and solve the FEM system.
        - Compute validation and verification data.
    """

    def __init__(self) -> None:
        """
        Initialize the point load solver and logger.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEMPointSolver initialized")

    # -------------------------------------------------------------------------
    def generate_and_solve(
        self,
        file_name: str,
        point_forces: list[tuple[tuple[float, float, float], float, tuple[float, float, float]]],
        material: str,
        selected_boundary_point: float,
        selected_axis: str,
        boundary_direction: str,
    ) -> str:
        """
        Complete FEM workflow for a point-load problem.

        Steps:
            1. Prepare output folder
            2. Generate mesh
            3. Setup function space
            4. Apply boundary conditions
            5. Setup material
            6. Define variational problem
            7. Assemble system
            8. Apply point loads
            9. Solve system
            10. Compute postprocessing
            11. Compute validation data
            12. Write output files

        Args:
            file_name: Path to the STL geometry file.
            point_forces: list of tuples [(point_coords, magnitude, direction)].
            material: Material name (must be supported by base solver).
            selected_boundary_point: Coordinate for applying boundary conditions.
            selected_axis: Axis ("X", "Y", "Z").
            boundary_direction: "<" or ">" indicating boundary plane direction.

        Returns:
            str: Path to the written XDMF file.
        """
        self.logger.info(f"Starting point-load FEM solve for file: {file_name}")

        self._prepare_output_folder(file_name, "point_load")
        self._generate_mesh(file_name)
        self._setup_function_space()
        self._apply_boundary_conditions(selected_boundary_point, selected_axis, boundary_direction)
        self._setup_material(material)
        self._define_variational_problem()
        self._assemble_system()
        self._apply_point_loads(point_forces)
        self._solve_linear_system()
        self._compute_postprocessing()
        self._compute_validation_data(point_forces, material, selected_boundary_point, selected_axis, boundary_direction)
        xdmf_path = self._write_output_files()

        self.logger.info(f"Point-load FEM solve completed. Results written to: {xdmf_path}")
        return xdmf_path

    # -------------------------------------------------------------------------
    def _apply_boundary_conditions(
    self,
    selected_boundary_point: float,
    selected_axis: str,
    boundary_direction: str,
    ) -> None:
        """
        Apply Dirichlet boundary conditions if a valid boundary selection is provided.

        Args:
            selected_boundary_point: Plane coordinate for boundary.
            selected_axis: Axis ("X", "Y", "Z").
            boundary_direction: "<" or ">".
        """
        self.logger.debug(
            f"Applying boundary conditions: {selected_axis}={selected_boundary_point}, dir={boundary_direction}"
        )

        if selected_boundary_point is not None and selected_axis and boundary_direction:

            class CustomBoundary(do.SubDomain):
                def inside(self, x, on_boundary):
                    if not on_boundary:
                        return False
                    if selected_axis == "X":
                        return (x[0] <= selected_boundary_point and boundary_direction == "<") or \
                            (x[0] >= selected_boundary_point and boundary_direction == ">")
                    elif selected_axis == "Y":
                        return (x[1] <= selected_boundary_point and boundary_direction == "<") or \
                            (x[1] >= selected_boundary_point and boundary_direction == ">")
                    elif selected_axis == "Z":
                        return (x[2] <= selected_boundary_point and boundary_direction == "<") or \
                            (x[2] >= selected_boundary_point and boundary_direction == ">")
                    else:
                        raise ValueError(f"Invalid axis for boundary selection: {selected_axis}")

            custom_boundary = CustomBoundary()

            # Mark facets for Dirichlet boundary
            mesh = self.fenics_mesh
            dim = mesh.topology().dim()
            self.dirichlet_markers = do.MeshFunction("size_t", mesh, dim - 1)
            self.dirichlet_markers.set_all(0)
            for facet in do.facets(mesh):
                mp = facet.midpoint()
                if custom_boundary.inside(mp.array(), True):
                    self.dirichlet_markers[facet] = 1

            num_bc_facets = int(np.sum(self.dirichlet_markers.array()))
            if num_bc_facets == 0:
                self.logger.warning("No boundary facets marked for Dirichlet conditions")
            else:
                self.logger.info(f"{num_bc_facets} facet(s) marked for Dirichlet conditions")

            # Define ds for this boundary
            self.ds_dirichlet = do.Measure("ds", domain=mesh, subdomain_data=self.dirichlet_markers)

            # Define the BC itself
            bc = do.DirichletBC(self.V, do.Constant((0.0, 0.0, 0.0)), custom_boundary)
            self.boundary_conditions = [bc]
            self.logger.info("Dirichlet boundary condition successfully applied")

        else:
            self.logger.warning("No valid boundary selection found - no Dirichlet BC applied.")
            self.boundary_conditions = []
        
    # -------------------------------------------------------------------------
    def _assemble_system(self) -> None:
        """
        Assemble the FEM linear system Ax = b with boundary conditions applied.

        Raises:
            RuntimeError: If variational problem has not been defined.
        """
        if self.a is None or self.L is None:
            raise RuntimeError("Variational problem not defined. Call _define_variational_problem() first.")

        self.logger.debug("Assembling FEM system (A, b)")
        self.A, self.b = do.assemble_system(self.a, self.L, self.boundary_conditions)
        self.logger.info("System assembly completed")

    # -------------------------------------------------------------------------
    def _apply_point_loads(
        self,
        point_forces: list[tuple[tuple[float, float, float], float, tuple[float, float, float]]],
    ) -> None:
        """
        Apply concentrated point forces to the assembled right-hand side vector.

        Each load is applied at the nearest node within an epsilon tolerance.

        Args:
            point_forces: list of tuples [(coords, magnitude, direction)].

        Raises:
            ValueError: If a zero-length force direction vector is provided.
        """
        if self.fenics_mesh is None or self.b is None:
            raise RuntimeError("Mesh or system vector not initialized before applying point loads.")

        self.logger.debug(f"Applying {len(point_forces)} point load(s)")
        epsilon_check = 1e-6

        for point, force, direction in point_forces:
            closest_point = None
            min_distance = float("inf")

            # Find the closest mesh node
            for mesh_node in self.fenics_mesh.coordinates():
                distance = np.linalg.norm(np.array(mesh_node) - np.array(point))
                if distance < epsilon_check and distance < min_distance:
                    closest_point = mesh_node
                    min_distance = distance

            if closest_point is None:
                self.logger.warning(f"No matching mesh node found near point {point}")
                continue

            dir_len = np.linalg.norm(direction)
            if dir_len == 0:
                self.logger.warning(f"Zero direction vector for point {point}, skipping load")
                continue

            normalized_dir = [d / dir_len for d in direction]
            force_vector = [force * d for d in normalized_dir]

            # Apply point loads component-wise
            do.PointSource(self.V.sub(0), do.Point(*closest_point), force_vector[0]).apply(self.b)
            do.PointSource(self.V.sub(1), do.Point(*closest_point), force_vector[1]).apply(self.b)
            do.PointSource(self.V.sub(2), do.Point(*closest_point), force_vector[2]).apply(self.b)

            self.logger.debug(f"Applied point force {force_vector} at {closest_point}")

    # -------------------------------------------------------------------------
    def _compute_validation_data(
        self,
        point_forces: list[tuple[tuple[float, float, float], float, tuple[float, float, float]]],
        material: str,
        selected_boundary_point: float,
        selected_axis: str,
        boundary_direction: str,
    ) -> None:
        """
        Compute additional validation data for point load simulations.

        Data includes:
            - Total strain energy
            - Displacement extremes
            - Maximum Von Mises stress
            - Point force metadata
            - Solver log

        Raises:
            RuntimeError: If solution or postprocessing fields are not available.
        """
        if self.u_solution is None or self.von_mises_proj is None or self._sigma is None or self._epsilon is None:
            raise RuntimeError("Solution or postprocessing fields not available.")

        self.logger.debug("Computing validation data for point load case")

        u = self.u_solution
        sigma = self._sigma
        epsilon = self._epsilon
        mesh = self.fenics_mesh

        # Strain energy 
        energy = float(do.assemble(0.5 * do.inner(sigma(u), epsilon(u)) * do.dx))
        max_disp = float(np.max(u.vector().get_local()))
        min_disp = float(np.min(u.vector().get_local()))
        max_vm = float(np.max(self.von_mises_proj.vector().get_local()))

        self.logger.debug(f"Strain energy: {energy}")
        self.logger.debug(f"Displacement min/max: {min_disp}/{max_disp}")
        self.logger.debug(f"Max Von Mises stress: {max_vm}")

        # External work from multiple point loads 
        W_ext_total = 0.0
        for point, force, direction in point_forces:
            dir_vec = np.array(direction, dtype=float)
            if np.linalg.norm(dir_vec) == 0:
                continue
            F_vec = float(force) * dir_vec / np.linalg.norm(dir_vec)
            try:
                u_point = np.array(u(point))
                W_ext_total += np.dot(F_vec, u_point)
                self.logger.debug(f"Point {point}: u={u_point}, F={F_vec}, contribution={np.dot(F_vec, u_point)}")
            except Exception as e:
                self.logger.warning(f"Failed to evaluate displacement at {point}: {e}")
        self.logger.info(f"Total external work from point loads: W_ext_total={W_ext_total}")

        # Energy balance check 
        rel_err = abs(energy - 0.5 * W_ext_total) / max(1.0, abs(energy))
        self.logger.info(f"Energy check: U={energy:.6e}, 0.5*W_ext={0.5*W_ext_total:.6e}, rel_err={rel_err:.3e}")

        # Build validation report
        validation_data = {
            "file": self.base_name,
            "solver": {
                "type": self.solver_type,
                "preconditioner": self.preconditioner,
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
                "boundary_direction": boundary_direction,
            },
            "point_forces": [
                {
                    "applied_point": list(map(float, point)),
                    "force_magnitude": float(force),
                    "force_direction": (
                            [float(d) / np.linalg.norm(direction) for d in direction]
                            if np.linalg.norm(direction) != 0 else [0.0, 0.0, 0.0]
                        ),
                    "input_direction": list(map(float, direction))
                }
                for point, force, direction in point_forces
            ],
            "solver_log": self.solver_output,
        }

        report_path = os.path.join(self.output_dir, f"{self.base_name}_point_load_validation.json")
        try:
            with open(report_path, "w") as f_json:
                json.dump(validation_data, f_json, indent=4)
            self.logger.info(f"Validation data saved to {report_path}")
        except OSError as e:
            self.logger.error(f"Failed to save validation data: {e}")



# -----------------------------------------------------------------------------
# FEM Base Solver
# -----------------------------------------------------------------------------
# Description:
#   Abstract base class for FEM analyses. Provides shared functionality for:
#     - Output folder preparation
#     - Mesh generation via Gmsh -> MeshIO -> FeniCS
#     - Function space and variational form 
#     - Material parameter setup 
#     - Linear solve (direct or iterative)
#     - Postprocessing (von Mises, stress, strain)
#     - Results export (XDMF)
#
#   Subclasses (FenicsPointSolver, FenicsAreaSolver) are responsible for:
#     - Defining boundary conditions and external loads
#     - Building measures (ds_area) and forces (f_vec)
#     - Assembling the linear system: self.A, self.b
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import os
import sys
import tempfile
from datetime import datetime
from typing import Optional, List

import dolfin as do
import meshio
import numpy as np

from fem_app.mesh.mesh_generator import MeshGenerator


class FEMBaseSolver:
    """
    Base solver class for FEniCS-based FEM calculations.

    This class encapsulates common steps required by multiple FEM analyses:
    mesh generation, function-space setup, material parameterization, weak-form
    definition, linear system solution, postprocessing, and result export.

    Subclasses must:
        - Define boundary conditions and loads (set 'self.boundary_conditions',
          'self.ds_area', 'self.f_vec' as needed).
        - Assemble the linear system and set 'self.A' and 'self.b' before calling
          '_solve_linear_system()'

    Attributes:
        logger (logging.Logger): Module-level logger.
        mesh (meshio.Mesh): Raw mesh produced by MeshIO.
        fenics_mesh (do.Mesh): Converted FEniCS mesh.
        V (do.FunctionSpace): Vector function space.
        u (do.TrialFunction): Trial function for displacement.
        v (do.TestFunction): Test function for displacement.
        material (str): Selected material descriptor.
        mu (do.Constant): Shear modulus.
        lambda_ (do.Constant): First Lamé parameter.
        ds_area (Optional[do.Measure]): Exterior boundary measure with markers.
        f_vec (Optional[do.Constant]): Body/traction vector used on boundary.
        boundary_conditions (List): List of FEniCS DirichletBC objects.
        a (Optional[do.Form]): Bilinear form.
        L (Optional[do.Form]): Linear form.
        u_solution (Optional[do.Function]): Displacement solution.
        von_mises_proj (Optional[do.Function]): Scalar von Mises field.
        sigma_proj (Optional[do.Function]): Tensor stress field.
        epsilon_proj (Optional[do.Function]): Tensor strain field.
        solver_output (Optional[List[str] | str]): Iterative solver log or note.
        solver_type (Optional[str]): "LU" or "CG".
        preconditioner (Optional[str]): Preconditioner used for iterative solve.
        output_dir (Optional[str]): Simulation output directory.
        base_name (Optional[str]): Base file name for outputs.
    """

    def __init__(self) -> None:
        """
        Initialize the FEM solver state with empty fields and a logger.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEMBaseSolver initialized")

        # FEM state variables
        self.mesh: Optional[meshio.Mesh] = None
        self.fenics_mesh: Optional[do.Mesh] = None
        self.V: Optional[do.FunctionSpace] = None
        self.u = None
        self.v = None

        # Material properties
        self.material: Optional[str] = None
        self.mu: Optional[do.Constant] = None
        self.lambda_: Optional[do.Constant] = None

        # Boundary and load handling
        self.ds_area: Optional[do.Measure] = None
        self.f_vec: Optional[do.Constant] = None
        self.boundary_conditions: List = []

        # Variational problem
        self.a: Optional[do.Form] = None
        self.L: Optional[do.Form] = None

        # Linear system (must be set by subclass before solving)
        self.A = None  
        self.b = None  

        # Solution and postprocessing
        self.u_solution: Optional[do.Function] = None
        self.von_mises_proj: Optional[do.Function] = None
        self.sigma_proj: Optional[do.Function] = None
        self.epsilon_proj: Optional[do.Function] = None

        # Solver info
        self.solver_output: Optional[List[str] | str] = None
        self.solver_type: Optional[str] = None
        self.preconditioner: Optional[str] = None

        # Output directories
        self.output_dir: Optional[str] = None
        self.base_name: Optional[str] = None

        # Stress ops
        self._sigma = None
        self._epsilon = None

    # -------------------------------------------------------------------------
  
    def _prepare_output_folder(self, file_name: str, analysis_type: str, output_root: str = None) -> None:
        """
        Create an output folder next to the input file.

        Args:
            file_name: Path to the input geometry file.
            analysis_type: A short tag describing the analysis variant.
        """
        
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        result_folder_name = f"{base_name}_{analysis_type}_{timestamp}"
        
        if output_root:
            output_dir = os.path.join(output_root, result_folder_name)
        else:
            input_dir = os.path.dirname(os.path.abspath(file_name))
            output_dir = os.path.join(input_dir, result_folder_name)

        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.base_name = base_name

        self.logger.info(f"Output directory prepared at: {self.output_dir}")


    # -------------------------------------------------------------------------
    def _generate_mesh(self, file_name: str) -> None:
        """
        Generate a mesh using Gmsh and convert it to a FEniCS-compatible mesh.

        Workflow:
            1) MeshGenerator -> Gmsh 3D tetra mesh
            2) Write temporary dolfin-xml via meshio
            3) Load do.Mesh from temporary file

        Args:
            file_name: Path to the STL file.

        Raises:
            RuntimeError: If mesh conversion to FeniCS fails.
            ValueError, FileNotFoundError: Propagated from mesh generator.
        """
        if not self.output_dir:
            raise RuntimeError("Output directory is not prepared. Call _prepare_output_folder() first.")

        self.logger.debug(f"Generating mesh for file: {file_name}")
        mesh_generator = MeshGenerator()
        self.mesh = mesh_generator.generate_mesh_with_gmsh(file_name, self.output_dir)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as temp_xml:
                tmp_path = temp_xml.name
                meshio.write(temp_xml.name, self.mesh, file_format="dolfin-xml")

            self.fenics_mesh = do.Mesh(tmp_path)

            self.logger.info(f"Mesh generated with {self.mesh.cells[0].data.shape[0]} elements")
        except Exception as e:
            self.logger.error(f"Failed to convert mesh to FEniCS format: {e}")
            raise RuntimeError(f"Failed to convert mesh to FEniCS format: {e}") from e
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError as rm_err:
                    self.logger.warning(f"Temporary mesh file could not be removed: {rm_err}")

    # -------------------------------------------------------------------------
    def _setup_function_space(self) -> None:
        """
        Setup a first-order Lagrange vector function space and trial/test functions.

        Raises:
            RuntimeError: If the FEniCS mesh has not been created yet.
        """
        if self.fenics_mesh is None:
            raise RuntimeError("FEniCS mesh is not available. Call _generate_mesh() first.")

        self.logger.debug("Setting up function space")
        self.V = do.VectorFunctionSpace(self.fenics_mesh, "Lagrange", 2)
        self.u = do.TrialFunction(self.V)
        self.v = do.TestFunction(self.V)
        self.logger.info(f"Number of DOFs: {self.V.dim()}")

    # -------------------------------------------------------------------------
    def _setup_material(self, material: str) -> None:
        """
        Define material properties for isotropic linear elasticity.

        Supported materials (and expected geometry units):
            - "Structural Steel [m]"   (E=210e9,  nu=0.30)
            - "Titanium [m]"           (E=110e9,  nu=0.34)
            - "Structural Steel [cm]"  (E=210e5,  nu=0.30)
            - "Titanium [cm]"          (E=1.1e7,  nu=0.34)

        Args:
            material: Selected material descriptor.

        Raises:
            ValueError: If an unsupported material is provided.
        """
        self.logger.debug(f"Setting up material: {material}")

        if material == "Structural Steel [m]":
            E = do.Constant(210e9); nu = do.Constant(0.30)
        elif material == "Titanium [m]":
            E = do.Constant(110e9); nu = do.Constant(0.34)
        elif material == "Structural Steel [cm]":
            E = do.Constant(210e5); nu = do.Constant(0.30)
        elif material == "Titanium [cm]":
            E = do.Constant(1.1e7); nu = do.Constant(0.34)
        else:
            self.logger.error(f"Invalid material selected: {material}")
            raise ValueError(f"Invalid material selected: {material}")

        self.material = material
        self.mu = E / (2 * (1 + nu))
        self.lambda_ = E * nu / ((1 + nu) * (1 - 2 * nu))

        self.logger.info(
            f"Material set: {material} (E={_const_value(E):.6g}, ν={_const_value(nu):.6g})"
        )

    # -------------------------------------------------------------------------
    def _define_variational_problem(self) -> None:
        """
        Define the weak form of the linear elasticity problem.

        The bilinear form 'a(u, v)' uses the Lame parameters.
        The linear form 'L(v)' optionally applies a boundary traction 'f_vec'
        on marked boundary 'ds_area(1)'; otherwise no external traction is applied.

        Raises:
            RuntimeError: If material parameters or function space are not initialized.
        """
        if self.V is None or self.u is None or self.v is None:
            raise RuntimeError("Function space is not set. Call _setup_function_space() first.")
        if self.lambda_ is None or self.mu is None:
            raise RuntimeError("Material parameters are not set. Call _setup_material() first.")

        self.logger.debug("Defining variational problem")

        def epsilon(u_):
            return do.sym(do.grad(u_))

        def sigma(u_):
            return self.lambda_ * do.tr(epsilon(u_)) * do.Identity(3) + 2 * self.mu * epsilon(u_)

        self._sigma = sigma
        self._epsilon = epsilon
        self.a = do.inner(sigma(self.u), epsilon(self.v)) * do.dx

        if self.f_vec is not None and self.ds_area is not None:
            self.L = do.dot(self.f_vec, self.v) * self.ds_area(1)
            self.logger.debug("Boundary traction applied in variational form")
        else:
            self.L = do.dot(do.Constant((0.0, 0.0, 0.0)), self.v) * do.dx
            self.logger.debug("No external tractions defined")

    # -------------------------------------------------------------------------
    def _solve_linear_system(self) -> None:
        """
        Solve the linear system for displacement.

        Uses a direct LU factorization for small systems (DOFs < 1e4) and
        Conjugate Gradient with hypre AMG preconditioning for larger systems.

        Preconditions (must be satisfied by subclasses before calling this):
            - 'self.A' (assembled matrix) and 'self.b' (assembled RHS) exist.
            - Boundary conditions have been applied during assembly as needed.

        Raises:
            RuntimeError: If the function space or linear system is not prepared.
        """
        if self.V is None:
            raise RuntimeError("Function space not set. Call _setup_function_space() and assemble the system first.")
        if self.A is None or self.b is None:
            raise RuntimeError("Linear system (A, b) is not assembled. Subclass must set self.A and self.b.")

        self.logger.debug("Solving linear system")
        self.u_solution = do.Function(self.V)
        num_dofs = self.V.dim()

        if num_dofs < 1e4:
            self.logger.info(f"DOFs: {num_dofs} -> Using direct LU solver")
            do.solve(self.A, self.u_solution.vector(), self.b, "lu")
            self.solver_output = "no iterative output for LU"
            self.solver_type = "LU"
            self.preconditioner = None
        else:
            self.logger.info(f"DOFs: {num_dofs} -> Using CG solver with hypre_amg preconditioner")
            solver = do.KrylovSolver("cg", "hypre_amg")
            solver.parameters["absolute_tolerance"] = 1e-10
            solver.parameters["relative_tolerance"] = 1e-6
            solver.parameters["maximum_iterations"] = 1000
            solver.parameters["monitor_convergence"] = True

            # Capture solver output to a temp file
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
                tmp_path = tmp.name

            original_stdout_fd = os.dup(sys.stdout.fileno())
            original_stderr_fd = os.dup(sys.stderr.fileno())
            try:
                with open(tmp_path, "w") as tmp_file:
                    os.dup2(tmp_file.fileno(), sys.stdout.fileno())
                    os.dup2(tmp_file.fileno(), sys.stderr.fileno())
                    try:
                        solver.solve(self.A, self.u_solution.vector(), self.b)
                    finally:
                        os.dup2(original_stdout_fd, sys.stdout.fileno())
                        os.dup2(original_stderr_fd, sys.stderr.fileno())
                with open(tmp_path, "r") as tmp_file:
                    self.solver_output = tmp_file.read().splitlines()
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            self.solver_type = "CG"
            self.preconditioner = "hypre_amg"

        self.u_solution.rename("Displacement", "")
        self.logger.info(f"Solve completed using {self.solver_type} solver")

    # -------------------------------------------------------------------------


    def _compute_postprocessing(self) -> None:
        """
        Compute postprocessing fields:
            - Von Mises stress (scalar)
            - Cauchy stress tensor
            - Small-strain tensor
            - Optional scaling to MPa based on material system

        Raises:
            RuntimeError: If solution or mesh is unavailable.
        """
        if self.u_solution is None or self.fenics_mesh is None or self._sigma is None or self._epsilon is None:
            raise RuntimeError("Postprocessing prerequisites not met. Solve problem first.")

        self.logger.debug("Computing postprocessing fields")

        # Compute stress tensor from displacement field
        S = self._sigma(self.u_solution)

        def dev(S_):
            return S_ - (1.0 / 3.0) * do.tr(S_) * do.Identity(3)

        von_mises = do.sqrt(3.0 / 2.0 * do.inner(dev(S), dev(S)))

        # Von Mises projection (scalar)
        self.von_mises_proj = do.project(
            von_mises,
            do.FunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.von_mises_proj.rename("VonMisesStress", "")

        # Clamp negative numerical noise
        arr = self.von_mises_proj.vector().get_local()
        arr[arr < 0.0] = 0.0
        self.von_mises_proj.vector().set_local(arr)
        self.von_mises_proj.vector().apply("insert")

        # Stress tensor projection
        self.sigma_proj = do.project(
            S,
            do.TensorFunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.sigma_proj.rename("StressTensor", "")

        # Strain tensor projection (no scaling, dimensionless)
        self.epsilon_proj = do.project(
            self._epsilon(self.u_solution),
            do.TensorFunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.epsilon_proj.rename("StrainTensor", "")

        # Unit scaling based on material label
        scale_factor = 1.0
        material_label = getattr(self, "material", "").lower()

        if "[cm]" in material_label:
            scale_factor = 0.01        # N/cm^2 -> MPa
        elif "[m]" in material_label:
            scale_factor = 1.0 / 1e6   # Pa -> MPa

        # Apply scaling to stress and Von Mises
        if scale_factor != 1.0:
            self.von_mises_proj.vector()[:] *= scale_factor
            self.von_mises_proj.vector().apply("insert")

            self.sigma_proj.vector()[:] *= scale_factor
            self.sigma_proj.vector().apply("insert")

            self.logger.info(
                f"Stress fields scaled by factor {scale_factor} for material '{self.material}'"
            )

        self.logger.info("Postprocessing completed: Von Mises, Stress, Strain (in MPa)")


    '''
    def _compute_postprocessing(self) -> None:
        """
        Compute postprocessing fields:
            - Von Mises stress (scalar)
            - Cauchy stress tensor
            - Small-strain tensor

        Raises:
            RuntimeError: If solution or mesh is unavailable.
        """
        if self.u_solution is None or self.fenics_mesh is None or self._sigma is None or self._epsilon is None:
            raise RuntimeError("Postprocessing prerequisites not met. Solve problem first.")

        self.logger.debug("Computing postprocessing fields")
        S = self._sigma(self.u_solution)

        def dev(S_):
            return S_ - (1.0 / 3.0) * do.tr(S_) * do.Identity(3)

        von_mises = do.sqrt(3.0 / 2.0 * do.inner(dev(S), dev(S)))

        # Von Mises projection (P1)
        self.von_mises_proj = do.project(
            von_mises,
            do.FunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.von_mises_proj.rename("VonMisesStress", "")

        # Clamp numerical negatives to zero
        arr = self.von_mises_proj.vector().get_local()
        arr[arr < 0.0] = 0.0
        self.von_mises_proj.vector().set_local(arr)
        self.von_mises_proj.vector().apply("insert")

        # Stress tensor projection
        self.sigma_proj = do.project(
            S,
            do.TensorFunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.sigma_proj.rename("StressTensor", "")

        # Strain tensor projection
        self.epsilon_proj = do.project(
            self._epsilon(self.u_solution),
            do.TensorFunctionSpace(self.fenics_mesh, "P", 1),
            solver_type="cg",
            preconditioner_type="hypre_amg",
        )
        self.epsilon_proj.rename("StrainTensor", "")

        self.logger.info("Postprocessing completed: Von Mises, Stress, Strain")
        '''

    # -------------------------------------------------------------------------
    def _write_output_files(self) -> str:
        """
        Write derived fields to an XDMF file:
            - Displacement
            - Von Mises stress
            - Stress tensor
            - Strain tensor

        Returns:
            Path to the written XDMF file.

        Raises:
            RuntimeError: If required fields are missing or the output dir is unset.
            OSError: If writing the XDMF file fails.
        """
        if not self.output_dir or not self.base_name:
            raise RuntimeError("Output directory not prepared. Call _prepare_output_folder() first.")
        if self.u_solution is None or self.von_mises_proj is None or self.sigma_proj is None or self.epsilon_proj is None:
            raise RuntimeError("Fields not computed. Call _compute_postprocessing() first.")

        file_name_xdmf = os.path.join(self.output_dir, f"{self.base_name}.xdmf")
        self.logger.debug(f"Writing output to: {file_name_xdmf}")

        xdmf = None
        try:
            xdmf = do.XDMFFile(file_name_xdmf)
            xdmf.parameters["flush_output"] = True
            xdmf.parameters["functions_share_mesh"] = True
            xdmf.write(self.u_solution, 0.0)
            xdmf.write(self.von_mises_proj, 0.0)
            xdmf.write(self.sigma_proj, 0.0)
            xdmf.write(self.epsilon_proj, 0.0)
        except Exception as e:
            self.logger.error(f"Failed to write XDMF results: {e}")
            raise
        finally:
            try:
                if xdmf is not None:
                    xdmf.close()
            except Exception:
                pass

        self.logger.info(f"Results written to {file_name_xdmf}")
        return file_name_xdmf


# -----------------------------------------------------------------------------#
# Utilities
# -----------------------------------------------------------------------------#

def _const_value(c: do.Constant) -> float:
    """
    Safely extract a scalar value from a FeniCS Constant for logging.

    Args:
        c: FEniCS Constant.

    Returns:
        float: Scalar numeric value.
    """
    try:
        return float(c)
    except Exception:
        try:
            # Fallback for older FEniCS versions
            return float(c.values()[0])  # type: ignore[attr-defined]
        except Exception:
            return np.nan




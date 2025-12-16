# -----------------------------------------------------------------------------
# FEM Point Solver Validation Script
# -----------------------------------------------------------------------------
# This script validates the point-load solver against a known analytical
# beam theory result. It compares computed FEM results (deflection, stress)
# with reference analytical values for a simple cantilever beam under a
# single point load.
#
# It performs:
#  - FEM solves for multiple mesh refinements
#  - Extraction of maximum deflection and stress
#  - Comparison with analytical benchmark values
#  - Calculation of absolute and relative percentage errors
#  - Tabulated summary of validation accuracy
#
# -----------------------------------------------------------------------------
# PHYSICAL SETUP:
# -----------------------------------------------------------------------------
# Geometry:
#  - Beam dimensions: 100 cm (length) × 5 cm (height) × 5 cm (depth)
#  - Material: Structural Steel [cm]
#  - Boundary condition: beam fixed at the left end (x = 0, direction "<")
#  - Loading: point load of 2000 N acting vertically downward (-Y direction)
#    applied in the middle of the right free end top surface.
#
# This setup represents a classical cantilever beam configuration:
# the beam is constrained on the left and extends outward,
# with a downward point load applied at the free end.
#
# -----------------------------------------------------------------------------
# HOW TO USE:
# -----------------------------------------------------------------------------
# 1.  Choose whether to save FEM result files:
#      save_results = True    # keeps .xdmf and .json files
#      save_results = False   # uses temporary folder and deletes after
#
# 2.  Run the script:
#      python -m tests/validate_point_solver
#
# -----------------------------------------------------------------------------
# HOW IT VALIDATES:
# -----------------------------------------------------------------------------
# For each mesh:
#  - Runs a full FEM solve with the given point load and boundary setup.
#  - Reads computed values for:
#        - Minimum displacement magnitude (deflection)
#        - Maximum von Mises stress
#  - Compares them to known analytical results for a
#    cantilever beam under tip load.
#  - Computes:
#        - Absolute error 
#        - Relative error 
# -----------------------------------------------------------------------------

import os
import time
import json
import logging
import numpy as np
import tempfile
import shutil
from fem_app.fem.fenics_point_solver import FEMPointSolver


class FEMSolverValidator:

    def __init__(
        self,
        meshes,
        point_force,
        bc_params,
        material="Structural Steel [cm]",
        true_deflection=0.6095,
        true_stress=96.0,
        save_results=False,
    ):
        self.meshes = meshes
        self.point_force = point_force
        self.bc_params = bc_params
        self.material = material
        self.true_deflection = true_deflection
        self.true_stress = true_stress
        self.save_results = save_results
        self.logger = logging.getLogger("FEMSolverValidator")
        logging.basicConfig(level=logging.INFO)


    def run_validation(self):

        results = []

        for stl_file in self.meshes:
            if not os.path.exists(stl_file):
                self.logger.warning(f"Missing mesh file: {stl_file}")
                continue

            if self.save_results:
                mesh_dir = os.path.dirname(os.path.abspath(stl_file))
                results_dir = os.path.join(mesh_dir, "results_validation")
                os.makedirs(results_dir, exist_ok=True)
                save_mode = "permanent"
            else:
                results_dir = tempfile.mkdtemp(prefix="tmp_validation_")
                save_mode = "temporary"

            self.logger.info(
                f"Running validation on {os.path.basename(stl_file)} "
                f"| Save mode: {save_mode.upper()} | Folder: {results_dir}"
            )

            solver = FEMPointSolver()
            solver._prepare_output_folder(stl_file, "validation_case", results_dir)

            start_time = time.perf_counter()

            # Full FEM Solve Process 
            solver._generate_mesh(stl_file)
            solver._setup_function_space()
            solver._apply_boundary_conditions(
                self.bc_params["selected_boundary_point"],
                self.bc_params["selected_axis"],
                self.bc_params["boundary_direction"],
            )
            solver._setup_material(self.material)
            solver._define_variational_problem()
            solver._assemble_system()
            solver._apply_point_loads(self.point_force)
            solver._solve_linear_system()
            solver._compute_postprocessing()
            solver._compute_validation_data(
                self.point_force,
                self.material,
                self.bc_params["selected_boundary_point"],
                self.bc_params["selected_axis"],
                self.bc_params["boundary_direction"],
            )

            # Write only if saving enabled
            if self.save_results:
                solver._write_output_files()

            end_time = time.perf_counter()
            total_runtime = end_time - start_time

            validation_file = os.path.join(
                solver.output_dir, f"{solver.base_name}_point_load_validation.json"
            )

            if os.path.exists(validation_file):
                with open(validation_file) as f:
                    data = json.load(f)
                num_deflection = abs(data.get("min_displacement", np.nan))
                num_stress = data.get("max_von_mises", np.nan) 
            else:
                num_deflection = num_stress = np.nan

            # computer errors
            defl_error_abs = abs(num_deflection - self.true_deflection)
            defl_error_rel = defl_error_abs / abs(self.true_deflection) * 100.0
            stress_error_abs = abs(num_stress - self.true_stress)
            stress_error_rel = stress_error_abs / abs(self.true_stress) * 100.0

            results.append({
                "mesh": os.path.basename(stl_file),
                "num_dofs": solver.V.dim(),
                "total_runtime_s": total_runtime,
                "deflection_FEM": num_deflection,
                "stress_FEM": num_stress,
                "deflection_true": self.true_deflection,
                "stress_true": self.true_stress,
                "deflection_error_abs": defl_error_abs,
                "deflection_error_rel(%)": defl_error_rel,
                "stress_error_abs": stress_error_abs,
                "stress_error_rel(%)": stress_error_rel,
                "save_mode": save_mode,
                "save_path": solver.output_dir,
            })

            # remove temporary folder if not saving results
            if not self.save_results:
                self.logger.info(f"Removing temporary results folder: {results_dir}")
                shutil.rmtree(results_dir, ignore_errors=True)

        return results


    def print_summary(self, results):
        print("\n=== FEM Solver Validation Summary ===")
        print(
            f"{'Mesh':20s} {'DOFs':>10s} {'Runtime(s)':>12s} "
            f"{'d_FEM':>12s} {'d_true':>12s} {'err_d(%)':>10s} "
            f"{'s_FEM':>12s} {'s_true':>12s} {'err_s(%)':>10s}"
        )
        print("-" * 120)
        for r in results:
            print(
                f"{r['mesh']:20s} "
                f"{r['num_dofs']:10d} "
                f"{r['total_runtime_s']:12.2f} "
                f"{r['deflection_FEM']:12.4f} "
                f"{r['deflection_true']:12.4f} "
                f"{r['deflection_error_rel(%)']:10.2f} "
                f"{r['stress_FEM']:12.2f} "
                f"{r['stress_true']:12.2f} "
                f"{r['stress_error_rel(%)']:10.2f}"
            )
        print("-" * 120)
        print("Note: d = tip deflection, s = maximum stress [MPa]")


if __name__ == "__main__":

    # Choose whether to keep result files
    save_results = False

    # Meshes for validation
    beam_meshes = [
        "tests/test_data/beam_medium.stl",
        "tests/test_data/beam_fine.stl",
        "tests/test_data/beam_super_fine.stl",
    ]

    # Point load (at the free right end of the beam, 2000N ,straight downward -Y)
    point_force = [((100.0, 5.0, 2.5), 2000.0, (0.0, -1.0, 0.0))]

    # Fixed boundary at left end of the beam (x = 0)
    bc = {"selected_boundary_point": 0.0, "selected_axis": "X", "boundary_direction": "<"}

    # Material and analytical truth
    material = "Structural Steel [cm]"
    true_deflection = 0.6095  # in cm
    true_stress = 96.0       # in MPa

    # validation 
    validator = FEMSolverValidator(
        meshes=beam_meshes,
        point_force=point_force,
        bc_params=bc,
        material=material,
        true_deflection=true_deflection,
        true_stress=true_stress,
        save_results=save_results,
    )

    results = validator.run_validation()
    validator.print_summary(results)
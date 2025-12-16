# -----------------------------------------------------------------------------
# FEM Point-Load Runtime & Convergence Test
# -----------------------------------------------------------------------------
# This script benchmarks FEM solver runtime and numerical convergence for different
# geometries subjected to a single point load.
#
# It:
#  - Runs FEMPointSolver for multiple mesh refinements (from coarse -> medium -> fine)
#  - Measures runtime performance 
#  - Computes strain energy and displacement errors
#  - Prints convergence information and solver statistics
#
# -----------------------------------------------------------------------------
# HOW TO USE:
# -----------------------------------------------------------------------------
# 1. Choose the geometry set you want to test:
#      mesh_type = "beam"
#      mesh_type = "cube"
#      mesh_type = "wrench"
#      mesh_type = "dental"
#
# 2. Each geometry has predefined:
#      - STL mesh files (in 'tests/test_data/')
#      - Point load parameters (position, magnitude, direction)
#      - Boundary conditions 
#      - Material setup
#
# 3. Optional:
#      - Set 'num_runs' for repeated timing
#      - Enable or disable file saving with 'save_results=True/False'
#
# 4. Run the script:
#      python -m tests/test_fem_point
# -----------------------------------------------------------------------------


import os
import time
import json
import logging
import numpy as np
import tempfile
import shutil
from fem_app.fem.fenics_point_solver import FEMPointSolver


def run_pointload_runtime_convergence_test(
    mesh_group: list,
    point_forces: list[tuple[tuple[float, float, float], float, tuple[float, float, float]]],
    material: str,
    bc_params: dict,
    num_runs: int = 1,
    save_results: bool = False,
):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FEMPointConvergenceTest")

    results = []

    for stl_file in mesh_group:
        if not os.path.exists(stl_file):
            logger.warning(f"Missing file: {stl_file}")
            continue

        # Decides where to store results 
        if save_results:
            mesh_dir = os.path.dirname(os.path.abspath(stl_file))
            results_dir = os.path.join(mesh_dir, "results_point_load")
            os.makedirs(results_dir, exist_ok=True)
            save_mode = "permanent"
        else:
            results_dir = tempfile.mkdtemp(prefix="tmp_pointload_")
            save_mode = "temporary"

        logger.info(f"Saving mode: {save_mode.upper()} | Folder: {results_dir}")

        runtimes = []
        solver = FEMPointSolver()

        for run in range(num_runs):
            logger.info(f"=== Solving {os.path.basename(stl_file)} (run {run + 1}/{num_runs}) ===")

            solver._prepare_output_folder(results_dir, stl_file, "point_load")
            solver._generate_mesh(stl_file)  # mesh generation (excluded from timing)

            start_time = time.perf_counter()

            solver._setup_function_space()
            solver._apply_boundary_conditions(
                bc_params["selected_boundary_point"],
                bc_params["selected_axis"],
                bc_params["boundary_direction"],
            )
            solver._setup_material(material)
            solver._define_variational_problem()
            solver._assemble_system()
            solver._apply_point_loads(point_forces)
            solver._solve_linear_system()
            solver._compute_postprocessing()
            solver._compute_validation_data(
                point_forces,
                material,
                bc_params["selected_boundary_point"],
                bc_params["selected_axis"],
                bc_params["boundary_direction"],
            )

            if save_results:
                solver._write_output_files()

            end_time = time.perf_counter()
            runtimes.append(end_time - start_time)

        validation_file = os.path.join(
            solver.output_dir, f"{solver.base_name}_point_load_validation.json"
        )

        if os.path.exists(validation_file):
            with open(validation_file) as f:
                data = json.load(f)
            energy = data.get("energy_total_strain", np.nan)
            max_disp = data.get("max_displacement", np.nan)
            min_disp = data.get("min_displacement", np.nan)
        else:
            energy = max_disp = min_disp = np.nan

        runtimes_np = np.array(runtimes)
        runtime_mean = np.mean(runtimes_np)
        runtime_std = np.std(runtimes_np)
        runtime_min = np.min(runtimes_np)
        runtime_max = np.max(runtimes_np)

        results.append({
            "mesh_path": stl_file,
            "mesh_name": os.path.basename(stl_file),
            "num_dofs": solver.V.dim(),
            "energy": energy,
            "max_disp": max_disp,
            "min_disp": min_disp,
            "solver_type": getattr(solver, "solver_type", "unknown"),
            "runtime_mean": runtime_mean,
            "runtime_std": runtime_std,
            "runtime_min": runtime_min,
            "runtime_max": runtime_max,
            "save_mode": save_mode,
            "save_path": solver.output_dir,
        })

        # Remove temporary results folder if not saving
        if not save_results:
            logger.info(f"Removing temporary results folder: {results_dir}")
            shutil.rmtree(results_dir, ignore_errors=True)

    return results


def compute_convergence_errors(results, reference_index=-1):
    ref_energy = results[reference_index]["energy"]
    ref_disp = results[reference_index]["max_disp"]

    for r in results:
        if np.isfinite(r["energy"]) and np.isfinite(ref_energy):
            r["energy_error"] = abs(r["energy"] - ref_energy) / abs(ref_energy)
        else:
            r["energy_error"] = np.nan

        if np.isfinite(r["max_disp"]) and np.isfinite(ref_disp):
            r["disp_error"] = abs(r["max_disp"] - ref_disp) / abs(ref_disp)
        else:
            r["disp_error"] = np.nan

    return results


def print_convergence_summary(results):
    print("\n=== FEM Point-Load Runtime & Convergence Summary ===")
    print(
        f"{'Mesh':25s} {'DOFs':>8s} {'Solver':>10s} "
        f"{'t_mean(s)':>10s} {'t_std(s)':>10s} {'t_min(s)':>10s} {'t_max(s)':>10s} "
        f"{'Energy':>12s} {'Disp(max)':>12s} {'Disp(min)':>12s} "
        f"{'E_err':>10s} {'U_err':>10s}"
    )
    print("-" * 160)

    for r in results:
        print(
            f"{r['mesh_name']:25s} "
            f"{r['num_dofs']:8d} "
            f"{r['solver_type']:>10s} "
            f"{r['runtime_mean']:10.3f} "
            f"{r['runtime_std']:10.3f} "
            f"{r['runtime_min']:10.3f} "
            f"{r['runtime_max']:10.3f} "
            f"{r['energy']:12.3e} "
            f"{r['max_disp']:12.3e} "
            f"{r['min_disp']:12.3e} "
            f"{r.get('energy_error', np.nan):10.3e} "
            f"{r.get('disp_error', np.nan):10.3e}"
        )
    print("-" * 160)


if __name__ == "__main__":

    # Choose which mesh group to test and number of runs and saving option 
    mesh_type = "beam"       
    num_runs = 1             
    save_results = False     

    mesh_groups = {
        "beam": [
            #"tests/test_data/beam_coarse.stl",
            #"tests/test_data/beam_medium.stl",
            #"tests/test_data/beam_fine.stl",
            #"tests/test_data/beam_super_fine.stl",
            "tests/test_data/beam_extreme_fine.stl",
        ],
        "cube": [
            "tests/test_data/cube_coarse.stl",
            "tests/test_data/cube_medium.stl",
            "tests/test_data/cube_fine.stl",
            "tests/test_data/cube_super_fine.stl",
        ],
    }

    # Predefined simulation setups 
    test_setups = {
        "beam": {
            "point_forces": [((100.0, 5.0, 5.0), 2000.0, (0.0, -1.0, 0.0))],
            "boundary_condition": {
                "selected_boundary_point": 0.0,
                "selected_axis": "X",
                "boundary_direction": "<",
            },
            "material": "Titanium [cm]",
            "description": "Cantilever beam fixed at x = 0, with a downward point load applied at the free end on the top surface.",
        },
        "cube": {
            "point_forces": [((5.0, 10.0, 5.0), 1500.0, (0.0, -1.0, 0.0))],
            "boundary_condition": {
                "selected_boundary_point": 0.0,
                "selected_axis": "Y",
                "boundary_direction": "<",
            },
            "material": "Structural Steel [cm]",
            "description": "Cube fixed at y = 0, with a downward point load applied at the center of the top surface.",
        },
        "wrench": {
            "point_forces": [((-11.3580, -70.5210, 10.0), 1000.0, (-1.0, 0.0, 0.0))],
            "boundary_condition": {
                "selected_boundary_point": 52.0,
                "selected_axis": "Y",
                "boundary_direction": ">",
            },
            "material": "Titanium [m]",
            "description": "Wrench fixed at socket end, point load at handle to simulate torque.",
        },
        "dental": {
            "point_forces": [((-12.92799, 21.75146, 23.78158), 1000.0, (1.0, -2.0, 0.0))],
            "boundary_condition": {
                "selected_boundary_point": -10.88069,
                "selected_axis": "Y",
                "boundary_direction": "<",
            },
            "material": "Structural Steel [m]",
            "description": "Dental model fixed at bottom, point load on top crown directed forward and downward.",
        },
    }

    # Validation check 
    if mesh_type not in mesh_groups or mesh_type not in test_setups:
        raise ValueError(
            f"Invalid mesh type '{mesh_type}'. Choose from: {list(mesh_groups.keys())}"
        )

    setup = test_setups[mesh_type]

    # Display simulation configuration 
    print(f"\n=== Running FEM Point-Load Runtime + Convergence Test ===")
    print(f"Geometry:     {mesh_type.upper()}")
    print(f"Material:     {setup['material']}")
    print(f"Description:  {setup['description']}")
    print(f"Load:         {setup['point_forces']}")
    print(f"Boundary:     {setup['boundary_condition']}")
    print(f"Save results: {save_results}")
    print(f"Runs per mesh:{num_runs}\n")

    # Run solver and compute results
    results = run_pointload_runtime_convergence_test(
        mesh_groups[mesh_type],
        setup["point_forces"],
        setup["material"],
        setup["boundary_condition"],
        num_runs=num_runs,
        save_results=save_results,
    )

    results = compute_convergence_errors(results)
    print_convergence_summary(results)
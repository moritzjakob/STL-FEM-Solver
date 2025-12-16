# -----------------------------------------------------------------------------
# FEM Area-Load Runtime & Convergence Test
# -----------------------------------------------------------------------------
# This script benchmarks FEM solver runtime and numerical convergence for different
# geometries subjected to an area load
#
# It:
#  - Runs FEMAreaSolver for multiple mesh refinements (from coarse -> medium -> fine)
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
#
# 2. Each geometry has predefined:
#     - STL mesh files (in 'tests/test_data/')
#      - Area facet vertices for area load application
#     - Load magnitude and direction
#     - Boundary condition parameters
#     - Material setup
#
# 3. Optional:
#      - Set 'num_runs' for repeated timing
#     - Enable or disable file saving with 'save_results=True/False'
#
# 4. Run the script:
#      python -m tests/test_fem_area
# -----------------------------------------------------------------------------


import os
import time
import json
import logging
import numpy as np
import tempfile
import shutil
from typing import Any
from fem_app.fem.fenics_area_solver import FEMAreaSolver
from tests.area_facets_data import beam_coarse, beam_medium, beam_fine, cube_coarse, cube_medium, cube_fine 



def run_areaload_runtime_convergence_test(
    mesh_group: list[dict[str, Any]],
    material: str,
    bc_params: dict,
    force_value: float,
    force_direction: tuple[float, float, float],
    num_runs: int = 1,
    save_results: bool = False,
):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FEMAreaConvergenceTest")

    results = []


    for mesh_entry in mesh_group:
        stl_file = mesh_entry["mesh"]
        area_facet_vertices = mesh_entry["facets"]

        if not os.path.exists(stl_file):
            logger.warning(f"Missing mesh file: {stl_file}")
            continue


        # Decides where to store results 
        if save_results:
            mesh_dir = os.path.dirname(os.path.abspath(stl_file))
            results_dir = os.path.join(mesh_dir, "results_area_load")
            os.makedirs(results_dir, exist_ok=True)
            save_mode = "permanent"
        else:
            results_dir = tempfile.mkdtemp(prefix="tmp_areaload_")
            save_mode = "temporary"

        logger.info(f"Running mesh {os.path.basename(stl_file)} | Save mode: {save_mode.upper()}")

        runtimes = []
        solver = FEMAreaSolver()

        for run in range(num_runs):
            logger.info(f"=== Solving {os.path.basename(stl_file)} (run {run + 1}/{num_runs}) ===")

            solver._prepare_output_folder(results_dir, stl_file, "area_load")
            solver._generate_mesh(stl_file) # mesh generation (excluded from timing)

            start_time = time.perf_counter()

            solver._setup_function_space()
            solver._mark_area_facets(area_facet_vertices)
            solver._apply_boundary_conditions(
                bc_params["selected_boundary_point"],
                bc_params["selected_axis"],
                bc_params["boundary_direction"],
            )
            solver._setup_material(material)
            solver._apply_area_loads(force_value, force_direction)
            solver._define_variational_problem()
            solver._assemble_system()
            solver._solve_linear_system()
            solver._compute_postprocessing()
            solver._compute_validation_data(
                material,
                bc_params["selected_boundary_point"],
                bc_params["selected_axis"],
                bc_params["boundary_direction"],
                force_value,
                force_direction,
            )

            if save_results:
                solver._write_output_files()

            end_time = time.perf_counter()
            runtimes.append(end_time - start_time)

        validation_file = os.path.join(
            solver.output_dir, f"{solver.base_name}_area_load_validation.json"
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
    print("\n=== FEM Area-Load Runtime & Convergence Summary ===")
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
    mesh_type = "cube"   
    num_runs = 2          
    save_results = False   

    mesh_groups = {
        "beam": [
            {"mesh": "tests/test_data/beam_coarse.stl", "facets": beam_coarse},
            {"mesh": "tests/test_data/beam_medium.stl", "facets": beam_medium},
            {"mesh": "tests/test_data/beam_fine.stl", "facets": beam_fine},
        ],
        "cube": [
            {"mesh": "tests/test_data/cube_coarse.stl", "facets": cube_coarse},  
            {"mesh": "tests/test_data/cube_medium.stl", "facets": cube_medium},
            {"mesh": "tests/test_data/cube_fine.stl", "facets": cube_fine},
        ],
    }

    # Predefined simulation setups 
    test_setups = {
        "beam": {
            "boundary_condition": {"selected_boundary_point": 0.0, "selected_axis": "X", "boundary_direction": "<"},
            "force_value": 2000.0,
            "force_direction": (0.0, -1.0, 0.0),
            "material": "Titanium [cm]",
            "description": "Cantilever beam fixed at x=0, downward load applied on top surface.",
        },
        "cube": {
            "boundary_condition": {"selected_boundary_point": 0.0, "selected_axis": "Y", "boundary_direction": "<"},
            "force_value": 1500.0,
            "force_direction": (0.0, -1.0, 0.0),
            "material": "Structural Steel [cm]",
            "description": "Cube fixed at y=0, uniform downward load applied on top surface.",
        },
    }

    # Validation check 
    if mesh_type not in mesh_groups or mesh_type not in test_setups:
        raise ValueError(f"Invalid mesh type '{mesh_type}'. Choose from: {list(mesh_groups.keys())}")

    setup = test_setups[mesh_type]

    # Display simulation configuration
    print(f"\n=== Running FEM Area-Load Runtime + Convergence Test ===")
    print(f"Geometry:     {mesh_type.upper()}")
    print(f"Material:     {setup['material']}")
    print(f"Description:  {setup['description']}")
    print(f"Force:        {setup['force_value']} N, direction {setup['force_direction']}")
    print(f"Boundary:     {setup['boundary_condition']}")
    print(f"Save results: {save_results}")
    print(f"Runs per mesh:{num_runs}\n")

     
    # Run solver and compute results
    results = run_areaload_runtime_convergence_test(
        mesh_groups[mesh_type],
        setup["material"],
        setup["boundary_condition"],
        setup["force_value"],
        setup["force_direction"],
        num_runs=num_runs,
        save_results=save_results,
    )

    results = compute_convergence_errors(results)
    print_convergence_summary(results)
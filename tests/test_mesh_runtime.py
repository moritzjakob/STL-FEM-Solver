# -----------------------------------------------------------------------------
# Mesh Runtime Test Script
# -----------------------------------------------------------------------------
# This script measures how long it takes to generate finite element meshes
# from STL geometry files using the MeshGenerator class (Gmsh backend).
#
# It:
#  - Loops through all meshes for a selected geometry 
#  - Runs the mesh generation several times per file
#  - Collects timing and mesh size statistics (points, elements)
#  - Prints a summary of runtime performance
#
# -----------------------------------------------------------------------------
# HOW TO USE:
# -----------------------------------------------------------------------------
# 1. Choose the geometry set you want to test:
#     mesh_type = "beam"
#     mesh_type = "cube"
#     mesh_type = "wrench"
#     mesh_type = "dental"
#
# 2. Adjust number of runs per mesh:
#     num_runs = 5  
#
# 3. Run the script:
#     python -m tests/test_mesh_runtime
# -----------------------------------------------------------------------------

import os
import time
import tempfile
import logging
from fem_app.mesh.mesh_generator import MeshGenerator  

def run_mesh_runtime_test(stl_file: str, element_size=None, num_runs: int = 1):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("MeshRuntimeTest")

    if not os.path.isfile(stl_file):
        raise FileNotFoundError(f"STL file not found: {stl_file}")

    meshgen = MeshGenerator()
    logger.info(f"Starting runtime test for {os.path.basename(stl_file)}")

    results = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        runtimes = []
        mesh_sizes = []

        for run in range(num_runs):
            logger.info(f"Run {run + 1}/{num_runs} starting...")

            start_time = time.perf_counter()
            mesh = meshgen.generate_mesh_with_gmsh(stl_file, tmpdir, element_size)
            end_time = time.perf_counter()

            elapsed = end_time - start_time
            runtimes.append(elapsed)
            mesh_sizes.append((len(mesh.points), sum(len(c.data) for c in mesh.cells)))

            logger.info(
                f"Run {run + 1}: {elapsed:.2f} seconds | "
                f"Points: {mesh_sizes[-1][0]} | Elements: {mesh_sizes[-1][1]}"
            )

    avg_time = sum(runtimes) / num_runs
    min_time = min(runtimes)
    max_time = max(runtimes)
    std_dev = (sum((t - avg_time) ** 2 for t in runtimes) / num_runs) ** 0.5

    results.update({
        "stl_file": stl_file,
        "run_times": runtimes,
        "mesh_sizes": mesh_sizes,
        "average_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "std_dev": std_dev,
    })

    logger.info(
        f"Finished {num_runs} runs: avg={avg_time:.2f}s, "
        f"min={min_time:.2f}s, max={max_time:.2f}s, std={std_dev:.2f}s"
    )

    return results


def print_mesh_runtime_summary(result: dict) -> None:
    print("\n=== Mesh Runtime Test Summary ===")
    print(f"Mesh file:          {os.path.basename(result['stl_file'])}")
    print(f"Number of runs:     {len(result['run_times'])}")
    print(f"Points:             {result['mesh_sizes'][0][0]}")
    print(f"Elements:           {result['mesh_sizes'][0][1]}")
    print(f"Run times (s):      {', '.join(f'{t:.3f}' for t in result['run_times'])}")
    print(f"Average time (s):   {result['average_time']:.3f}")
    print(f"Min time (s):       {result['min_time']:.3f}")
    print(f"Max time (s):       {result['max_time']:.3f}")
    print(f"Std deviation (s):  {result['std_dev']:.3f}")



if __name__ == "__main__":

    # Choose which mesh group to test and number of runs
    number_of_runs = 3
    mesh_type = "wrench"     

    mesh_groups = {
        "beam": [
            "tests/test_data/beam_coarse.stl",
            "tests/test_data/beam_medium.stl",
            "tests/test_data/beam_fine.stl",
            "tests/test_data/beam_super_fine.stl",
            "tests/test_data/beam_extreme_fine.stl",
        ],
        "cube": [
            "tests/test_data/cube_coarse.stl",
            "tests/test_data/cube_medium.stl",
            "tests/test_data/cube_fine.stl",
            "tests/test_data/cube_super_fine.stl",
        ],
        "dental": [
            "tests/test_data/dental.stl",
        ],
        "wrench": [
            "tests/test_data/wrench.stl",
        ],
    }

    # Validation check
    if mesh_type not in mesh_groups:
        raise ValueError(
            f"Invalid mesh type '{mesh_type}'. "
            f"Choose from: {', '.join(mesh_groups.keys())}"
        )

    print(f"\n=== Running mesh runtime tests for: {mesh_type.upper()} ===")

    results = [] 

    # Run tests for each mesh in the selected group
    for stl_file in mesh_groups[mesh_type]:
        if not os.path.exists(stl_file):
            print(f" Missing file: {stl_file}")
            continue

        result = run_mesh_runtime_test(stl_file, element_size=None, num_runs=number_of_runs)
        results.append(result)

    print("\n\n=== FINAL RESULTS SUMMARY ===")
    for result in results:
        print_mesh_runtime_summary(result)




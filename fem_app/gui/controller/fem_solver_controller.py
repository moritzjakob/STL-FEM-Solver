# -----------------------------------------------------------------------------
# FEM Solver Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller provides the core logic to solve FEM problems from the GUI.
#   It determines the active load type (point or area), validates all required
#   FEM input parameters, and handles over the actual solving to the corresponding
#   solver class.
#
#   Core functionality includes:
#       - Determining the active load group
#       - Validating force values, directions, and boundary conditions
#       - Calling the appropriate FEM solver (point or area)
#       - Handling all UI feedback and error messaging
#       - Loading the solved mesh back into the renderer
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_stl_file
from fem_app.fem.fenics_point_solver import FEMPointSolver
from fem_app.fem.fenics_area_solver import FEMAreaSolver

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Main Solve Dispatcher
# -------------------------------------------------------------------------
def solve_fem():
    """
    Determine the active load group (point or area) and call the appropriate FEM solver.

    Raises:
        QMessageBox: If no valid STL file is loaded or no load group is active.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded for FEM solving.")
        if main_window:
            QMessageBox.critical(main_window, "FEM Solving Error", "Current file is not a valid STL file.")
        return

    try:
        if sidebar and sidebar.fem_section.point_load_group.isVisible():
            logger.info("Solving FEM with point load.")
            main_window.statusBar().showMessage("Solving FEM with Area Load...", 5000)
            solve_point_load()

        elif sidebar and sidebar.fem_section.area_load_group.isVisible():
            logger.info("Solving FEM with area load.")
            main_window.statusBar().showMessage("Solving FEM with Area Load...", 5000)
            solve_area_load()

        else:
            raise ValueError("No active load group selected for FEM solving.")

    except Exception as e:
        logger.exception("Error during FEM solving.")
        if main_window:
            QMessageBox.critical(main_window, "FEM Solving Error", f"Error during FEM solving: {e}")


# -------------------------------------------------------------------------
# Area Load Solver
# -------------------------------------------------------------------------
def solve_area_load():
    """
    Run FEM solver for area loads.

    Steps:
        1. Validate force value
        2. Validate force direction
        3. Validate material and boundary conditions
        4. Run FEM area solver
        5. Load solution into renderer
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    # Force value validation
    try:
        force_value_str = sidebar.fem_section.area_force_input.text()
        force_value = float(force_value_str)
        if force_value == 0.0:
            QMessageBox.critical(
                main_window,
                "Invalid Force Value",
                "Force value cannot be 0. Please enter a non-zero number."
            )
            logger.warning("Force value is 0 - solver aborted.")
            return
        logger.debug(f"Force value: {force_value}")
    except (ValueError, TypeError):
        QMessageBox.critical(
            main_window,
            "Invalid Force Value",
            f"Invalid force value: '{force_value_str}'. Please enter a valid number."
        )
        logger.exception("Invalid force value.")
        return
    # Direction vector validation
    try:
        force_direction = app_context.get_app_state().get_force_direction()
        vector_value = [float(force_direction[axis]) for axis in ["X", "Y", "Z"]]
        if all(v == 0.0 for v in vector_value):
            raise ValueError("No force direction given.")
        logger.debug(f"Force direction vector: {vector_value}")
    except Exception:
        QMessageBox.critical(main_window, "Invalid Direction Value",
                             f"Invalid vector direction: {force_direction}. Please ensure all components are valid numbers.")
        logger.exception("Invalid force direction vector.")
        return

    try:
        # Material Validation
        if not app_context.get_app_state().get_selected_material() or \
           app_context.get_app_state().get_selected_material() == "None":
            raise ValueError("No material selected for FEM analysis.")

        # Boundary condition 
        selected_axis = _get_selected_boundary_axis(sidebar)
        boundary_direction = _get_selected_boundary_direction(sidebar)

        # Facet validation
        if not app_context.get_app_state().get_cells_vertices_values():
            raise ValueError("No valid facet provided.")

        # Solve 
        solver = FEMAreaSolver()
        xdmf_file = solver.generate_and_solve(
            app_context.get_app_state().get_current_file(),
            app_context.get_app_state().get_cells_vertices_values(),
            app_context.get_app_state().get_selected_material(),
            app_context.get_app_state().get_selected_boundary_point(),
            selected_axis,
            boundary_direction,
            force_value,
            vector_value
        )

        # Post solve, load solution
        _load_solution_into_renderer(xdmf_file)
        logger.info("FEM area load solved successfully.")

    except Exception as e:
        QMessageBox.critical(main_window, "FEM Solving Error", f"Error during FEM solving: {e}")
        logger.exception("Error solving FEM with area load.")


# -------------------------------------------------------------------------
# Point Load Solver
# -------------------------------------------------------------------------
def solve_point_load():
    """
    Run FEM solver for point loads.

    Steps:
        1. Validate forces and directions for all points
        2. Validate material and boundary conditions
        3. Run FEM point solver
        4. Load solution into renderer
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    forces = []
    for point_tuple, values in app_context.get_app_state().get_point_values().items():
        try:
            # Force validation 
            force_raw = values.get('force', 0)
            force_value = float(force_raw)
            if force_value == 0.0:
                readable_index = tuple(float(c) for c in point_tuple)
                QMessageBox.critical(
                    main_window,
                    "Invalid Force Value",
                    f"Force at point {readable_index} is 0. Please enter a non-zero value."
                )
                logger.warning(f"Force at {readable_index} is 0 - solver aborted.")
                return

        except (ValueError, TypeError):
            QMessageBox.critical(
                main_window,
                "Invalid Force Value",
                f"Invalid force input at point {point_tuple}: '{values.get('force')}'. "
                "Please enter a valid numeric value."
            )
            logger.exception(f"Invalid force value at {point_tuple}")
            return

        # Direction validation 
        try:
            vector = values.get('vector', {})
            vector_value = [float(vector.get(axis, 0.0)) for axis in ["X", "Y", "Z"]]
        except (ValueError, TypeError):
            QMessageBox.critical(
                main_window,
                "Invalid Direction Value",
                f"Invalid direction components at point {point_tuple}: {vector}. "
                "Please ensure all components are valid numbers."
            )
            logger.exception(f"Invalid direction at {point_tuple}")
            return

        if all(v == 0.0 for v in vector_value):
            QMessageBox.critical(
                main_window,
                "Invalid Direction Vector",
                f"Direction vector at point {point_tuple} is all zeros. "
                "Please enter a non-zero direction."
            )
            logger.warning(f"Zero direction vector at {point_tuple} - solver aborted.")
            return

        # All good -> add to list 
        forces.append((point_tuple, force_value, vector_value))
        logger.debug(f"Force point {point_tuple}: value={force_value}, vector={vector_value}")


    try:
        # Material validation
        if not app_context.get_app_state().get_selected_material() or \
           app_context.get_app_state().get_selected_material() == "None":
            raise ValueError("No material selected for FEM analysis.")
        if not forces:
            raise ValueError("No valid force points provided.")

        # Boundary 
        selected_axis = _get_selected_boundary_axis(sidebar)
        boundary_direction = _get_selected_boundary_direction(sidebar)

        # Solve 
        solver = FEMPointSolver()
        xdmf_file = solver.generate_and_solve(
            app_context.get_app_state().get_current_file(),
            forces,
            app_context.get_app_state().get_selected_material(),
            app_context.get_app_state().get_selected_boundary_point(),
            selected_axis,
            boundary_direction
        )

        # Post solve, load solution
        _load_solution_into_renderer(xdmf_file)
        logger.info("FEM point load solved successfully.")

    except Exception as e:
        QMessageBox.critical(main_window, "FEM Solving Error", f"Error during FEM solving: {e}")
        logger.exception("Error solving FEM with point load.")


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------
def _get_selected_boundary_axis(sidebar):
    """Return the currently selected boundary axis from the sidebar."""
    selected_axis = next(
        (axis for axis, checkbox in [
            ("X", sidebar.fem_section.checkbox_x_plane),
            ("Y", sidebar.fem_section.checkbox_y_plane),
            ("Z", sidebar.fem_section.checkbox_z_plane)
        ] if checkbox.isChecked()), None
    )
    if not selected_axis:
        raise ValueError("No boundary axis selected.")
    return selected_axis


def _get_selected_boundary_direction(sidebar):
    """Return the currently selected boundary direction from the sidebar."""
    boundary_direction = next(
        (direction for direction, checkbox in [
            ("<", sidebar.fem_section.checkbox_less_than),
            (">", sidebar.fem_section.checkbox_greater_than)
        ] if checkbox.isChecked()), None
    )
    if not boundary_direction:
        raise ValueError("No boundary direction selected.")
    return boundary_direction


def _load_solution_into_renderer(xdmf_file):
    """
    Load the solved FEM result XDMF file into the renderer and
    switch the sidebar back to 'View' mode.
    """
    sidebar = app_context.get_sidebar()
    app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(xdmf_file)
    app_context.get_app_state().set_current_file(xdmf_file)
    if sidebar:
        sidebar.mode_selector.setCurrentIndex(0)
    logger.debug("FEM solution loaded into renderer and sidebar switched to 'View' mode.")







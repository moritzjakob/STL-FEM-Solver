# -----------------------------------------------------------------------------
# Sidebar FEM Boundary Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller manages boundary selection, visualization and mesh coloring
#   in the FEM mode of the application.
#
#   Core functionality includes:
#       - Toggling boundary selection mode
#       - Disabling other selection modes (point, facets, paint)
#       - Rendering and removing boundary planes interactively
#       - Coloring mesh based on cutting plane (less/greater regions)
#       - Resetting boundary states and actors
# -----------------------------------------------------------------------------


import logging
import vtk
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_stl_file
from fem_app.gui.controller.sidebar_fem_force_controller import (
    disable_point_selection,
    disable_facets_selection,
    disable_facets_paint
)

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)



# -------------------------------------------------------------------------
# Boundary Selection Mode
# -------------------------------------------------------------------------
def toggle_boundary_selection():
    """
    Toggle boundary point selection mode ON/OFF.
    Ensures that other conflicting selection modes are disabled first.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    # Validate file
    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded. Cannot toggle boundary selection.")
        return

    # Validate renderer
    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot toggle boundary selection.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    # Disable other selection modes
    if app_context.get_app_state().is_point_selection_enabled():
        disable_point_selection()
    if app_context.get_app_state().is_facets_selection_enabled():
        disable_facets_selection()
    if app_context.get_app_state().is_facets_paint_enabled():
        disable_facets_paint()

    # Toggle boundary selection mode
    try:
        if not app_context.get_app_state().is_boundary_selection_enabled():
            app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_boundary_selector_interactor()
            app_context.get_app_state().enable_boundary_selection(True)

            if sidebar and hasattr(sidebar.fem_section, "button_boundary_condition"):
                sidebar.fem_section.button_boundary_condition.setText("Disable Boundary Selection")

            logger.info("Boundary selection mode enabled.")
        else:
            app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
            app_context.get_app_state().enable_boundary_selection(False)

            if sidebar and hasattr(sidebar.fem_section, "button_boundary_condition"):
                sidebar.fem_section.button_boundary_condition.setText("Select Boundary Conditions")

            logger.info("Boundary selection mode disabled.")
    except Exception as e:
        logger.exception("Failed to toggle boundary selection mode.")
        if main_window:
            QMessageBox.critical(main_window, "Boundary Selection Error", f"Failed to toggle boundary selection: {e}")


def disable_boundary_selection():
    """
    Disable boundary selection and restore the default interactor.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot disable boundary selection.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
        app_context.get_app_state().enable_boundary_selection(False)

        if sidebar and hasattr(sidebar.fem_section, "button_boundary_condition"):
            sidebar.fem_section.button_boundary_condition.setText("Select Boundary Conditions")

        logger.info("Boundary selection disabled and default interactor restored.")
    except Exception as e:
        logger.exception("Failed to disable boundary selection.")
        if main_window:
            QMessageBox.critical(main_window, "Boundary Selection Error", f"Failed to disable boundary selection: {e}")


# -------------------------------------------------------------------------
# Boundary Plane Rendering & Coloring
# -------------------------------------------------------------------------
def update_boundary_coloring():
    """
    Colors the mesh based on the currently selected boundary point and axis.
    A cutting plane is created at the selected position and the mesh is split
    into 'less than' and 'greater than' regions for visualization.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    # Validate renderer
    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot update boundary coloring.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    # Validate boundary selection
    if app_context.get_app_state().get_selected_boundary_coords is None:
        logger.warning("No boundary point selected for coloring.")
        return

    # Determine axis
    axis = None
    if sidebar.fem_section.checkbox_x_plane.isChecked():
        axis = "x"
    elif sidebar.fem_section.checkbox_y_plane.isChecked():
        axis = "y"
    elif sidebar.fem_section.checkbox_z_plane.isChecked():
        axis = "z"

    if axis is None:
        logger.warning("No axis selected for boundary coloring.")
        return

    # Remove previous plane
    if app_context.get_app_state().get_selected_boundary_point() is not None:
        remove_plane()

    # Render new plane
    coords = app_context.get_app_state().get_selected_boundary_coords()
    if coords is None:
        logger.warning("No boundary coordinates available for coloring.")
        return

    axis_map = {"x": 0, "y": 1, "z": 2}

    if axis not in axis_map:
        logger.warning(f"Invalid axis '{axis}' for boundary coloring.")
        return

    # Schutz: prüfen ob Index im coords-Bereich ist
    idx = axis_map[axis]
    if idx >= len(coords):
        logger.error(f"Axis index {idx} out of range for coords {coords}")
        return

    render_plane(coords[idx], axis)
    app_context.get_app_state().set_selected_boundary_point(coords[idx])
    # Ensure actor exists
    if app_context.get_app_state().get_selected_boundary_plane_actor() is None:
        logger.warning("No boundary plane actor found after rendering.")
        return

    # Determine direction
    is_less_than_checked = sidebar.fem_section.checkbox_less_than.isChecked()
    is_greater_than_checked = sidebar.fem_section.checkbox_greater_than.isChecked()
    position = app_context.get_app_state().get_selected_boundary_point()

    # Adjust position if on bounds
    actor = app_context.get_renderer_state().get_actor()
    input_data = actor.GetMapper().GetInput()
    bounds = input_data.GetBounds()  

    epsilon = 1e-6

    if axis == "x":
        if abs(position - bounds[1]) < epsilon:
            position -= epsilon  
        elif abs(position - bounds[0]) < epsilon:
            position += epsilon  
    elif axis == "y":
        if abs(position - bounds[3]) < epsilon:
            position -= epsilon
        elif abs(position - bounds[2]) < epsilon:
            position += epsilon
    elif axis == "z":
        if abs(position - bounds[5]) < epsilon:
            position -= epsilon
        elif abs(position - bounds[4]) < epsilon:
            position += epsilon


    # Cutting plane 
    cutting_plane = vtk.vtkPlane()
    if axis == "x":
        cutting_plane.SetNormal(1, 0, 0)
        cutting_plane.SetOrigin(position, 0, 0)
    elif axis == "y":
        cutting_plane.SetNormal(0, 1, 0)
        cutting_plane.SetOrigin(0, position, 0)
    elif axis == "z":
        cutting_plane.SetNormal(0, 0, 1)
        cutting_plane.SetOrigin(0, 0, position)
    
    less_than_mapper, greater_than_mapper = color_mesh_by_boundary(cutting_plane, position, axis)

    # Remove old boundary actor
    if app_context.get_app_state().get_selected_boundary_space_actor() is not None:
        app_context.get_renderer_state().get_renderer().RemoveActor(
            app_context.get_app_state().get_selected_boundary_space_actor()
        )
        app_context.get_app_state().set_selected_boundary_space_actor(None)

    # Add actor for selected direction
    actor = vtk.vtkActor()
    if is_less_than_checked:
        actor.SetMapper(less_than_mapper)
    elif is_greater_than_checked:
        actor.SetMapper(greater_than_mapper)
    else:
        logger.warning("No direction selected for boundary coloring.")
        return

    actor.GetProperty().SetColor(0.3, 0.3, 1)
    actor.GetProperty().SetOpacity(1.0)
    app_context.get_renderer_state().get_renderer().AddActor(actor)
    app_context.get_app_state().set_selected_boundary_space_actor(actor)

    app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()
    logger.info("Boundary coloring updated for axis '%s' at position %s", axis, position)


def render_plane(position, plane_axis):
    """
    Render a cutting plane at the given position along the specified axis.
    """
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot render plane.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    interactor_style = app_context.get_renderer_state().get_interactor().GetInteractorStyle()
    if hasattr(interactor_style, "render_plane"):
        interactor_style.render_plane(position, plane_axis)
        logger.debug("Rendered boundary plane at %s along axis '%s'", position, plane_axis)
    else:
        logger.warning("Current interactor does not support plane rendering.")


def remove_plane():
    """
    Remove the previously rendered cutting plane if it exists.
    """
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot remove plane.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    interactor_style = app_context.get_renderer_state().get_interactor().GetInteractorStyle()
    if hasattr(interactor_style, "remove_plane"):
        interactor_style.remove_plane()
        logger.debug("Boundary plane removed.")
    else:
        logger.warning("Current interactor does not support plane removal.")


def reset_boundary_plane():
    """
    Remove the actor of the boundary plane from the renderer and reset the selection state.
    """
    main_window = app_context.get_main_window()

    try:
        actor = app_context.get_app_state().get_selected_boundary_space_actor()
        if actor is not None:
            app_context.get_renderer_state().get_renderer().RemoveActor(actor)
            app_context.get_app_state().set_selected_boundary_space_actor(None)

        logger.info("Boundary plane reset successfully.")
    except Exception as e:
        logger.exception("Failed to reset boundary plane.")
        QMessageBox.critical(main_window, "Boundary Plane Reset Error", f"Error resetting the boundary plane: {e}")


def color_mesh_by_boundary(plane, position, axis):
    """
    Divide the mesh into two parts based on the clipping plane and return
    the mappers for both parts (less than / greater than).
    """
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot color mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return None, None

    try:
        input_data = app_context.get_renderer_state().actor.GetMapper().GetInput()

        # Less than region
        clipper_less = vtk.vtkClipPolyData()
        clipper_less.SetInputData(input_data)
        clipper_less.SetClipFunction(plane)
        clipper_less.InsideOutOn()
        clipper_less.Update()

        # Greater than region
        clipper_greater = vtk.vtkClipPolyData()
        clipper_greater.SetInputData(input_data)
        clipper_greater.SetClipFunction(plane)
        clipper_greater.InsideOutOff()
        clipper_greater.Update()

        # Mappers
        less_than_mapper = vtk.vtkPolyDataMapper()
        less_than_mapper.SetInputConnection(clipper_less.GetOutputPort())

        greater_than_mapper = vtk.vtkPolyDataMapper()
        greater_than_mapper.SetInputConnection(clipper_greater.GetOutputPort())

        logger.debug("Mesh successfully clipped at %s on axis '%s'", position, axis)
        return less_than_mapper, greater_than_mapper

    except Exception as e:
        logger.exception("Failed to color mesh by boundary.")
        if main_window:
            QMessageBox.critical(main_window, "Mesh Coloring Error", f"Failed to color mesh: {e}")
        return None, None



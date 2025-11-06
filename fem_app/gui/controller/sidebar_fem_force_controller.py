# -----------------------------------------------------------------------------
# Sidebar FEM Force Controller 
# -----------------------------------------------------------------------------
# Description:
#   Controller functions for the FEM sidebar related to load definitions.
#
#   Core functionality includes:
#       - Switching between point and area load UI
#       - Updating direction vectors and point vector components
#       - Enabling/disabling point selection mode
#       - Updating point load values
#       - Confirmation dialog for deleting a point
#       - Managing points (remove, reset, refresh scroll UI)
#       - Point highlighting from the scroll list
#       - Rendering/removing vector arrows
#       - Determining arrow scaling from mesh bounds
#       - Facet selection mode on/off
#       - Facet paint mode on/off
#       - Enabling/disabling while deactivating conflicting modes
#       - Resetting facets (button/programmatically)
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_stl_file
from fem_app.gui.controller.view_utils_controller import enable_default_interactor

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Force Type (Point vs Area)
# -----------------------------------------------------------------------------
def update_force_type():
    """
    Switch between 'Point Force' and 'Area Force' UI modes.
    Adjusts interactor and visible UI groups accordingly.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    if sidebar is None:
        logger.warning("Sidebar not available. Cannot update force type.")
        return

    try:
        force_type = sidebar.fem_section.combo_box_force_type.currentText()

        enable_default_interactor()

        if force_type == "Point Force":
            sidebar.fem_section.refresh_scroll_area()
            reset_facets()  
            sidebar.fem_section.point_load_group.setVisible(True)
            sidebar.fem_section.area_load_group.setVisible(False)
            sidebar.fem_section.button_point_selection.setText("Select Points")
            logger.info("Switched to 'Point Force' mode.")
        elif force_type == "Area Force":
            reset_points()         
            remove_vector_arrow()  
            sidebar.fem_section.point_load_group.setVisible(False)
            sidebar.fem_section.area_load_group.setVisible(True)
            logger.info("Switched to 'Area Force' mode.")

    except Exception as e:
        logger.exception("Failed to update force type mode.")
        if main_window:
            QMessageBox.critical(main_window, "Force Type Error", f"Failed to update force type: {e}")


# -----------------------------------------------------------------------------
# Area Force – Dircetion Vector
# -----------------------------------------------------------------------------
def update_force_direction(axis: str, value: str):
    """
    Update the force direction vector component for a given axis (Area load).

    Parameters:

    axis : str
        "X", "Y" or "Z".
    value : str
        Numerical Value as String 
    """
    main_window = app_context.get_main_window()

    try:
        num = float(value) if value else 0.0
        app_context.get_app_state().force_direction[axis] = num
        logger.debug("Force direction updated: %s = %s", axis, num)
    except ValueError:
        logger.exception("Invalid value for force direction %s", axis)
        if main_window:
            QMessageBox.critical(
                main_window,
                "Invalid Direction Value",
                f"Invalid value for {axis} direction: {value}"
            )


# -----------------------------------------------------------------------------
# Point Force – Vector Component Update
# -----------------------------------------------------------------------------
def update_vector_value(index, axis, value):
    """
    Update a single vector component for a given point.

    Parameters:
    
    index : tuple
        The point (x, y, z) as a key in the state
     axis : str
        "X", "Y" or "Z".
    value : str
        Numerical Value as String 
    """
    main_window = app_context.get_main_window()

    try:
        num = float(value) if value else 0.0
        app_context.get_app_state().get_point_values().setdefault(
            index, {}
        ).setdefault('vector', {'X': 0.0, 'Y': 0.0, 'Z': 0.0})[axis] = num
        logger.debug("Updated vector component %s at point %s = %s", axis, index, num)
    except ValueError:
        logger.exception("Invalid vector component for %s at point %s", axis, index)
        if main_window:
            QMessageBox.critical(
                main_window,
                "Invalid Vector Component Error",
                f"Invalid value for vector component {axis}"
            )


# -----------------------------------------------------------------------------
# Point Selection – Toggle/Disable
# -----------------------------------------------------------------------------
def toggle_point_selection():
    """
    Toggle between enabling and disabling point selection mode for FEM.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    if app_context.get_app_state().is_facets_selection_enabled():
        disable_facets_selection()  
    if app_context.get_app_state().is_facets_paint_enabled():
        disable_facets_paint()     
    if app_context.get_app_state().is_boundary_selection_enabled():
        from fem_app.gui.controller.sidebar_fem_boundary_controller import disable_boundary_selection
        disable_boundary_selection()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("Point selection requires a valid STL file.")
        return

    try:
        if not app_context.get_app_state().is_point_selection_enabled():
            app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_point_selector_interactor()
            app_context.get_app_state().enable_point_selection(True)
            if sidebar and hasattr(sidebar.fem_section, "button_point_selection"):
                sidebar.fem_section.button_point_selection.setText("Disable Point Selection")
            logger.info("Point selection enabled.")
        else:
            app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
            app_context.get_app_state().enable_point_selection(False)
            if sidebar and hasattr(sidebar.fem_section, "button_point_selection"):
                sidebar.fem_section.button_point_selection.setText("Select Points")
            logger.info("Point selection disabled.")
    except Exception as e:
        logger.exception("Failed to toggle point selection.")
        if main_window:
            QMessageBox.critical(
                main_window,
                "Point Selection Error",
                f"Failed to toggle point selection: {e}"
            )


def disable_point_selection():
    """
    Disable point selection and reset to default interactor.
    """
    sidebar = app_context.get_sidebar()

    if app_context.get_renderer_state():
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
    app_context.get_app_state().enable_point_selection(False)

    if sidebar and hasattr(sidebar.fem_section, "button_point_selection"):
        sidebar.fem_section.button_point_selection.setText("Select Points")
    logger.info("Point selection disabled.")

# -----------------------------------------------------------------------------
# Point Force – Force value per point
# -----------------------------------------------------------------------------
def update_point_value(index, key, value):
    """
    Update the scalar force value for a given point.

    Parameters:

    index : tuple
        The point (x, y, z) as key in the state.
    key : str
        Typically "force".
    value : str
        Numeric value as string; empty strings are interpreted as 0.0.
    """
    main_window = app_context.get_main_window()

    try:
        num = float(value) if value else 0.0
        app_context.get_app_state().get_point_values().setdefault(index, {})[key] = num
        logger.debug("Updated point value: %s[%s] = %s", index, key, num)
    except ValueError:
        logger.exception("Invalid value for force at point %s", index)
        if main_window:
            readable_index = tuple(float(c) for c in index)
            QMessageBox.critical(
                main_window,
                "Invalid Value Error",
                f"Invalid value for force at point {readable_index}: {value}"
            )


# -----------------------------------------------------------------------------
# Point Force – Delete with confirmation
# -----------------------------------------------------------------------------
def confirm_delete_point(point_tuple):
    """
    Ask the user before deleting a selected point (confirmation dialog).
    Calls remove_point(point_tuple) on confirmation.
    """
    main_window = app_context.get_main_window()

    if main_window is None:
        logger.warning("Main window not available. Cannot confirm delete point.")
        return

    reply = QMessageBox.question(
        main_window,
        "Delete Point",
        f"Do you really want to delete point ({point_tuple[0]:.7f}, {point_tuple[1]:.7f}, {point_tuple[2]:.7f})?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )

    if reply == QMessageBox.Yes:
        remove_point(point_tuple)  # implemented in Part 2/3


# -----------------------------------------------------------------------------
# Point management
# -----------------------------------------------------------------------------
def remove_point(point_tuple):
    """
    Remove a selected point from application state, renderer, and sidebar UI.

    Parameters:

    point_tuple : tuple
        The point key (x, y, z) as stored in AppState.
    """
    sidebar = app_context.get_sidebar()
    renderer_state = app_context.get_renderer_state()

    # 1. Remove from state
    app_context.get_app_state().get_point_values().pop(point_tuple, None)

    # 2. Remove highlight actor from renderer
    if point_tuple in app_context.get_app_state().get_highlighted_points_actor():
        actor = app_context.get_app_state().get_highlighted_points_actor().pop(point_tuple)
        if renderer_state and renderer_state.get_renderer():
            renderer_state.get_renderer().RemoveActor(actor)

    # 3. Refresh sidebar UI
    if sidebar and hasattr(sidebar, "fem_section"):
        sidebar.fem_section.refresh_scroll_area()

    # 4. Re-render
    if renderer_state and renderer_state.get_renderer():
        renderer_state.get_renderer().GetRenderWindow().Render()

    logger.info("Deleted point %s and updated renderer/UI", point_tuple)


def highlight_from_scroll(point_tuple):
    """
    Highlight a point (yellow) when the corresponding entry is clicked in the
    scroll area. All other highlighted points are shown in red.

    Parameters:

    point_tuple : tuple
        The point key (x, y, z) as stored in AppState.
    """
    renderer_state = app_context.get_renderer_state()
    if not renderer_state or not renderer_state.get_renderer():
        logger.warning("Renderer not available - cannot highlight point from scroll.")
        return

    actors_map = app_context.get_app_state().get_highlighted_points_actor()
    if point_tuple not in actors_map:
        logger.debug("No actor found for point %s", point_tuple)
        return

    # Set all to red
    for actor in actors_map.values():
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red

    # Set the selected one to yellow
    highlight_actor = actors_map[point_tuple]
    highlight_actor.GetProperty().SetColor(1.0, 1.0, 0.0)  # yellow

    renderer_state.get_renderer().GetRenderWindow().Render()
    logger.debug("Highlighted point %s from scroll", point_tuple)


def update_point_scroll_area(point, selected=True):
    """
    Update the list of selected points in AppState and refresh the scroll UI.

    Parameters:
    
    point : Iterable[float]
        Point coordinate (x, y, z).
    selected : bool
        True -> add/update point, False -> remove point.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    try:
        point_tuple = tuple(point)
        if selected:
            app_context.get_app_state().get_point_values().setdefault(
                point_tuple,
                {'force': 0.0, 'vector': {'X': 0.0, 'Y': 0.0, 'Z': 0.0}}
            )
        else:
            app_context.get_app_state().get_point_values().pop(point_tuple, None)

        if sidebar and hasattr(sidebar, "fem_section"):
            sidebar.fem_section.refresh_scroll_area()

        logger.debug("Point scroll area updated. Selected=%s, point=%s", selected, point_tuple)

    except Exception as e:
        logger.exception("Failed to update scroll area for point %s", point)
        if main_window:
            QMessageBox.critical(
                main_window,
                "Scroll Area Update Error",
                f"Error updating scroll area for point {point}: {e}"
            )


def reset_points():
    """
    Reset all selected points and remove their highlight actors from the renderer.
    """
    main_window = app_context.get_main_window()
    renderer_state = app_context.get_renderer_state()

    try:
        if renderer_state and renderer_state.get_renderer():
            for actor in app_context.get_app_state().get_highlighted_points_actor().values():
                renderer_state.get_renderer().RemoveActor(actor)

        app_context.get_app_state().get_highlighted_points_actor().clear()
        app_context.get_app_state().get_point_values().clear()

        logger.info("Points reset successfully.")
    except Exception as e:
        logger.exception("Failed to reset points.")
        if main_window:
            QMessageBox.critical(main_window, "Point Reset Error", f"Error resetting points: {e}")


def reset_points_button():
    """
    Reset points (button action): removes all point-related actors,
    clears the state, refreshes the scroll list, and resets the interactor.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()
    renderer_state = app_context.get_renderer_state()

    try:
        if renderer_state and renderer_state.get_renderer():
            for actor in app_context.get_app_state().get_highlighted_points_actor().values():
                renderer_state.get_renderer().RemoveActor(actor)

        app_context.get_app_state().get_highlighted_points_actor().clear()
        app_context.get_app_state().get_point_values().clear()

        if sidebar and hasattr(sidebar, "fem_section"):
            sidebar.fem_section.refresh_scroll_area()
            app_context.get_app_state().enable_point_selection(False)
            sidebar.fem_section.button_point_selection.setText("Select Points")

        if renderer_state and renderer_state.get_renderer():
            renderer_state.get_renderer().GetRenderWindow().Render()

        # Reset interactor to default
        enable_default_interactor()

        logger.info("Points reset via button successfully.")
    except Exception as e:
        logger.exception("Failed to reset points via button.")
        if main_window:
            QMessageBox.critical(main_window, "Point Reset Error", f"Error resetting points: {e}")

# -----------------------------------------------------------------------------
# Vector arrows (visualization)
# -----------------------------------------------------------------------------
def render_vector_arrow():
    """
    Render force vector arrows for all selected points stored in AppState.
    Arrows are scaled proportionally to the mesh size.
    """
    main_window = app_context.get_main_window()

    if (app_context.get_renderer_state() is None or
        app_context.get_renderer_state().get_renderer_controller().appearance is None):
        logger.warning("Renderer state or appearance not available. Cannot render arrows.")
        return
    
    app_context.get_renderer_state().get_renderer_controller().appearance.remove_arrow_actors()

    scale = compute_arrow_scale()

    for point_tuple, values in app_context.get_app_state().get_point_values().items():
        try:
            vector = values.get("vector", {})
            vx, vy, vz = vector.get("X", 0.0), vector.get("Y", 0.0), vector.get("Z", 0.0)

            if vx == 0.0 and vy == 0.0 and vz == 0.0:
                continue

            app_context.get_renderer_state().get_renderer_controller().appearance.add_arrow(
                point_tuple, (vx, vy, vz), scale_factor=scale
            )

            logger.debug("Rendered arrow at %s with vector (%s, %s, %s)", point_tuple, vx, vy, vz)

        except Exception as e:
            logger.exception("Failed to render vector arrow at %s", point_tuple)
            if main_window:
                QMessageBox.critical(
                    main_window,
                    "Arrow Rendering Error",
                    f"Failed to render arrow at {point_tuple}: {e}"
                )


def compute_arrow_scale():
    """
    Compute a suitable scale factor for vector arrows based on mesh bounds.

    Returns:
    float - Arrow length scale relative to mesh size (fallback 1.0).
    """
    renderer_state = app_context.get_renderer_state()
    appearance = None
    if renderer_state and renderer_state.get_renderer_controller():
        appearance = renderer_state.get_renderer_controller().appearance

    if not appearance:
        logger.warning("Renderer appearance not available. Using fallback scale factor.")
        return 1.0

    bounds = appearance.get_mesh_bounds()
    if bounds is None:
        logger.warning("Mesh bounds not found. Using fallback scale factor.")
        return 1.0

    x_size = bounds[1] - bounds[0]
    y_size = bounds[3] - bounds[2]
    z_size = bounds[5] - bounds[4]
    max_dim = max(x_size, y_size, z_size)

    # Adjust factor to control relative arrow size
    scale = max_dim * 0.08
    logger.debug("Arrow scale computed based on mesh bounds: %s", scale)
    return scale


def remove_vector_arrow():
    """
    Remove all rendered vector arrow actors from the scene.
    """
    main_window = app_context.get_main_window()
    renderer_state = app_context.get_renderer_state()

    if (not renderer_state or
        not renderer_state.get_renderer_controller() or
        not renderer_state.get_renderer_controller().appearance):
        logger.warning("Renderer state or appearance not available. Cannot remove arrows.")
        return

    try:
        renderer_state.get_renderer_controller().appearance.remove_arrow_actors()
        logger.info("All vector arrows removed from scene.")
    except Exception as e:
        logger.exception("Failed to remove vector arrows.")
        if main_window:
            QMessageBox.critical(main_window, "Arrow Error", f"Failed to remove vector arrows: {e}")


# -----------------------------------------------------------------------------
# Facet selection (Area-Load) – toggle mode
# -----------------------------------------------------------------------------
def toggle_facets_selection():
    """
    Toggle facet selection mode in Area Force mode.
    Disables conflicting modes beforehand (Paint, Point, Boundary Selection).
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()
    renderer_state = app_context.get_renderer_state()

    if not renderer_state:
        logger.warning("Renderer state not available. Cannot toggle facets selection.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return
    print(app_context.get_app_state().cells_vertices_values)
    # Disable conflicting modes
    if app_context.get_app_state().is_facets_paint_enabled():
        disable_facets_paint()
    if app_context.get_app_state().is_point_selection_enabled():
        disable_point_selection()
    if app_context.get_app_state().is_boundary_selection_enabled():
        from fem_app.gui.controller.sidebar_fem_boundary_controller import disable_boundary_selection
        disable_boundary_selection()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded for facets selection.")
        return

    try:
        if not app_context.get_app_state().is_facets_selection_enabled():
            renderer_state.get_renderer_controller().interactor_manager.set_area_selector_interactor()
            app_context.get_app_state().enable_facets_selection(True)
            if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
                sidebar.fem_section.button_select_facet.setText("Disable Facet Selection")
            logger.info("Facet selection mode enabled.")
        else:
            renderer_state.get_renderer_controller().interactor_manager.set_default_interactor()
            app_context.get_app_state().enable_facets_selection(False)
            if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
                sidebar.fem_section.button_select_facet.setText("Select Facets")
            logger.info("Facet selection mode disabled.")
    except Exception as e:
        logger.exception("Failed to toggle facet selection.")
        if main_window:
            QMessageBox.critical(main_window, "Facet Selection Error", f"Failed to toggle facet selection: {e}")


# -----------------------------------------------------------------------------
# Facet paint (Area-Load) – toggle mode
# -----------------------------------------------------------------------------
def toggle_facets_paint():
    """
    Toggle facet paint selection mode.
    Disables conflicting modes beforehand (Facet-Selection, Point, Boundary).
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()
    renderer_state = app_context.get_renderer_state()

    if not renderer_state:
        logger.warning("Renderer state not available. Cannot toggle facets paint.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    # Disable conflicting modes
    if app_context.get_app_state().is_facets_selection_enabled():
        disable_facets_selection()
    if app_context.get_app_state().is_point_selection_enabled():
        disable_point_selection()
    if app_context.get_app_state().is_boundary_selection_enabled():
        from fem_app.gui.controller.sidebar_fem_boundary_controller import disable_boundary_selection
        disable_boundary_selection()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded for facet painting.")
        return

    try:
        if not app_context.get_app_state().is_facets_paint_enabled():
            renderer_state.get_renderer_controller().interactor_manager.set_area_paint_selector_interactor()
            app_context.get_app_state().enable_facets_paint(True)
            if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
                sidebar.fem_section.button_paint_facet.setText("Disable Facet Painting")
            logger.info("Facet paint mode enabled.")
        else:
            renderer_state.get_renderer_controller().interactor_manager.set_default_interactor()
            app_context.get_app_state().enable_facets_paint(False)
            if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
                sidebar.fem_section.button_paint_facet.setText("Paint Facets")
            logger.info("Facet paint mode disabled.")
    except Exception as e:
        logger.exception("Failed to toggle facet paint mode.")
        if main_window:
            QMessageBox.critical(main_window, "Facet Paint Error", f"Failed to toggle facet paint mode: {e}")


# -----------------------------------------------------------------------------
# Disable helpers
# -----------------------------------------------------------------------------
def disable_facets_selection():
    """
    Disable facet selection mode and reset interactor to default.
    """
    sidebar = app_context.get_sidebar()
    renderer_state = app_context.get_renderer_state()

    if renderer_state:
        renderer_state.get_renderer_controller().interactor_manager.set_default_interactor()
    app_context.get_app_state().enable_facets_selection(False)

    if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
        sidebar.fem_section.button_select_facet.setText("Select Facets")

    logger.info("Facet selection disabled.")


def disable_facets_paint():
    """
    Disable facet paint mode and reset interactor to default.
    """
    sidebar = app_context.get_sidebar()
    renderer_state = app_context.get_renderer_state()

    if renderer_state:
        renderer_state.get_renderer_controller().interactor_manager.set_default_interactor()
    app_context.get_app_state().enable_facets_paint(False)

    if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
        sidebar.fem_section.button_paint_facet.setText("Paint Facets")

    logger.info("Facet painting disabled.")


# -----------------------------------------------------------------------------
# Reset facets
# -----------------------------------------------------------------------------
def reset_facets():
    """
    Remove all facet highlight actors from the renderer,
    clear facet-related states, and reset UI/flags.
    Used, among others, when switching modes or during load operations.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()
    renderer_state = app_context.get_renderer_state()

    try:
        if renderer_state and renderer_state.get_renderer():
            for actor in app_context.get_app_state().get_highlighted_cells_actor().values():
                renderer_state.get_renderer().RemoveActor(actor)

        app_context.get_app_state().get_highlighted_cells_actor().clear()
        app_context.get_app_state().get_cells_vertices_values().clear()
        app_context.get_app_state().enable_facets_paint(False)
        app_context.get_app_state().enable_facets_selection(False)

        if sidebar and hasattr(sidebar, "fem_section") and sidebar.fem_section:
            try:
                if hasattr(sidebar.fem_section, "button_select_facet") and sidebar.fem_section.button_select_facet:
                    sidebar.fem_section.button_select_facet.setText("Select Facets")
                if hasattr(sidebar.fem_section, "button_paint_facet") and sidebar.fem_section.button_paint_facet:
                    sidebar.fem_section.button_paint_facet.setText("Paint Facets")
            except RuntimeError:
                # Widget is already deleted - ignore
                logger.warning("Widgets already deleted. Ignoring reset.")
        # Optional rendering
        if renderer_state and renderer_state.get_renderer():
            renderer_state.get_renderer().GetRenderWindow().Render()

        logger.info("Facets reset successfully.")
    except Exception as e:
        logger.exception("Failed to reset facets.")
        QMessageBox.critical(main_window, "Facet Reset Error", f"Error resetting facets: {e}")


def reset_facets_button():
    """
    Button action: reset facets, render the scene, and
    reset the interactor to default.
    """
    main_window = app_context.get_main_window()
    renderer_state = app_context.get_renderer_state()

    try:
        if renderer_state and renderer_state.get_renderer():
            for actor in app_context.get_app_state().get_highlighted_cells_actor().values():
                renderer_state.get_renderer().RemoveActor(actor)

        app_context.get_app_state().get_highlighted_cells_actor().clear()
        app_context.get_app_state().get_cells_vertices_values().clear()

        if renderer_state and renderer_state.get_renderer():
            renderer_state.get_renderer().GetRenderWindow().Render()

        enable_default_interactor()

        logger.info("Facets reset via button successfully.")
    except Exception as e:
        logger.exception("Failed to reset facets via button.")
        QMessageBox.critical(main_window, "Facet Reset Error", f"Error resetting facets: {e}")




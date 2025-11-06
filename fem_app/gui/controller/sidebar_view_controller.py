# -----------------------------------------------------------------------------
# Sidebar View Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller manages all visualization-related actions for FEM results
#   displayed through the sidebar "View" section.
#
#   Core functionality includes:
#       - Reload visualization modes without reloading the mesh
#       - Reset visualization to default (base mesh)
#       - Show Von Mises stress visualization (with optional min/max inputs)
#       - Show stress and strain tensor components
#       - Enable and control displacement visualization
#       - Displacement magnitude & overlay rendering
#       - Live displacement scaling (multiplier)
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_xdmf_file

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Visualization Reloading
# -------------------------------------------------------------------------
def reload_current_visualization():
    """
    Reload the current visualization mode stored in AppState.
    Does not reload the file - only updates the visualization state.

    Supported modes:
        - von_mises
        - stress
        - strain
        - displacement_magnitude
        - displacement_overlay
        - fallback: displacement
    """
    vis = app_context.get_app_state().get_current_visualization()

    if vis == "von_mises":
        load_von_mises_stress()
    elif vis == "stress":
        load_stress_component()
    elif vis == "strain":
        load_strain_component()
    elif vis == "displacement_magnitude":
        load_displacement_magnitude()
    elif vis == "displacement_overlay":
        load_displacement_overlay()
    else:
        load_displacement()


def reload_mesh():
    """
    Reload the base mesh without any visualization overlays.
    Used when resetting visualization to a clean state.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file in AppState. Cannot reload mesh.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot reload mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_app_state().set_current_visualization(None)
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(current_file)
        logger.info("Mesh reloaded from file: %s", current_file)
    except Exception as e:
        logger.exception("Failed to reload mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Mesh Error", f"Failed to reload mesh:\n{e}")


# -------------------------------------------------------------------------
# Von Mises Stress Visualization
# -------------------------------------------------------------------------
def load_von_mises_stress():
    """
    Load the mesh with Von Mises stress visualization.
    Min and max stress values can be provided by the user through the sidebar inputs.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file in AppState. Cannot load Von Mises stress.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load Von Mises stress.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    min_von_mises = None
    max_von_mises = None

    # Parse user input
    if sidebar is not None:
        min_text = sidebar.view_section.min_von_mises_input.text().strip()
        max_text = sidebar.view_section.max_von_mises_input.text().strip()

        if min_text:
            try:
                min_von_mises = float(min_text)
            except ValueError:
                QMessageBox.critical(main_window, "Input Error", "Invalid min value. Please enter a valid number.")
                return

        if max_text:
            try:
                max_von_mises = float(max_text)
            except ValueError:
                QMessageBox.critical(main_window, "Input Error", "Invalid max value. Please enter a valid number.")
                return

    # Load visualization
    try:
        app_context.get_app_state().set_current_visualization("von_mises")
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=True,
            apply_displacement=app_context.get_app_state().is_displacement_enabled(),
            show_displacement_color_map=False,
            min_von_mises=min_von_mises,
            max_von_mises=max_von_mises,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info(
            "Von Mises stress visualization loaded (min=%s, max=%s) from file: %s",
            min_von_mises, max_von_mises, current_file
        )
    except Exception as e:
        logger.exception("Failed to load Von Mises stress.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load Von Mises stress:\n{e}")


# -------------------------------------------------------------------------
# Stress & Strain Component Visualization
# -------------------------------------------------------------------------
def load_stress_component():
    """
    Load a specific stress tensor component selected in the sidebar.
    Maps the component name to the corresponding tensor index.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file set. Cannot load stress component.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load stress component.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    comp_map = {"xx": 0, "xy": 1, "xz": 2, "yy": 4, "yz": 5, "zz": 8}
    comp_name = sidebar.view_section.stress_component_combo.currentText()
    comp_index = comp_map[comp_name]

    try:
        app_context.get_app_state().set_current_visualization("stress")
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=False,
            apply_displacement=app_context.get_app_state().is_displacement_enabled(),
            show_stress=True,
            show_strain=False,
            stress_component=comp_index,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info("Stress component '%s' (index=%d) loaded from %s", comp_name, comp_index, current_file)
    except Exception as e:
        logger.exception("Failed to load stress component.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load stress component:\n{e}")


def load_strain_component():
    """
    Load a specific strain tensor component selected in the sidebar.
    Maps the component name to the corresponding tensor index.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file set. Cannot load strain component.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load strain component.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    comp_map = {"xx": 0, "xy": 1, "xz": 2, "yy": 4, "yz": 5, "zz": 8}
    comp_name = sidebar.view_section.strain_component_combo.currentText()
    comp_index = comp_map[comp_name]

    try:
        app_context.get_app_state().set_current_visualization("strain")
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=False,
            apply_displacement=app_context.get_app_state().is_displacement_enabled(),
            show_stress=False,
            show_strain=True,
            strain_component=comp_index,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info("Strain component '%s' (index=%d) loaded from %s", comp_name, comp_index, current_file)
    except Exception as e:
        logger.exception("Failed to load strain component.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load strain component:\n{e}")


# -------------------------------------------------------------------------
# Displacement Visualization
# -------------------------------------------------------------------------
def load_displacement():
    """
    Reload visualization with the current displacement state.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file set. Cannot load displacement.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load displacement.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=False,
            apply_displacement=app_context.get_app_state().is_displacement_enabled(),
            show_displacement_color_map=False,
            show_displacement_wireframe=False,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info(
            "Displacement visualization loaded (enabled=%s, multiplier=%s)",
            app_context.get_app_state().is_displacement_enabled(),
            app_context.get_app_state().get_displacement_multiplier()
        )
    except Exception as e:
        logger.exception("Failed to load displacement visualization.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load displacement:\n{e}")


def toggle_displacement():
    """
    Toggle displacement ON/OFF while keeping the current visualization mode active.
    Updates both the application state and the sidebar button text.
    """
    sidebar = app_context.get_sidebar()

    app_context.get_app_state().enable_displacement(
        not app_context.get_app_state().is_displacement_enabled()
    )

    if sidebar is not None and hasattr(sidebar.view_section, "button_displacement"):
        if app_context.get_app_state().is_displacement_enabled():
            sidebar.view_section.button_displacement.setText("Displacement ON")
        else:
            sidebar.view_section.button_displacement.setText("Displacement OFF")

    logger.info("Displacement toggled: %s", app_context.get_app_state().is_displacement_enabled())
    reload_current_visualization()


def update_displacement_multiplier(multiplicator):
    """
    Update the displacement multiplier to make deformation more or less visible.
    If displacement visualization is active, deformation is updated live.
    """
    main_window = app_context.get_main_window()
    app_context.get_app_state().set_displacement_multiplier(multiplicator)
    logger.info("Displacement multiplier set to %s", multiplicator)

    if not app_context.get_app_state().is_displacement_enabled():
        logger.debug("Displacement disabled — deformation not applied.")
        return

    if app_context.get_renderer_state() is None or \
       app_context.get_renderer_state().get_renderer_controller().xdmf_handler is None:
        logger.warning("Renderer state not available. Cannot update displacement deformation.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    if hasattr(app_context.get_renderer_state(), "original_grid") and \
       app_context.get_renderer_state().get_original_grid() is not None:
        try:
            app_context.get_renderer_state().get_renderer_controller().xdmf_handler._apply_deformation_live(multiplicator)
            logger.info("Live deformation updated with multiplier %s", multiplicator)
        except Exception as e:
            logger.exception("Failed to apply live deformation.")
            if main_window:
                QMessageBox.critical(main_window, "Visualization Error", f"Failed to apply deformation:\n{e}")
    else:
        logger.warning("No original grid available. Cannot apply deformation.")


def load_displacement_magnitude():
    """
    Load the mesh with displacement magnitude coloring.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file set. Cannot load displacement magnitude.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load displacement magnitude.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_app_state().set_current_visualization("displacement_magnitude")
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=False,
            apply_displacement=app_context.get_app_state().is_displacement_enabled(),
            show_displacement_color_map=True,
            show_displacement_wireframe=False,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info("Displacement magnitude visualization loaded from file: %s", current_file)
    except Exception as e:
        logger.exception("Failed to load displacement magnitude visualization.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load displacement magnitude:\n{e}")


def load_displacement_overlay():
    """
    Load original mesh as wireframe and overlay deformed mesh colored by displacement magnitude.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file:
        logger.warning("No current file set. Cannot load displacement overlay.")
        return

    if not is_xdmf_file(current_file):
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load displacement overlay.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_app_state().set_current_visualization("displacement_overlay")
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(
            current_file,
            show_von_mises=False,
            apply_displacement=True,
            show_displacement_color_map=False,
            show_displacement_wireframe=True,
            displacement_multiplier=app_context.get_app_state().get_displacement_multiplier()
        )
        logger.info("Displacement overlay visualization loaded from file: %s", current_file)
    except Exception as e:
        logger.exception("Failed to load displacement overlay visualization.")
        if main_window:
            QMessageBox.critical(main_window, "Visualization Error", f"Failed to load displacement overlay:\n{e}")



# -----------------------------------------------------------------------------
# Sidebar Edit Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller provides functionality for the "Edit" mode of the sidebar.
#
#   Core functionality includes:
#       - Enabling/disabling the movement interactor
#       - Resetting transformations
#       - Mesh refinement and saving
#       - Reloading meshes after modifications
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_xdmf_file, is_stl_file

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Movement Interactor
# -------------------------------------------------------------------------
def toggle_movement():
    """
    Toggle the movement interactor in Edit mode.
    Switch between the default interactor and the movement interactor.

    Raises:
        QMessageBox: If renderer or file context is invalid.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_xdmf_file(current_file):
        logger.warning("No valid XDMF file loaded. Cannot toggle movement interactor.")
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot toggle movement interactor.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        interactor_manager = app_context.get_renderer_state().get_renderer_controller().interactor_manager
        movement_enabled = app_context.get_app_state().is_movement_enabled()

        if not movement_enabled:
            interactor_manager.set_movement_interactor()
            app_context.get_app_state().set_movement_enabled(True)
            if sidebar and hasattr(sidebar.edit_section, "button_movement"):
                sidebar.edit_section.button_movement.setText("Disable Movement")
            logger.info("Movement interactor enabled.")
        else:
            interactor_manager.set_default_interactor()
            app_context.get_app_state().set_movement_enabled(False)
            if sidebar and hasattr(sidebar.edit_section, "button_movement"):
                sidebar.edit_section.button_movement.setText("Enable Movement")
            logger.info("Movement interactor disabled.")

        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

    except Exception as e:
        logger.exception("Failed to toggle movement interactor.")
        if main_window:
            QMessageBox.critical(main_window, "Movement Error", f"Failed to toggle movement: {e}")


def reset_movement():
    """
    Reload the opened XDMF file without the applied movement.
    Resets the interactor to the default mode and UI state.
    """
    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_xdmf_file(current_file):
        logger.warning("No valid XDMF file loaded. Cannot reset movement.")
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot reset movement.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        # Reload the XDMF file to restore original geometry
        controller = app_context.get_renderer_state().get_renderer_controller()
        controller.cleanup.reset_window()
        controller.xdmf_handler.load_xdmf(current_file)

        # Reset movement state and UI
        app_context.get_app_state().set_movement_enabled(False)
        if sidebar and hasattr(sidebar.edit_section, "button_movement"):
            controller.interactor_manager.set_default_interactor()
            sidebar.edit_section.button_movement.setText("Enable Movement")

        logger.info("Movement interactor reset and file reloaded: %s", current_file)

    except Exception as e:
        logger.exception("Failed to reset movement interactor.")
        if main_window:
            QMessageBox.critical(main_window, "Reset Error", f"Failed to reset the movement: {e}")


# -------------------------------------------------------------------------
# Mesh Refinement
# -------------------------------------------------------------------------
def refine_mesh():
    """
    Refine the currently loaded STL mesh by a fixed factor.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded. Cannot refine mesh.")
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot refine mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_renderer_state().get_renderer_controller().stl_handler.refine_mesh()
        logger.info("Mesh refinement applied to file: %s", current_file)

    except Exception as e:
        logger.exception("Failed to refine mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Unexpected Error", f"Failed to refine the mesh: {e}")


def save_refine_mesh():
    """
    Save the STL mesh with the current refinement applied.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded. Cannot save refined mesh.")
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot save refined mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        app_context.get_renderer_state().get_renderer_controller().stl_handler.save_refined_mesh(current_file)
        logger.info("Refined mesh saved to file: %s", current_file)

    except Exception as e:
        logger.exception("Failed to save refined mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Save Error", f"Failed to save the refined mesh: {e}")


def reset_refine_mesh():
    """
    Reload the STL file without the applied refinement.
    This effectively resets the mesh to its original state.
    """
    main_window = app_context.get_main_window()
    current_file = app_context.get_app_state().get_current_file()

    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded. Cannot reset refinement.")
        return

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot reset refinement.")
        if main_window:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        controller = app_context.get_renderer_state().get_renderer_controller()
        controller.cleanup.reset_window()
        controller.stl_handler.load_stl(current_file)
        controller.stl_handler.reset_refinement_of_mesh()
        logger.info("Refinement of STL mesh reset and file reloaded: %s", current_file)

    except Exception as e:
        logger.exception("Failed to reset refined mesh.")
        if main_window:
            QMessageBox.critical(main_window, "Reset Error", f"Failed to reset the refined mesh: {e}")






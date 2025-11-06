# -----------------------------------------------------------------------------
# Header Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller provides functional logic for the header UI widget.
#   It connects UI elements (sidebar toggle button, wireframe checkbox)
#   with the underlying renderer and application context.
#
#   Core functionality includes:
#       - Toggling sidebar visibility
#       - Toggling wireframe mode in the renderer
#       - Retrieving wireframe state
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Sidebar Controls
# -------------------------------------------------------------------------
def toggle_sidebar():
    """
    Toggle the visibility of the sidebar in the application.

    Raises:
        QMessageBox: If the sidebar is not accessible or if toggling fails.
    """
    logger.debug("Toggling sidebar visibility")

    main_window = app_context.get_main_window()
    sidebar = app_context.get_sidebar()

    if sidebar is None:
        logger.warning("Sidebar not registered. Cannot toggle visibility.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Sidebar Error", "Sidebar could not be accessed.")
        return

    try:
        sidebar.setVisible(not sidebar.isVisible())
        logger.info("Sidebar visibility toggled to %s", sidebar.isVisible())

    except Exception as e:
        logger.exception("Failed to toggle sidebar visibility.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Unexpected Error", f"Failed to toggle sidebar: {e}")


# -------------------------------------------------------------------------
# Wireframe Controls
# -------------------------------------------------------------------------
def toggle_wireframe():
    """
    Toggle the wireframe mode of the renderer.

    Raises:
        QMessageBox: If the renderer is not initialized or an error occurs.
    """
    logger.debug("Wireframe toggle state triggered")

    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot toggle wireframe.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    try:
        current_mode = app_context.get_renderer_state().get_wireframe_mode()
        app_context.get_renderer_state().get_renderer_controller().appearance.toggle_wireframe_mode(not current_mode)
        logger.info("Wireframe mode toggled to %s", not current_mode)

    except AttributeError as e:
        logger.exception("Renderer not properly initialized.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Renderer Error", f"Renderer not initialized:\n{e}")

    except Exception as e:
        logger.exception("Unexpected error while toggling wireframe.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Unexpected Error", str(e))


# -------------------------------------------------------------------------
# Wireframe State Getter
# -------------------------------------------------------------------------
def get_wireframe_state():
    """
    Return the current wireframe state from the renderer context.

    Returns:
        bool: True if wireframe mode is active, False otherwise.
    """
    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available when checking wireframe state.")
        return False

    try:
        state = app_context.get_renderer_state().get_wireframe_mode()
        logger.debug(f"Wireframe state retrieved: {state}")
        return state

    except Exception as e:
        logger.error(f"Failed to read wireframe state: {e}")
        return False






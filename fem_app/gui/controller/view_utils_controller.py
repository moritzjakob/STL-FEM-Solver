# -----------------------------------------------------------------------------
# View Utils Controller
# -----------------------------------------------------------------------------
# Description:
#   This module provides utility functions for handling global view actions
#   in the FEM GUI. 
#
#   Core functionality includes:
#       - Resetting the renderer window
#       - Re-enabling the default interactor
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------
def reset_window():
    """
    Reset the entire renderer window to its initial state.

    Raises:
        QMessageBox error dialogs if the renderer is not properly initialized.
    """
    main_window = app_context.get_main_window()

    if main_window is None or app_context.get_renderer_state() is None:
        logger.warning("Cannot reset window. Main window or renderer not initialized.")
        return

    try:
        app_context.get_renderer_state().get_renderer_controller().cleanup.reset_window()
        logger.info("Renderer window successfully reset.")

    except AttributeError as e:
        logger.exception("Renderer not properly initialized during reset.")
        QMessageBox.critical(
            main_window,
            "Initialization Error",
            f"Error: {e}\nEnsure vtk_renderer is properly initialized and reset_window is implemented."
        )

    except Exception as e:
        logger.exception("Unexpected error occurred during window reset.")
        QMessageBox.critical(
            main_window,
            "Unexpected Error",
            f"An unexpected error occurred during window reset: {e}"
        )


def enable_default_interactor():
    """
    Enable the default interactor style in the renderer.

    Raises:
        QMessageBox error dialogs if enabling the interactor fails.
    """
    main_window = app_context.get_main_window()

    try:
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
        logger.debug("Default interactor enabled.")
    except Exception as e:
        logger.exception("Failed to enable default interactor.")
        QMessageBox.critical(
            main_window,
            "Default Interactor Error",
            f"Failed to enable the default interactor: {e}"
        )



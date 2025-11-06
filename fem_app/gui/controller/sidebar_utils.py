# -----------------------------------------------------------------------------
# Sidebar Utilities Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller provides utility functions to manage the sidebar UI state
#   independently from the core FEM logic.
#
#   Core functionality includes:
#       - Resetting the global FEM application state
#       - Resetting sidebar UI elements (e.g. checkboxes, buttons)
#       - Ensuring sidebar state consistency after mesh or FEM state resets
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Sidebar Reset
# -------------------------------------------------------------------------
def reset_sidebar_state():
    """
    Reset the global FEM application state and bring all sidebar UI elements
    back to their default state.
    """
    # Reset global FEM state 
    try:
        app_context.get_app_state().reset()
        logger.info("FEMAppState reset via sidebar_utils.")
    except Exception as e:
        logger.exception("Failed to reset FEMAppState.")
        return

    # Reset sidebar UI 
    sidebar = app_context.get_sidebar()
    if sidebar is None:
        logger.warning("Sidebar not registered during state reset.")
        return


    # Reset UI elements 
    if hasattr(sidebar, "fem_section"):
        fem_section = sidebar.fem_section
        try:
            if hasattr(fem_section, "checkbox_draw") and fem_section.checkbox_draw is not None:
                fem_section.checkbox_draw.setChecked(False)

            if hasattr(fem_section, "button_boundary_condition") and fem_section.button_boundary_condition is not None:
                fem_section.button_boundary_condition.setChecked(False)

            if hasattr(fem_section, "button_point_selection") and fem_section.button_point_selection is not None:
                fem_section.button_point_selection.setChecked(False)

            logger.debug("Sidebar UI elements successfully reset to default.")
        except RuntimeError:
            # Widget is already deleted - ignore
            logger.warning("Widgets already deleted. Ignoring reset.")





# -----------------------------------------------------------------------------
# Sidebar FEM Materials Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller handles the material selection functionality in the
#   FEM sidebar. It updates the selected material in the global AppState
#   based on the current combo box selection.
#
#   Core functionality includes:
#       - Update selected material from UI combo box
#       - Ensure a valid STL file is loaded before updating
#       - Handle UI errors 
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.utils.file_utils import is_stl_file

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Material Selection
# -------------------------------------------------------------------------
def update_material():
    """
    Update the selected material in the AppState based on the
    combo box selection in the FEM sidebar.

    Preconditions:
        - A valid STL file must be loaded.
        - Sidebar and material combo box must be initialized.
    """
    sidebar = app_context.get_sidebar()
    main_window = app_context.get_main_window()

    # Validate mesh file
    current_file = app_context.get_app_state().get_current_file()
    if not current_file or not is_stl_file(current_file):
        logger.warning("No valid STL file loaded. Cannot update material.")
        return

    try:
        if sidebar is not None and hasattr(sidebar.fem_section, "combo_box_material"):
            selected_material = sidebar.fem_section.combo_box_material.currentText()
            app_context.get_app_state().set_selected_material(selected_material)
            logger.info("Selected material updated to '%s'", selected_material)
    except Exception as e:
        logger.exception("Failed to update selected material.")
        if main_window:
            QMessageBox.critical(main_window, "Material Error", f"Failed to update material: {e}")





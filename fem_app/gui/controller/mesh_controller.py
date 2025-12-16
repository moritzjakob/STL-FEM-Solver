# -----------------------------------------------------------------------------
# Mesh Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller manages mesh loading operations for the FEM application.
#   It serves as the central entry point for importing mesh data into the
#   renderer and resetting relevant states prior to loading.
#
#   Core functionality includes:
#       - Loading STL and XDMF mesh files
#       - Resetting FEM and renderer state before mesh import
#       - Handling UI sidebar state after loading
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context
from fem_app.gui.controller.sidebar_utils import reset_sidebar_state

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# STL File Loading
# -------------------------------------------------------------------------
def load_stl_file(file_path: str):
    """
    Load an STL file into the renderer and reset the application state beforehand.

    Args:
        file_path (str): Absolute path to the STL file.

    Steps:
        1. Validate renderer state
        2. Reset FEMAppState and renderer
        3. Load STL mesh via renderer controller
        4. Reset UI sidebar if present
    """
    logger.debug(f"Loading STL file: {file_path}")
    main_window = app_context.get_main_window()

    # Check if renderer is initialized
    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load STL file.")
        return

    try:
        # Reset application and UI state
        _reset_state_before_mesh_load()
        reset_sidebar_state()

        # Load STL mesh
        app_context.get_renderer_state().get_renderer_controller().stl_handler.load_stl(file_path)
        logger.info(f"STL file successfully loaded: {file_path}")

        # Optional UI updates
        _reset_sidebar_combo_box()

    except Exception as e:
        logger.exception("Failed to load STL file.")
        if main_window is not None:
            QMessageBox.critical(main_window, "File Error", f"Failed to load STL file:\n{e}")


# -------------------------------------------------------------------------
# XDMF File Loading
# -------------------------------------------------------------------------
def load_xdmf_file(file_path: str):
    """
    Load an XDMF file into the renderer and reset the application state beforehand.

    Args:
        file_path (str): Absolute path to the XDMF file.

    Steps:
        1. Validate renderer state
        2. Reset FEMAppState and renderer
        3. Load XDMF mesh via renderer controller
        4. Reset UI sidebar if present
    """
    logger.debug(f"Loading XDMF file: {file_path}")
    main_window = app_context.get_main_window()

    # Check if renderer is initialized
    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot load XDMF file.")
        return

    try:
        # Reset application and UI state
        _reset_state_before_mesh_load()
        reset_sidebar_state()

        # Load XDMF mesh
        app_context.get_renderer_state().get_renderer_controller().xdmf_handler.load_xdmf(file_path)
        logger.info(f"XDMF file successfully loaded: {file_path}")

        # Optional UI updates
        _reset_sidebar_combo_box()

    except Exception as e:
        logger.exception("Failed to load XDMF file.")
        if main_window is not None:
            QMessageBox.critical(main_window, "File Error", f"Failed to load XDMF file:\n{e}")


# -------------------------------------------------------------------------
# Shared Helpers
# -------------------------------------------------------------------------
def _reset_state_before_mesh_load():
    """
    Reset FEMAppState and renderer before loading a new mesh file.

    This ensures:
        - Clean FEM state
        - Renderer geometry is cleared
        - Old selections or results are removed
    """
    app_context.get_app_state().reset()
    logger.debug("FEMAppState reset before mesh load.")

    renderer_state = app_context.get_renderer_state()
    if hasattr(renderer_state, "clear_geometry"):
        renderer_state.clear_geometry()
        logger.debug("Renderer geometry cleared before mesh load.")


def _reset_sidebar_combo_box():
    """
    Reset the sidebar combo box to its default index if available.

    This is used to ensure that the sidebar UI reflects the clean state
    after loading a new mesh.
    """
    sidebar = app_context.get_sidebar()
    if sidebar is not None and hasattr(sidebar, "combo_box"):
        try:
            sidebar.combo_box.setCurrentIndex(0)
            logger.debug("Sidebar combo box reset to default state after mesh load.")
        except Exception as e:
            logger.warning(f"Failed to reset sidebar combo box: {e}")





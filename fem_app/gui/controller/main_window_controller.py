# -----------------------------------------------------------------------------
# Main Window Controller
# -----------------------------------------------------------------------------
# Description:
#   This controller provides high-level utility functions for file handling,
#   mesh color manipulation, and renderer background control.
#
#   It acts as the bridge between GUI actions in the main window (menu bar,
#   buttons) and core rendering logic in the application.
#
#   Core functionality includes:
#       - Opening and loading STL and XDMF files
#       - Changing mesh and background colors
#       - Handling renderer initialization checks and UI dialogs
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMessageBox, QColorDialog, QFileDialog
from fem_app.core.app_context import app_context
from fem_app.gui.controller.mesh_controller import load_stl_file, load_xdmf_file

# -------------------------------------------------------------------------
# Logger
# -------------------------------------------------------------------------
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# File Handling
# -------------------------------------------------------------------------
def open_stl_file():
    """
    Open a file dialog to select an STL file and load it into the renderer.

    Raises:
        QMessageBox: If the main window is not available or loading fails.
    """
    logger.debug("Opening STL file dialog")
    main_window = app_context.get_main_window()

    if main_window is None:
        logger.warning("Main window not registered. Cannot open STL file.")
        return

    file_name, _ = QFileDialog.getOpenFileName(
        main_window,
        "Open STL File",
        "",
        "STL Files (*.stl)"
    )

    if file_name:
        logger.info(f"STL file selected: {file_name}")
        try:
            load_stl_file(file_name)
        except Exception as e:
            logger.exception("Failed to load STL file.")
            QMessageBox.critical(main_window, "File Load Error", f"Failed to load STL file:\n{e}")


def open_xdmf_file():
    """
    Open a file dialog to select an XDMF file and load it into the renderer.

    Raises:
        QMessageBox: If the main window is not available or loading fails.
    """
    logger.debug("Opening XDMF file dialog")
    main_window = app_context.get_main_window()

    if main_window is None:
        logger.warning("Main window not registered. Cannot open XDMF file.")
        return

    file_name, _ = QFileDialog.getOpenFileName(
        main_window,
        "Open XDMF File",
        "",
        "XDMF Files (*.xdmf)"
    )

    if file_name:
        logger.info(f"XDMF file selected: {file_name}")
        try:
            load_xdmf_file(file_name)
        except Exception as e:
            logger.exception("Failed to load XDMF file.")
            QMessageBox.critical(main_window, "File Load Error", f"Failed to load XDMF file:\n{e}")


# -------------------------------------------------------------------------
# Color Controls
# -------------------------------------------------------------------------
def change_mesh_color():
    """
    Open a color dialog and update the mesh color in the renderer.

    Raises:
        QMessageBox: If the renderer is not initialized.
    """
    logger.debug("Changing mesh color via color dialog")
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot change mesh color.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    color = QColorDialog.getColor(parent=main_window)
    if color.isValid():
        rgb = (color.redF(), color.greenF(), color.blueF())
        app_context.get_renderer_state().get_renderer_controller().appearance.set_mesh_color(rgb)
        logger.info(f"Mesh color changed to RGB {rgb}")


def change_background_color():
    """
    Open a color dialog and update the renderer background color.

    Raises:
        QMessageBox: If the renderer is not initialized.
    """
    logger.debug("Changing background color via color dialog")
    main_window = app_context.get_main_window()

    if app_context.get_renderer_state() is None:
        logger.warning("Renderer state not available. Cannot change background color.")
        if main_window is not None:
            QMessageBox.critical(main_window, "Renderer Error", "Renderer not initialized.")
        return

    color = QColorDialog.getColor(parent=main_window)
    if color.isValid():
        rgb = (color.redF(), color.greenF(), color.blueF())
        app_context.get_renderer_state().get_renderer_controller().appearance.set_background_color(rgb)
        logger.info(f"Background color changed to RGB {rgb}")



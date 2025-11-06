# -----------------------------------------------------------------------------
# File Type Checker Utility
# -----------------------------------------------------------------------------
# Description:
#   Provides helper functions to validate file types used in the FEM app.
#   Currently supports:
#     - STL files for mesh generation
#     - XDMF files for simulation results
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import os
from typing import Optional

from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context

logger = logging.getLogger(__name__)


def is_stl_file(file_path: str) -> bool:
    """
    Check if the given file path points to a valid STL file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        True if the file has a '.stl' extension (case-insensitive),
        False otherwise.

    Side Effects:
        Displays a GUI error dialog if the application has a main window,
        otherwise logs an error message.
    """
    _, extension = os.path.splitext(file_path)
    if extension.lower() == ".stl":
        logger.debug("File %s is a valid STL file.", file_path)
        return True

    _show_file_error(
        "The selected file is not an STL file.\nPlease select a valid STL file."
    )
    logger.warning("Invalid file type for STL: %s", extension)
    return False


def is_xdmf_file(file_path: str) -> bool:
    """
    Check if the given file path points to a valid XDMF file.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        True if the file has a '.xdmf' extension (case-insensitive),
        False otherwise.

    Side Effects:
        Displays a GUI error dialog if the application has a main window,
        otherwise logs an error message.
    """
    _, extension = os.path.splitext(file_path)
    if extension.lower() == ".xdmf":
        logger.debug("File %s is a valid XDMF file.", file_path)
        return True

    _show_file_error(
        "The selected file is not an XDMF file.\nPlease select a valid XDMF file."
    )
    logger.warning("Invalid file type for XDMF: %s", extension)
    return False


def _show_file_error(message: str) -> None:
    """
    Display an error message related to file validation.

    If a GUI main window is available, shows a modal error dialog.
    Otherwise logs the error message.

    Args:
        message: The message text to display or log.
    """
    main_window = app_context.get_main_window()
    if main_window is not None:
        QMessageBox.critical(main_window, "File Error", message)
    else:
        logger.error("File Error: %s (no GUI context available)", message)




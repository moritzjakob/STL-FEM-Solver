
# -----------------------------------------------------------------------------
# GUI Header Widget
# -----------------------------------------------------------------------------
# Description:
#   This widget represents the top header bar of the FEM application GUI.
#
# Features:
#       - Toggling the sidebar visibility
#       - Enabling/disabling wireframe rendering
#       - Displaying the application title 
#
#   This header is instantiated once in the main GUI window.
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QCheckBox
from PySide6.QtCore import Qt

# Context & Controller
from fem_app.core.app_context import app_context
from fem_app.gui.controller.header_controller import toggle_wireframe, get_wireframe_state, toggle_sidebar


class Header(QWidget):
    """
    Header
    ------
    GUI header bar containing:
        - Sidebar toggle button
        - Wireframe toggle checkbox
        - Application title label
    """

    def __init__(self):
        """
        Initialize the Header widget:
        - Sets up base layout
        - Creates UI elements (sidebar button, wireframe toggle, title)
        - Connects signals to controller functions
        """
        super().__init__()

        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Header widget initialized")

        # ---------------------------------------------------------------------
        # Base Layout Configuration
        # ---------------------------------------------------------------------
        self.setFixedHeight(40)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(15)

        # ---------------------------------------------------------------------
        # Sidebar Toggle Button
        # ---------------------------------------------------------------------
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(40, 30)
        self.toggle_button.clicked.connect(lambda: self._on_toggle_sidebar())
        header_layout.addWidget(self.toggle_button)
        self.logger.debug("Sidebar toggle button created")

        # ---------------------------------------------------------------------
        # Wireframe Mode Checkbox
        # ---------------------------------------------------------------------
        self.checkbox_wireframe = QCheckBox("Enable Wireframe Mode")
        self.checkbox_wireframe.setChecked(get_wireframe_state())
        self.checkbox_wireframe.stateChanged.connect(lambda: self._on_toggle_wireframe())
        header_layout.addWidget(self.checkbox_wireframe)
        self.logger.debug("Wireframe mode checkbox created")

        # ---------------------------------------------------------------------
        # Application Title 
        # ---------------------------------------------------------------------
        label_title = QLabel("FEM Solver")
        label_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(label_title, alignment=Qt.AlignmentFlag.AlignRight)
        self.logger.debug("Title label added")

        # ---------------------------------------------------------------------
        # Finalize Layout
        # ---------------------------------------------------------------------
        self.setLayout(header_layout)
        self.logger.debug("Header layout finalized")

    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    def _on_toggle_sidebar(self):
        """
        Toggle the sidebar panel visibility.
        """
        toggle_sidebar()
        self.logger.info("Sidebar visibility toggled")

    def _on_toggle_wireframe(self):
        """
        Toggle the wireframe rendering mode.
        """
        toggle_wireframe()
        state = "enabled" if self.checkbox_wireframe.isChecked() else "disabled"
        self.logger.info(f"Wireframe mode {state}")










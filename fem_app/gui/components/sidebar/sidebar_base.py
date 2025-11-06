# -----------------------------------------------------------------------------
# Sidebar Base Widget
# -----------------------------------------------------------------------------
# Description:
#   This class defines the base sidebar UI component of the FEM application.
#   It acts as a container for different mode sections:
#       - View  – for basic rendering controls
#       - Edit  – for object manipulation and scene editing
#       - FEM   – for simulation setup and boundary conditions
#
#   The sidebar uses a combo box for mode switching, and dynamically
#   rebuilds its content when a new mode is selected.
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QFrame, QVBoxLayout, QComboBox

# Sidebar mode sections
from fem_app.gui.components.sidebar.sidebar_view import SidebarView
from fem_app.gui.components.sidebar.sidebar_edit import SidebarEdit
from fem_app.gui.components.sidebar.sidebar_fem import SidebarFEM


class SidebarBase(QFrame):
    """
    SidebarBase
    -----------
    Base sidebar widget that manages mode switching between:
        - View: rendering and visualization options
        - Edit: object manipulation tools
        - FEM: simulation setup 

    Each mode section is defined in a separate class to keep the sidebar modular.
    """

    def __init__(self):
        """
        Initialize the base sidebar widget.
        Creates the mode selector, container layout, and mode sections.
        """
        super().__init__()

        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SidebarBase initialized")

        # ---------------------------------------------------------------------
        # Styling
        # ---------------------------------------------------------------------
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #f0f0f0;")

        # ---------------------------------------------------------------------
        # Layout Configuration
        # ---------------------------------------------------------------------
        layout = QVBoxLayout()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["View", "Edit", "FEM"])
        self.mode_selector.currentIndexChanged.connect(self.update_mode)
        layout.addWidget(self.mode_selector)
        self.logger.debug("Mode selector created with options: View, Edit, FEM")

        # Container for the active mode section
        self.widget_container = QVBoxLayout()
        layout.addLayout(self.widget_container)
        layout.addStretch()
        self.setLayout(layout)

        # ---------------------------------------------------------------------
        # Mode Sections
        # ---------------------------------------------------------------------
        self.view_section = SidebarView()
        self.edit_section = SidebarEdit()
        self.fem_section = SidebarFEM()
        self.logger.debug("Sidebar mode sections instantiated")

        # Load initial mode (View)
        self.update_mode()

    # -------------------------------------------------------------------------
    # Layout Handling
    # -------------------------------------------------------------------------
    def clear_container(self):
        """
        Remove all widgets and layouts from the container before loading a new mode.
        """
        self.logger.debug("Clearing sidebar container before switching mode")
        while self.widget_container.count():
            item = self.widget_container.takeAt(0)
            if item.widget():
                widget_name = item.widget().__class__.__name__
                self.logger.debug(f"Deleting widget: {widget_name}")
                item.widget().deleteLater()
            elif item.layout():
                layout_name = item.layout().__class__.__name__
                self.logger.debug(f"Clearing nested layout: {layout_name}")
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        """
        Recursively clear a layout and all its child widgets or layouts.
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                widget_name = child.widget().__class__.__name__
                self.logger.debug(f"Deleting child widget: {widget_name}")
                child.widget().deleteLater()
            elif child.layout():
                layout_name = child.layout().__class__.__name__
                self.logger.debug(f"Recursively clearing child layout: {layout_name}")
                self._clear_layout(child.layout())

    # -------------------------------------------------------------------------
    # Mode Switching
    # -------------------------------------------------------------------------
    def update_mode(self):
        """
        Switch the sidebar content based on the selected mode.
        This method clears the container and adds the layout of the new mode section.
        """
        mode = self.mode_selector.currentText()
        self.logger.info(f"Switching sidebar mode to: {mode}")

        # Clear current widgets before loading the new section
        self.clear_container()

        if mode == "View":
            self.logger.debug("Building 'View' mode layout")
            self.widget_container.addLayout(self.view_section.build())

        elif mode == "Edit":
            self.logger.debug("Building 'Edit' mode layout")
            self.widget_container.addLayout(self.edit_section.build())

        elif mode == "FEM":
            self.logger.debug("Building 'FEM' mode layout")
            self.widget_container.addLayout(self.fem_section.build())

        else:
            self.logger.warning(f"Unknown sidebar mode selected: {mode}")









# -----------------------------------------------------------------------------
# Main Application Window
# -----------------------------------------------------------------------------
# Description:
#   This module defines the MainWindow class, the central entry point for the GUI.
#   It sets up the main layout structure, integrates the renderer, sidebar,
#   header, and menubar, and initializes the application context.
#
# Features:
#   - Application header with global controls
#   - Sidebar for model settings and FEM operations
#   - Central VTK renderer for 3D visualization
#   - Menubar with file and view actions
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt

# GUI components
from fem_app.gui.components.header.header import Header
from fem_app.gui.components.sidebar.sidebar_base import SidebarBase as Sidebar

# Renderer
from fem_app.renderer.vtk_renderer import VTKRenderer

# Context & Controller
from fem_app.core.app_context import app_context
from fem_app.gui.controller.main_window_controller import (
    change_mesh_color,
    change_background_color,
    open_stl_file,
    open_xdmf_file
)
from fem_app.gui.controller.view_utils_controller import reset_window


class MainWindow(QMainWindow):
    """
    MainWindow
    ----------
    Main application window that sets up the GUI layout,
    integrates the VTK renderer, header, sidebar, and menu bar.

    Responsibilities:
        - Initialize global UI components
        - Register widgets in the application context
        - Build the main layout with header, sidebar & renderer
        - Provide top-level menu bar actions
    """

    def __init__(self):
        """
        Initialize the main application window.
        Sets up renderer, header, sidebar, and menu bar.
        """
        super().__init__()
        self.setWindowTitle("FEM Solver")

        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("MainWindow initialized")

        # ---------------------------------------------------------------------
        # Initialize Application Context & Core UI Components
        # ---------------------------------------------------------------------
        self.vtk_renderer = VTKRenderer()
        self.sidebar = Sidebar()
        self.header = Header()

        app_context.register_main_window(self)
        app_context.register_sidebar(self.sidebar)
        app_context.register_header(self.header)

        self.logger.debug("Renderer, sidebar, and header registered in app_context")

        # ---------------------------------------------------------------------
        # Build UI Layout
        # ---------------------------------------------------------------------
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(app_context.get_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(app_context.get_sidebar())

        # Renderer content container
        main_content = QWidget()
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.addWidget(self.vtk_renderer.get_widget())
        splitter.addWidget(main_content)

        splitter.setSizes([225, 675])  # Initial sidebar width
        main_layout.addWidget(splitter)

        self.setCentralWidget(central_widget)
        self.resize(900, 600)

        self.logger.debug("Main layout constructed and splitter configured")

        # ---------------------------------------------------------------------
        # Menu Bar
        # ---------------------------------------------------------------------
        self._build_menu_bar()

    # -------------------------------------------------------------------------
    # Menu Bar Setup
    # -------------------------------------------------------------------------
    def _build_menu_bar(self):
        """
        Construct the menu bar with File and View actions.
        """
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Open STL", lambda: self._on_open_stl())
        file_menu.addAction("Open XDMF", lambda: self._on_open_xdmf())
        file_menu.addAction("Reset Window", lambda: self._on_reset_window())

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction("Change Mesh Color", lambda: self._on_change_mesh_color())
        view_menu.addAction("Change Background Color", lambda: self._on_change_background_color())

        self.logger.debug("Menu bar created with File and View menus")

    # -------------------------------------------------------------------------
    # Menu Action Handlers
    # -------------------------------------------------------------------------
    def _on_open_stl(self):
        """Open an STL mesh file."""
        self.logger.info("Open STL file triggered")
        open_stl_file()

    def _on_open_xdmf(self):
        """Open an XDMF simulation result file."""
        self.logger.info("Open XDMF file triggered")
        open_xdmf_file()

    def _on_reset_window(self):
        """Reset the VTK renderer window to default state."""
        self.logger.info("Reset Window triggered")
        reset_window()

    def _on_change_mesh_color(self):
        """Change the mesh surface color."""
        self.logger.info("Change mesh color triggered")
        change_mesh_color()

    def _on_change_background_color(self):
        """Change the background color of the renderer."""
        self.logger.info("Change background color triggered")
        change_background_color()





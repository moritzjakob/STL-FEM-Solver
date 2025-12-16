# -----------------------------------------------------------------------------
# Sidebar: Edit Mode
# -----------------------------------------------------------------------------
# Description:
#   This module defines the 'Edit' mode of the sidebar. It provides
#   interaction and manipulation tools for geometry editing and mesh refinement.
#
#   Features:
#       - Enable/disable movement and rotation of the selected actor
#       - Axis-specific movement toggles (X, Y, Z, R)
#       - Reset movement state
#       - Refine the current mesh and export refined geometry
#
#   This sidebar is automatically activated when "Edit" mode is selected in
#   SidebarBase.
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QCheckBox
)

# Context
from fem_app.core.app_context import app_context

# Controllers
from fem_app.gui.controller.sidebar_fem_force_controller import (
    reset_points,
    reset_facets
)
from fem_app.gui.controller.sidebar_fem_boundary_controller import (
    reset_boundary_plane
)
from fem_app.gui.controller.sidebar_edit_controller import (
    toggle_movement,
    reset_movement,
    refine_mesh,
    save_refine_mesh,
    reset_refine_mesh
)


class SidebarEdit:
    """
    SidebarEdit
    -----------
    UI builder for the 'Edit' mode of the sidebar.
    Provides object movement and mesh refinement functionality.
    """

    def __init__(self):
        """
        Initialize the Edit sidebar section.
        Sets up logger and UI references for movement controls.
        """
        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SidebarEdit initialized")

        # UI references
        self.button_movement = None
        self.x_movement_checkbox = None
        self.y_movement_checkbox = None
        self.z_movement_checkbox = None
        self.r_movement_checkbox = None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def build(self):
        """
        Build and return the full layout for the 'Edit' mode.

        This method:
            - Resets interactor and FEM state
            - Sets default interactor
            - Creates UI groups for movement control and mesh refinement
        """
        self.logger.debug("Building Edit mode layout")

        # Switch to default interactor for Edit mode
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()

        # Reset FEM selection elements (e.g., boundaries, points, facets)
        reset_boundary_plane()
        reset_points()
        reset_facets()

        # Main layout
        edit_layout = QVBoxLayout()
        edit_layout.setContentsMargins(10, 10, 10, 10)
        edit_layout.setSpacing(25)

        # Add UI sections
        edit_layout.addWidget(self._build_movement_section())
        edit_layout.addSpacing(25)
        edit_layout.addWidget(self._build_refinement_section())

        return edit_layout

    # -------------------------------------------------------------------------
    # UI Section Builders
    # -------------------------------------------------------------------------
    def _build_movement_section(self):
        """
        Build the movement control section.
        Allows enabling/disabling movement and rotation along selected axes.
        """
        self.logger.debug("Building movement section")
        group = QGroupBox("Movement")
        layout = QVBoxLayout()

        # Enable movement button
        self.button_movement = QPushButton("Enable Movement")
        self.button_movement.clicked.connect(lambda: toggle_movement())
        layout.addWidget(self.button_movement)

        # Axis checkboxes
        axis_checkbox_layout = QHBoxLayout()

        self.x_movement_checkbox = QCheckBox("X")
        axis_checkbox_layout.addWidget(self.x_movement_checkbox)

        self.y_movement_checkbox = QCheckBox("Y")
        axis_checkbox_layout.addWidget(self.y_movement_checkbox)

        self.z_movement_checkbox = QCheckBox("Z")
        axis_checkbox_layout.addWidget(self.z_movement_checkbox)

        self.r_movement_checkbox = QCheckBox("R")
        axis_checkbox_layout.addWidget(self.r_movement_checkbox)

        layout.addLayout(axis_checkbox_layout)

        # Reset movement button
        button_reset = QPushButton("Reset Movement")
        button_reset.clicked.connect(lambda: reset_movement())
        layout.addWidget(button_reset)

        group.setLayout(layout)
        return group

    def _build_refinement_section(self):
        """
        Build the mesh refinement control section.
        Allows refining, saving, and resetting mesh geometry.
        """
        self.logger.debug("Building mesh refinement section")
        group = QGroupBox("Mesh Refinement")
        layout = QVBoxLayout()

        # Refine Mesh
        button_refine = QPushButton("Refine Mesh")
        button_refine.clicked.connect(lambda: refine_mesh())
        layout.addWidget(button_refine)

        # Save refined STL Mesh
        button_save = QPushButton("Save refined STL Mesh")
        button_save.clicked.connect(lambda: save_refine_mesh())
        layout.addWidget(button_save)

        # Reset refined Mesh
        button_reset = QPushButton("Reset Mesh")
        button_reset.clicked.connect(lambda: reset_refine_mesh())
        layout.addWidget(button_reset)

        group.setLayout(layout)
        return group







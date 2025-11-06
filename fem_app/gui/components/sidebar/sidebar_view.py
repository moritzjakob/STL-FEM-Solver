# -----------------------------------------------------------------------------
# Sidebar: View Mode
# -----------------------------------------------------------------------------
# Description:
#   This module defines the 'View' mode of the sidebar. It provides interactive
#   controls for visualization and inspection of FEM simulation results.
#
#   Features:
#       - Reset view and visualization state
#       - Reload mesh
#       - Display Von Mises stress field
#       - Display stress and strain tensor components
#       - Toggle and scale displacement visualization
#
#   This sidebar is automatically activated when "View" mode is selected in
#   SidebarBase.
# -----------------------------------------------------------------------------

import logging
from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QSlider
)
from PySide6.QtCore import Qt

# Context
from fem_app.core.app_context import app_context

# Controllers
from fem_app.gui.controller.sidebar_view_controller import (
    reload_mesh,
    load_von_mises_stress,
    load_stress_component,
    load_strain_component,
    toggle_displacement,
    update_displacement_multiplier,
    load_displacement_magnitude,
    load_displacement_overlay
)
from fem_app.gui.controller.sidebar_fem_force_controller import (
    reset_points,
    reset_facets
)
from fem_app.gui.controller.sidebar_fem_boundary_controller import (
    reset_boundary_plane
)
from fem_app.gui.controller.view_utils_controller import (
    reset_window
)


class SidebarView:
    """
    SidebarView
    -----------
    UI builder for the 'View' mode of the sidebar.
    Provides visualization and inspection tools for FEM simulation results.
    """

    def __init__(self):
        """
        Initialize the View sidebar section.
        Sets up logger and UI element references.
        """
        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SidebarView initialized")

        # UI references
        self.max_von_mises_input = None
        self.min_von_mises_input = None
        self.stress_component_combo = None
        self.strain_component_combo = None
        self.button_displacement = None
        self.displacement_slider = None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def build(self):
        """
        Build and return the full layout for the 'View' mode.

        This method:
            - Resets FEM selection state (points, facets, boundaries)
            - Sets default interactor
            - Creates UI groups for visualization controls
        """
        self.logger.debug("Building View mode layout")

        # Reset interactor & FEM state
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
        reset_boundary_plane()
        reset_points()
        reset_facets()

        # Main layout
        view_layout = QVBoxLayout()
        view_layout.setContentsMargins(10, 10, 10, 10)
        view_layout.setSpacing(20)

        # Add UI sections
        view_layout.addWidget(self._build_reset_section())
        view_layout.addWidget(self._build_mesh_section())
        view_layout.addWidget(self._build_von_mises_section())
        view_layout.addWidget(self._build_stress_tensor_section())
        view_layout.addWidget(self._build_strain_tensor_section())
        view_layout.addWidget(self._build_displacement_section())

        return view_layout

    # -------------------------------------------------------------------------
    # UI Section Builders
    # -------------------------------------------------------------------------
    def _build_reset_section(self):
        """Build the 'Reset' section with a button to reset the renderer window."""
        self.logger.debug("Building reset section")
        group = QGroupBox("Reset")
        layout = QVBoxLayout()

        button_reset = QPushButton("Reset Window")
        button_reset.clicked.connect(reset_window)
        layout.addWidget(button_reset)

        group.setLayout(layout)
        return group

    def _build_mesh_section(self):
        """Build the 'Mesh' section for reloading the mesh geometry."""
        self.logger.debug("Building mesh section")
        group = QGroupBox("Mesh")
        layout = QVBoxLayout()

        button_mesh = QPushButton("Reload Mesh")
        button_mesh.clicked.connect(reload_mesh)
        layout.addWidget(button_mesh)

        group.setLayout(layout)
        return group

    def _build_von_mises_section(self):
        """Build the 'Von Mises' stress visualization section."""
        self.logger.debug("Building Von Mises section")
        group = QGroupBox("Von Mises Stress")
        layout = QVBoxLayout()

        # Main button
        button_von = QPushButton("Von Mises Stress")
        button_von.clicked.connect(lambda: load_von_mises_stress())
        layout.addWidget(button_von)

        # Optional min/max inputs
        layout.addWidget(QLabel("Max Value"))
        self.max_von_mises_input = QLineEdit()
        self.max_von_mises_input.setPlaceholderText("Enter max value (optional)")
        layout.addWidget(self.max_von_mises_input)

        layout.addWidget(QLabel("Min Value"))
        self.min_von_mises_input = QLineEdit()
        self.min_von_mises_input.setPlaceholderText("Enter min value (optional)")
        layout.addWidget(self.min_von_mises_input)

        group.setLayout(layout)
        return group

    def _build_stress_tensor_section(self):
        """Build the stress tensor component visualization section."""
        self.logger.debug("Building stress tensor section")
        group = QGroupBox("Stress Tensor")
        layout = QVBoxLayout()

        self.stress_component_combo = QComboBox()
        self.stress_component_combo.addItems(["xx", "yy", "zz", "xy", "xz", "yz"])

        layout.addWidget(QLabel("Select Component"))
        layout.addWidget(self.stress_component_combo)

        button_stress = QPushButton("Show Stress Component")
        button_stress.clicked.connect(lambda: load_stress_component())
        layout.addWidget(button_stress)

        group.setLayout(layout)
        return group

    def _build_strain_tensor_section(self):
        """Build the strain tensor component visualization section."""
        self.logger.debug("Building strain tensor section")
        group = QGroupBox("Strain Tensor")
        layout = QVBoxLayout()

        self.strain_component_combo = QComboBox()
        self.strain_component_combo.addItems(["xx", "yy", "zz", "xy", "xz", "yz"])

        layout.addWidget(QLabel("Select Component"))
        layout.addWidget(self.strain_component_combo)

        button_strain = QPushButton("Show Strain Component")
        button_strain.clicked.connect(lambda: load_strain_component())
        layout.addWidget(button_strain)

        group.setLayout(layout)
        return group

    def _build_displacement_section(self):
        """Build the displacement visualization section with multiplier slider."""
        self.logger.debug("Building displacement section")
        group = QGroupBox("Displacement")
        layout = QVBoxLayout()

        # Toggle displacement
        self.button_displacement = QPushButton("Displacement")
        self.button_displacement.clicked.connect(lambda: toggle_displacement())
        layout.addWidget(self.button_displacement)

        # Slider for displacement scaling
        self.displacement_slider, slider_layout = self._create_slider_with_label(
            min_val=1,
            max_val=100,
            initial_val=1,
            on_change=lambda value: update_displacement_multiplier(value)
        )
        self.displacement_slider.setTracking(True)

        layout.addWidget(QLabel("Displacement Multiplicator"))
        layout.addLayout(slider_layout)

        # Displacement visualization modes
        button_magnitude = QPushButton("Displacement Magnitude")
        button_magnitude.clicked.connect(lambda: load_displacement_magnitude())
        layout.addWidget(button_magnitude)

        button_overlay = QPushButton("Displacement Overlay")
        button_overlay.clicked.connect(lambda: load_displacement_overlay())
        layout.addWidget(button_overlay)

        group.setLayout(layout)
        return group

    # -------------------------------------------------------------------------
    # UI Utilities
    # -------------------------------------------------------------------------
    def _create_slider_with_label(self, min_val: int, max_val: int, initial_val: int, on_change):
        """
        Create a horizontal slider with an associated value label.

        Parameters
        ----------
        min_val : int
            Minimum value of the slider.
        max_val : int
            Maximum value of the slider.
        initial_val : int
            Initial slider value.
        on_change : callable
            Callback function executed when the slider value changes.

        Returns
        -------
        (QSlider, QHBoxLayout)
            The slider and its layout containing the value label.
        """
        self.logger.debug("Creating slider with label")
        layout = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(initial_val)

        label = QLabel(str(initial_val))
        slider.valueChanged.connect(lambda val: label.setText(str(val)))
        slider.valueChanged.connect(on_change)

        layout.addWidget(slider)
        layout.addWidget(label)
        return slider, layout



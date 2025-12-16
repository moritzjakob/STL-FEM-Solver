# -----------------------------------------------------------------------------
# Sidebar: FEM Mode
# -----------------------------------------------------------------------------
# Description:
#   This module defines the 'FEM' mode of the sidebar. It provides interactive
#   controls for the FEM Process.
#
#   Features:
#       - Material selection
#       - Boundary condition setup
#       - Point and area force definition
#       - FEM solver execution
#
#   This sidebar is automatically activated when "FEM" mode is selected in
#   SidebarBase.
# -----------------------------------------------------------------------------


import logging
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QWidget,
    QLineEdit,
    QButtonGroup,
    QMessageBox
)

# Context
from fem_app.core.app_context import app_context

# Controllers
from fem_app.gui.controller.fem_solver_controller import solve_fem
from fem_app.gui.controller.sidebar_fem_materials_controller import update_material
from fem_app.gui.controller.sidebar_fem_force_controller import (
    update_force_type,
    update_force_direction,
    toggle_point_selection,
    update_point_value,
    update_vector_value,
    confirm_delete_point,
    highlight_from_scroll,
    reset_points,
    reset_points_button,
    render_vector_arrow,
    remove_vector_arrow,
    toggle_facets_selection,
    toggle_facets_paint,
    reset_facets,
    reset_facets_button
)
from fem_app.gui.controller.sidebar_fem_boundary_controller import (
    reset_boundary_plane,
    toggle_boundary_selection,
    update_boundary_coloring
)


class SidebarFEM:
    """
    SidebarFEM
    ----------
    UI builder for the 'FEM' mode of the sidebar.
    Provides material selection, boundary condition setup,
    force definition (point and area), and solver execution.
    """

    def __init__(self):
        """
        Initialize the FEM sidebar section.
        Sets up logger, UI element references and interaction groups.
        """
        # ---------------------------------------------------------------------
        # Logger
        # ---------------------------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("SidebarFEM initialized")

        # UI references
        self.combo_box_material = None
        self.button_boundary_condition = None
        self.checkbox_x_plane = None
        self.checkbox_y_plane = None
        self.checkbox_z_plane = None
        self.checkbox_less_than = None
        self.checkbox_greater_than = None
        self.combo_box_force_type = None
        self.point_load_group = None
        self.area_load_group = None
        self.scroll_area_layout = None
        self.scroll_area_widget = None
        self.scroll_area = None
        self.button_point_selection = None
        self.area_force_input = None
        self.button_paint_facet = None
        self.checkbox_draw = None
        self.checkbox_erase = None
        self.button_select_facet = None
        self.button_reset_facets = None

        # Internal groups (for exclusivity)
        self.plane_group = None
        self.boundary_direction_group = None
        self.paint_mode_group = None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def build(self):
        """
        Build and return the full layout for the 'FEM' mode.

        This method:
            - Resets renderer interactor and FEM selection state
            - Sets default interactor
            - Creates UI groups for material, boundary, force and solver
        """
        self.logger.debug("Building FEM mode layout")

        # Reset interaction and state
        app_context.get_renderer_state().get_renderer_controller().interactor_manager.set_default_interactor()
        reset_boundary_plane()
        reset_points()
        reset_facets()

        # Main layout
        fem_layout = QVBoxLayout()
        fem_layout.setContentsMargins(10, 10, 10, 10)
        fem_layout.setSpacing(5)

        # Add UI sections
        fem_layout.addWidget(self._build_material_section())
        fem_layout.addSpacing(5)
        fem_layout.addWidget(self._build_boundary_section())
        fem_layout.addSpacing(5)
        fem_layout.addWidget(self._build_force_type_section())
        fem_layout.addWidget(self._build_point_force_section())  # folgt in Teil 2
        fem_layout.addSpacing(5)
        fem_layout.addWidget(self._build_area_force_section())   # folgt in Teil 2
        fem_layout.addSpacing(15)
        fem_layout.addWidget(self._build_solver_section())       # folgt in Teil 2

        # Show only the active force group
        self.point_load_group.setVisible(True)
        self.area_load_group.setVisible(False)

        return fem_layout

    # -------------------------------------------------------------------------
    # UI Section Builders 
    # -------------------------------------------------------------------------
    def _build_material_section(self):
        """
        Build the material selection section.
        """
        self.logger.debug("Building material section")
        group = QGroupBox("Material Selection")
        layout = QVBoxLayout()

        label_material = QLabel("Material:")
        layout.addWidget(label_material)

        self.combo_box_material = QComboBox()
        self.combo_box_material.addItems([
            "None",
            "Structural Steel [m]",
            "Titanium [m]",
            "Structural Steel [cm]",
            "Titanium [cm]"
        ])
        self.combo_box_material.currentIndexChanged.connect(lambda: update_material())
        layout.addWidget(self.combo_box_material)

        group.setLayout(layout)
        return group

    def _build_boundary_section(self):
        """
        Build the boundary condition selection section.
        """
        self.logger.debug("Building boundary section")
        group = QGroupBox("Boundary Condition Selection")
        layout = QVBoxLayout()

        # Boundary selection button
        self.button_boundary_condition = QPushButton("Select Boundary Conditions")
        self.button_boundary_condition.clicked.connect(lambda: toggle_boundary_selection())
        layout.addWidget(self.button_boundary_condition)

        # Plane selection
        plane_layout = QHBoxLayout()
        plane_layout.addWidget(QLabel("Plane Selection:"))

        self.checkbox_x_plane = QCheckBox("X")
        self.checkbox_y_plane = QCheckBox("Y")
        self.checkbox_z_plane = QCheckBox("Z")

        for cb in [self.checkbox_x_plane, self.checkbox_y_plane, self.checkbox_z_plane]:
            cb.stateChanged.connect(lambda: update_boundary_coloring())
            plane_layout.addWidget(cb)

        layout.addLayout(plane_layout)

        # Exclusive group for plane selection
        self.plane_group = QButtonGroup()
        self.plane_group.addButton(self.checkbox_x_plane)
        self.plane_group.addButton(self.checkbox_y_plane)
        self.plane_group.addButton(self.checkbox_z_plane)
        self.plane_group.setExclusive(True)

        # Boundary direction
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Boundary Direction:"))
        self.checkbox_less_than = QCheckBox("<")
        self.checkbox_greater_than = QCheckBox(">")
        for cb in [self.checkbox_less_than, self.checkbox_greater_than]:
            cb.stateChanged.connect(lambda: update_boundary_coloring())
            direction_layout.addWidget(cb)

        layout.addLayout(direction_layout)

        # Exclusive group for direction selection
        self.boundary_direction_group = QButtonGroup()
        self.boundary_direction_group.addButton(self.checkbox_less_than)
        self.boundary_direction_group.addButton(self.checkbox_greater_than)
        self.boundary_direction_group.setExclusive(True)

        group.setLayout(layout)
        return group

    def _build_force_type_section(self):
        """
        Build the force type selection section.
        Allows switching between point and area forces.
        """
        self.logger.debug("Building force type section")
        group = QGroupBox("Force Type Selection")
        layout = QVBoxLayout()

        self.combo_box_force_type = QComboBox()
        self.combo_box_force_type.addItems(["Point Force", "Area Force"])
        self.combo_box_force_type.currentIndexChanged.connect(lambda: update_force_type())

        layout.addWidget(QLabel("Select Force Type:"))
        layout.addWidget(self.combo_box_force_type)

        group.setLayout(layout)
        return group

    def _build_point_force_section(self):
        """
        Build the point force selection section.

        Features:
            - Select points interactively
            - Display and edit force magnitude and direction for each point
            - Visualize and remove force vectors
            - Reset point selection
        """
        self.logger.debug("Building point force section")
        self.point_load_group = QGroupBox("Point Load Selection")
        layout = QVBoxLayout()

        # Point selection button
        self.button_point_selection = QPushButton("Select Point")
        self.button_point_selection.clicked.connect(lambda: toggle_point_selection())
        layout.addWidget(self.button_point_selection)

        # Scroll area (for selected points)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(150)
        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area.setWidget(self.scroll_area_widget)
        layout.addWidget(self.scroll_area)

        # Reset points button
        reset_button = QPushButton("Reset Points")
        reset_button.clicked.connect(lambda: reset_points_button())
        layout.addWidget(reset_button)

        # Vector visualization buttons
        arrow_layout = QHBoxLayout()
        button_visualize = QPushButton("Show Vector")
        button_visualize.clicked.connect(lambda: render_vector_arrow())
        arrow_layout.addWidget(button_visualize)

        button_remove = QPushButton("Remove Vector")
        button_remove.clicked.connect(lambda: remove_vector_arrow())
        arrow_layout.addWidget(button_remove)

        layout.addLayout(arrow_layout)

        self.point_load_group.setLayout(layout)
        return self.point_load_group

    def _build_area_force_section(self):
        """
        Build the area force selection section.

        Features:
            - Select or paint facets
            - Define force value and direction
            - Switch between draw and erase mode
            - Reset painted facets
        """
        self.logger.debug("Building area force section")
        self.area_load_group = QGroupBox("Area Load Selection")
        layout = QVBoxLayout()

        # Facet selection
        self.button_select_facet = QPushButton("Select Facet")
        self.button_select_facet.clicked.connect(lambda: toggle_facets_selection())
        layout.addWidget(self.button_select_facet)

        layout.addSpacing(10)

        # Facet paint
        self.button_paint_facet = QPushButton("Paint Facets")
        self.button_paint_facet.clicked.connect(lambda: toggle_facets_paint())
        layout.addWidget(self.button_paint_facet)

        # Paint mode toggle (Draw/Erase)
        paint_layout = QHBoxLayout()
        paint_layout.addWidget(QLabel("Paint Mode:"))
        self.checkbox_draw = QCheckBox("Draw")
        self.checkbox_erase = QCheckBox("Erase")
        paint_layout.addWidget(self.checkbox_draw)
        paint_layout.addWidget(self.checkbox_erase)

        self.paint_mode_group = QButtonGroup()
        self.paint_mode_group.addButton(self.checkbox_draw)
        self.paint_mode_group.addButton(self.checkbox_erase)
        self.paint_mode_group.setExclusive(True)
        self.checkbox_draw.setChecked(True)
        layout.addLayout(paint_layout)

        # Force value input
        layout.addWidget(QLabel("Force Value:"))
        self.area_force_input = QLineEdit()
        self.area_force_input.setPlaceholderText("Enter force value")
        layout.addWidget(self.area_force_input)

        # Force direction input (X, Y, Z)
        layout.addWidget(QLabel("Force Direction (X, Y, Z):"))
        direction_layout = QHBoxLayout()
        for axis in ["X", "Y", "Z"]:
            vector_input = QLineEdit()
            vector_input.setPlaceholderText(axis)
            vector_input.setFixedWidth(50)
            vector_input.setText("0.0")
            vector_input.textChanged.connect(lambda text, ax=axis: update_force_direction(ax, text))
            direction_layout.addWidget(vector_input)
        layout.addLayout(direction_layout)

        # Reset facets button
        self.button_reset_facets = QPushButton("Reset Facets")
        self.button_reset_facets.clicked.connect(lambda: reset_facets_button())
        layout.addWidget(self.button_reset_facets)

        self.area_load_group.setLayout(layout)
        return self.area_load_group

    def _build_solver_section(self):
        """
        Build the solver execution section.
        """
        self.logger.debug("Building solver section")
        group = QGroupBox("Solver")
        layout = QVBoxLayout()

        button_calculate = QPushButton("Calculate Solution")
        button_calculate.clicked.connect(lambda: solve_fem())
        layout.addWidget(button_calculate)

        group.setLayout(layout)
        return group

    # -------------------------------------------------------------------------
    # Dynamic Point List Handling
    # -------------------------------------------------------------------------
    def _on_force_type_changed(self):
        """
        Toggle visibility between point and area force input sections.
        Triggered when the force type combobox changes.
        """
        selected = self.combo_box_force_type.currentText()
        self.logger.debug(f"Force type changed to: {selected}")

        if selected == "Point Force":
            self.point_load_group.setVisible(True)
            if hasattr(self, "vector_visualisation_group"):
                self.vector_visualisation_group.setVisible(True)
            self.area_load_group.setVisible(False)
        else:
            self.point_load_group.setVisible(False)
            if hasattr(self, "vector_visualisation_group"):
                self.vector_visualisation_group.setVisible(False)
            self.area_load_group.setVisible(True)

    def refresh_scroll_area(self):
        """
        Refresh the scroll area displaying selected points.
        Creates editable UI elements for each selected point.
        """
        self.logger.debug("Refreshing scroll area for point loads")
        try:
            # Clear previous entries
            while self.scroll_area_layout.count() > 0:
                widget = self.scroll_area_layout.takeAt(0)
                if widget.widget():
                    widget.widget().deleteLater()

            # Create entry for each point
            for point_tuple, values in app_context.get_app_state().get_point_values().items():
                self.logger.debug(f"Building UI entry for point: {point_tuple}")
                try:
                    point_entry = QGroupBox(
                        f"Point ({point_tuple[0]:.5f}, {point_tuple[1]:.5f}, {point_tuple[2]:.5f})"
                    )
                    point_layout = QVBoxLayout()
                    point_entry.mousePressEvent = lambda event, pt=point_tuple: self._highlight_from_scroll(pt)

                    # Force input
                    point_layout.addWidget(QLabel("Force Value:"))
                    force_input = QLineEdit()
                    force_input.setPlaceholderText("Enter force value")
                    force_input.setText(str(values['force']))
                    force_input.textChanged.connect(
                        lambda text, pt=point_tuple: update_point_value(pt, 'force', text)
                    )
                    point_layout.addWidget(force_input)

                    # Vector input fields
                    point_layout.addWidget(QLabel("Vector (X, Y, Z):"))
                    vector_layout = QHBoxLayout()
                    for axis in ["X", "Y", "Z"]:
                        vector_input = QLineEdit()
                        vector_input.setPlaceholderText(axis)
                        vector_input.setFixedWidth(50)
                        vector_input.setText(str(values['vector'][axis]))
                        vector_input.textChanged.connect(
                            lambda text, pt=point_tuple, ax=axis: update_vector_value(pt, ax, text)
                        )
                        vector_layout.addWidget(vector_input)
                    point_layout.addLayout(vector_layout)

                    # Delete button
                    delete_button = QPushButton("Delete")
                    delete_button.clicked.connect(lambda _, pt=point_tuple: confirm_delete_point(pt))
                    point_layout.addWidget(delete_button)

                    point_entry.setLayout(point_layout)
                    self.scroll_area_layout.addWidget(point_entry)

                except Exception as e:
                    self.logger.error(f"Error creating UI for point {point_tuple}: {e}")
                    QMessageBox.critical(None, "UI Creation Error", f"Error creating UI for point {point_tuple}: {e}")

            self.scroll_area.setWidget(self.scroll_area_widget)

        except Exception as e:
            self.logger.error(f"Error refreshing scroll area: {e}")
            QMessageBox.critical(None, "Scroll Area Refresh Error", f"Error refreshing scroll area: {e}")

    def _highlight_from_scroll(self, point_tuple):
        """
        Highlight the selected point in the renderer
        when the corresponding entry in the scroll area is clicked.
        """
        self.logger.debug(f"Highlighting point from scroll: {point_tuple}")
        highlight_from_scroll(point_tuple)









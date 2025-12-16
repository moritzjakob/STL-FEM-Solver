# -----------------------------------------------------------------------------
# App State
# -----------------------------------------------------------------------------
# Description:
#   This module defines the AppState class, which acts as a centralized
#   container for the GUI and simulation state. It manages:
#     - File paths and loaded geometry
#     - Visualization and displacement settings
#     - Material selection
#     - Boundary, point, and facet selection states
#     - Force direction vectors for area/point loading
#
#   AppState is typically accessed through the global 'app_context' instance.
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AppState:
    """
    This class is responsible for storing the current UI and simulation
    state. It is used to:
        - Track the currently loaded file
        - Store visualization settings
        - Handle selection modes (boundary, point, facets)
        - Store material and force direction
    """

    def __init__(self) -> None:
        """Initialize the App state with default values."""
        self.reset()
        logger.debug("FEMAppState initialized")

    # -------------------------------------------------------------------------
    def reset(self) -> None:
        """
        Reset the App state to default values.

        This is typically used when:
            - starting a new simulation,
            - clearing the current project,
            - or reinitializing the GUI.

        All selection states, visualization settings, and force directions
        are reset to their default values.
        """
        self.current_file: Optional[str] = None

        # Global simulation state
        self.displacement_multiplier: float = 1.0
        self.displacement_enabled: bool = False
        self.current_visualization: Optional[Any] = None
        self.movement_enabled: bool = False
        self.movement_axis: Dict[str, bool] = {"X": False, "Y": False, "Z": False}
        self.rotation_mode: bool = False

        # Material selection
        self.selected_material: Optional[str] = None

        # Boundary selection state
        self.boundary_selection_enabled: bool = False
        self.selected_boundary_point: Optional[float] = None
        self.selected_boundary_coords: Optional[tuple] = None
        self.selected_boundary_plane_actor: Optional[Any] = None
        self.selected_boundary_space_actor: Optional[Any] = None

        # Point selection state
        self.point_selection_enabled: bool = False
        self.point_values: Dict[Any, Any] = {}
        self.highlighted_points_actor: Dict[Any, Any] = {}

        # Facet selection state
        self.facets_selection_enabled: bool = False
        self.facets_paint_enabled: bool = False
        self.cells_vertices_values: List[Any] = []
        self.highlighted_cells_actor: Dict[Any, Any] = {}

        # Force direction vector
        self.force_direction: Dict[str, float] = {"X": 0.0, "Y": 0.0, "Z": 0.0}

        logger.debug("FEMAppState reset to default values")

    # -----------------------------
    # File Handling
    # -----------------------------
    def set_current_file(self, path: str) -> None:
        """Set the currently loaded STL file path."""
        self.current_file = path
        logger.debug("Current file set to %s", path)

    def get_current_file(self) -> Optional[str]:
        """Return the current loaded file path or None if not set."""
        return self.current_file

    # -----------------------------
    # Visualization
    # -----------------------------
    def set_current_visualization(self, visualization: Any) -> None:
        """
        Set the current visualization mode or object.

        Args:
            visualization: Object or identifier representing
                           the active visualization.
        """
        self.current_visualization = visualization
        logger.debug("Current visualization set to %s", visualization)

    def get_current_visualization(self) -> Optional[Any]:
        """Return the current visualization mode or object."""
        return self.current_visualization

    # -----------------------------
    # Displacement Visualization
    # -----------------------------
    def enable_displacement(self, enabled: bool) -> None:
        """Enable or disable displacement visualization."""
        self.displacement_enabled = enabled
        logger.debug("Displacement mode set to %s", enabled)

    def is_displacement_enabled(self) -> bool:
        """Return True if displacement visualization is enabled."""
        return self.displacement_enabled

    def set_displacement_multiplier(self, multiplier: float) -> None:
        """Set the displacement multiplier used for visualization."""
        self.displacement_multiplier = multiplier
        logger.debug("Displacement multiplier set to %.3f", multiplier)

    def get_displacement_multiplier(self) -> float:
        """Return the current displacement multiplier."""
        return self.displacement_multiplier

    # -----------------------------
    # Movement & Rotation
    # -----------------------------
    def enable_rotation_mode(self, enabled: bool) -> None:
        """Enable or disable rotation mode."""
        self.rotation_mode = enabled
        logger.debug("Rotation mode set to %s", enabled)

    def is_rotation_mode_enabled(self) -> bool:
        """Return True if rotation mode is currently enabled."""
        return self.rotation_mode

    def set_movement_enabled(self, enabled: bool) -> None:
        """Enable or disable movement of selected elements."""
        self.movement_enabled = enabled
        logger.debug("Movement enabled set to %s", enabled)

    def is_movement_enabled(self) -> bool:
        """Return True if movement is currently enabled."""
        return self.movement_enabled

    def set_movement_axis(self, axis: str, enabled: bool) -> None:
        """
        Enable or disable movement along a specific axis.

        Args:
            axis: One of "X", "Y", or "Z".
            enabled: Boolean indicating if movement is allowed on that axis.
        """
        if axis in self.movement_axis:
            self.movement_axis[axis] = enabled
            logger.debug("Movement axis %s set to %s", axis, enabled)
        else:
            logger.warning("Invalid axis '%s' passed to set_movement_axis", axis)

    def get_movement_axis(self) -> Dict[str, bool]:
        """Return a copy of the current movement axis state."""
        return self.movement_axis.copy()

    # -----------------------------
    # Material Selection
    # -----------------------------
    def set_selected_material(self, material: str) -> None:
        """Set the currently selected material."""
        self.selected_material = material
        logger.debug("Selected material set to %s", material)

    def get_selected_material(self) -> Optional[str]:
        """Return the currently selected material or None if not set."""
        return self.selected_material

    # -----------------------------
    # Boundary Selection
    # -----------------------------
    def enable_boundary_selection(self, enabled: bool) -> None:
        """Enable or disable boundary selection mode."""
        self.boundary_selection_enabled = enabled
        logger.debug("Boundary selection mode set to %s", enabled)

    def is_boundary_selection_enabled(self) -> bool:
        """Return True if boundary selection is currently enabled."""
        return self.boundary_selection_enabled

    def set_selected_boundary_point(self, point: float) -> None:
        """Set the selected boundary point coordinate."""
        self.selected_boundary_point = point
        logger.debug("Selected boundary point set to %s", point)

    def get_selected_boundary_point(self) -> Optional[float]:
        """Return the selected boundary point coordinate."""
        return self.selected_boundary_point

    def set_selected_boundary_coords(self, coords: tuple) -> None:
        """Set the selected boundary coordinates."""
        self.selected_boundary_coords = coords
        logger.debug("Selected boundary coordinates set to %s", coords)

    def get_selected_boundary_coords(self) -> Optional[tuple]:
        """Return the selected boundary coordinates."""
        return self.selected_boundary_coords

    def set_selected_boundary_plane_actor(self, actor: Any) -> None:
        """Set the selected boundary plane actor (e.g., VTK actor)."""
        self.selected_boundary_plane_actor = actor
        logger.debug("Selected boundary plane actor set")

    def get_selected_boundary_plane_actor(self) -> Optional[Any]:
        """Return the selected boundary plane actor."""
        return self.selected_boundary_plane_actor

    def set_selected_boundary_space_actor(self, actor: Any) -> None:
        """Set the selected boundary space actor (e.g., VTK actor)."""
        self.selected_boundary_space_actor = actor
        logger.debug("Selected boundary space actor set")

    def get_selected_boundary_space_actor(self) -> Optional[Any]:
        """Return the selected boundary space actor."""
        return self.selected_boundary_space_actor

    # -----------------------------
    # Point Selection
    # -----------------------------
    def enable_point_selection(self, enabled: bool) -> None:
        """Enable or disable point selection mode."""
        self.point_selection_enabled = enabled
        logger.debug("Point selection mode set to %s", enabled)

    def is_point_selection_enabled(self) -> bool:
        """Return True if point selection is currently enabled."""
        return self.point_selection_enabled

    def get_point_values(self) -> Dict[Any, Any]:
        """
        Return the dictionary of point values.
        """
        return self.point_values

    def get_highlighted_points_actor(self) -> Dict[Any, Any]:
        """
        Return the dictionary of highlighted point actors.
        """
        return self.highlighted_points_actor

    # -----------------------------
    # Facet Selection
    # -----------------------------
    def enable_facets_selection(self, enabled: bool) -> None:
        """Enable or disable facet selection mode."""
        self.facets_selection_enabled = enabled
        logger.debug("Facet selection mode set to %s", enabled)

    def is_facets_selection_enabled(self) -> bool:
        """Return True if facet selection is currently enabled."""
        return self.facets_selection_enabled

    def enable_facets_paint(self, enabled: bool) -> None:
        """Enable or disable facet painting mode."""
        self.facets_paint_enabled = enabled
        logger.debug("Facet paint mode set to %s", enabled)

    def is_facets_paint_enabled(self) -> bool:
        """Return True if facet paint mode is currently enabled."""
        return self.facets_paint_enabled

    def get_cells_vertices_values(self) -> List[Any]:
        """Return the list of cell vertices values."""
        return self.cells_vertices_values

    def get_highlighted_cells_actor(self) -> Dict[Any, Any]:
        """
        Return the dictionary of highlighted cell actors.
        """
        return self.highlighted_cells_actor

    # -----------------------------
    # Force Direction
    # -----------------------------
    def get_force_direction(self) -> Dict[str, float]:
        """Return a copy of the current force direction vector."""
        return self.force_direction.copy()


# Global singleton instance of the App state
app_state = AppState()







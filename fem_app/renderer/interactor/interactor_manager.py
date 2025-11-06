# -----------------------------------------------------------------------------
# Interactor Manager Service
# -----------------------------------------------------------------------------
# Description:
#   This service manages and switches between different VTK interactor styles.
#   It provides a clean interface for enabling interaction modes such as:
#
#       - Default camera (trackball) control
#       - Object movement interaction
#       - FEM boundary selection
#       - FEM point selection
#       - FEM cell selection
#       - FEM cell paint selection
#
#   All operations are executed using the registered renderer_controller
#   accessed through the AppContext.
# -----------------------------------------------------------------------------

import logging
import vtk

from fem_app.core.app_context import app_context

# Custom Interactor Styles---
from fem_app.renderer.interactor.interactor_styles.interactor_object_movement import InteractorObjectMovementStyle
from fem_app.renderer.interactor.interactor_styles.interactor_fem_boundary_selector import InteractorFEMBoundarySelectorStyle
from fem_app.renderer.interactor.interactor_styles.interactor_fem_cell_paint_selection import InteractorFEMCellPaintSelectorStyle
from fem_app.renderer.interactor.interactor_styles.interactor_fem_cell_selection import InteractorFEMCellSelectorStyle
from fem_app.renderer.interactor.interactor_styles.interactor_fem_point_selector import InteractorFEMPointSelectorStyle


class InteractorManager:
    """
    InteractorManager
    -----------------
    High-level service for managing all VTK interactor styles in the application.

    Responsibilities:
        - Switch between different interactor modes used in the simulation UI
        - Reset interactor state before switching (important for modes with internal state)
        - Keep the active interactor style synchronized with the global RendererState
        - Provide simple, clean API for the controller layer

    Supported Interaction Modes:
        - Default camera control (trackball)
        - Object movement
        - FEM boundary selection
        - FEM point selection
        - FEM cell selection
        - FEM paint selection
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("InteractorManager initialized")

    # -------------------------------------------------------------------------
    def reset_interactor(self):
        """
        Reset the state of the currently active interactor style if necessary.
        """
        current_style = app_context.get_renderer_state().get_interactor_style()
        if isinstance(current_style, InteractorObjectMovementStyle):
            current_style.reset_state()
            self.logger.debug("Current interactor state reset")

    def _set_style(self, style):
        """
        Helper method to safely switch the active interactor style.

        - Resets the current interactor state
        - Updates interactor style in VTK
        - Stores the new style in RendererState

        Args:
            style (vtkInteractorStyle): The new interactor style to activate.
        """
        self.reset_interactor()

        if not app_context.get_renderer_state().get_interactor():
            self.logger.warning("No interactor found - cannot set style")
            return

        app_context.get_renderer_state().get_interactor().SetInteractorStyle(style)
        app_context.get_renderer_state().set_interactor_style(style)
        self.logger.info(f"Interactor style set to: {type(style).__name__}")

    # -------------------------------------------------------------------------
    # Public API - Style Switching
    # -------------------------------------------------------------------------
    def set_default_interactor(self):
        """Activate default camera interactor (trackball style)."""
        style = vtk.vtkInteractorStyleTrackballCamera()
        self._set_style(style)
        self.logger.info("Default camera interactor activated")

    def set_movement_interactor(self):
        """Activate object movement interactor mode."""
        style = InteractorObjectMovementStyle()
        self._set_style(style)
        self.logger.info("Object movement interactor activated")

    def set_boundary_selector_interactor(self):
        """Activate FEM boundary selection interactor mode."""
        style = InteractorFEMBoundarySelectorStyle()
        self._set_style(style)
        self.logger.info("Boundary selection interactor activated")

    def set_point_selector_interactor(self):
        """Activate FEM point selection interactor mode."""
        style = InteractorFEMPointSelectorStyle()
        self._set_style(style)
        self.logger.info("Point selection interactor activated")

    def set_area_selector_interactor(self):
        """Activate FEM cell selection interactor mode."""
        style = InteractorFEMCellSelectorStyle()
        self._set_style(style)
        self.logger.info("Cell selection interactor activated")

    def set_area_paint_selector_interactor(self):
        """Activate FEM cell paint selection interactor mode."""
        style = InteractorFEMCellPaintSelectorStyle()
        self._set_style(style)
        self.logger.info("Paint cell selection interactor activated")






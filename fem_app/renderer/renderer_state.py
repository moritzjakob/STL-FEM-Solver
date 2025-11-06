# -----------------------------------------------------------------------------
# Renderer State 
# -----------------------------------------------------------------------------
# Description:
#   Centralized state container for all VTK renderer and visualization
#   components used in the FEM application. This class manages:
#     - Renderer, widget, and interactor references
#     - Mesh, actor, scalar bar, tooltip, and vector arrow states
#     - Interaction and wireframe settings
#     - Resetting the visualization state between simulations
#
#   It acts as the single source of truth for rendering-related
#   information and allows other modules (GUI, FEM solvers,
#   post-processing) to interact with the visualization without
#   direct dependencies on VTK internals.
#
#   RendererState is typically accessed through the global 'app_context' instance.
# -----------------------------------------------------------------------------

import logging
from typing import Optional, Any, List


class RendererState:
    """
    Centralized renderer state for VTK-based visualization.

    Provides an API to manage:
      - Renderer and interactor references
      - Tooltip, scalar bar, and orientation widget
      - Arrow/vector actors and mesh actors
      - Wireframe and displacement visualization modes

    The state can be reset at any time to clear the scene and
    prepare for a new simulation or model.
    """

    def __init__(self) -> None:
        """Initialize the renderer state and logger."""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("RendererState initialized")

        # -----------------------------
        # Renderer & Widget References
        # -----------------------------
        self.renderer: Optional[Any] = None                  # VTK renderer instance
        self.renderer_controller: Optional[Any] = None       # Renderer controller abstraction
        self.vtk_widget: Optional[Any] = None                # QVTKOpenGLWidget instance
        self.interactor: Optional[Any] = None                # VTK render interactor
        self.current_interactor_style: Optional[Any] = None  # Current interactor style object

        # -----------------------------
        # Scene & Visualization Objects
        # -----------------------------
        self.actor: Optional[Any] = None                     # Main mesh actor
        self.tooltip_actor: Optional[Any] = None             # Tooltip label actor
        self.tooltip_enabled: bool = False                   # Tooltip state
        self.picker: Optional[Any] = None                    # Generic picker
        self.point_picker: Optional[Any] = None              # Point picker
        self.orientation_widget: Optional[Any] = None        # Orientation axes widget
        self.scalar_bar: Optional[Any] = None                # Scalar bar actor
        self.scalar_bar_text_actor: Optional[Any] = None     # Optional label for scalar bar
        self.arrow_actors: List[Any] = []                    # Force/vector arrow actors

        # -----------------------------
        # File / Mesh / Data
        # -----------------------------
        self.filename: Optional[str] = None                  # Currently loaded filename
        self.mesh_data: Optional[Any] = None                 # Original mesh data
        self.original_grid: Optional[Any] = None             # Unmodified VTK grid
        self.refined_mesh: Optional[Any] = None              # Refined mesh if available

        # -----------------------------
        # Rendering Modes & Flags
        # -----------------------------
        self.wireframe_mode: bool = False                    # Wireframe rendering on/off
        self.displacement: Optional[Any] = None              # Displacement visualization object

    # -----------------------------
    # Renderer & Core Registration
    # -----------------------------
    def register_renderer(self, renderer: Any, renderer_controller: Any,
                          interactor: Any, vtk_widget: Any) -> None:
        """
        Register the main renderer components when the GUI initializes.

        Args:
            renderer: VTK renderer instance.
            renderer_controller: Custom controller object managing the renderer.
            interactor: VTK render interactor instance.
            vtk_widget: QVTKOpenGLWidget instance for rendering.
        """
        self.renderer = renderer
        self.renderer_controller = renderer_controller
        self.interactor = interactor
        self.vtk_widget = vtk_widget
        self.logger.info("Renderer registered with VTK widget and interactor")

    def update_view(self) -> None:
        """
        Trigger a manual update/redraw of the VTK render view.
        Useful when the scene changes outside of normal interaction events.
        """
        if self.vtk_widget:
            self.vtk_widget.update()
            self.logger.debug("VTK view updated")

    # -----------------------------
    # Renderer & Controller Access
    # -----------------------------
    def get_renderer(self) -> Optional[Any]:
        """Return the VTK renderer instance or None if not registered."""
        return self.renderer

    def get_renderer_controller(self) -> Optional[Any]:
        """Return the renderer controller instance or None if not set."""
        return self.renderer_controller

    def get_vtk_widget(self) -> Optional[Any]:
        """Return the QVTKOpenGLWidget instance used for rendering."""
        return self.vtk_widget

    # -----------------------------
    # Filename / Mesh
    # -----------------------------
    def set_filename(self, filename: str) -> None:
        """
        Set the current file name used in the renderer.

        Args:
            filename: Path to the currently loaded file.
        """
        self.filename = filename
        self.logger.debug("Renderer filename set to %s", filename)

    def get_filename(self) -> Optional[str]:
        """Return the current filename or None if no file is loaded."""
        return self.filename

    def set_mesh_data(self, mesh_data: Any) -> None:
        """
        Set the original mesh data object.

        Args:
            mesh_data: Mesh data structure (vtkPolyData or custom object).
        """
        self.mesh_data = mesh_data
        self.logger.debug("Mesh data set")

    def get_mesh_data(self) -> Optional[Any]:
        """Return the original mesh data object or None if not set."""
        return self.mesh_data

    def set_original_grid(self, grid: Any) -> None:
        """
        Set the unmodified original VTK grid.

        Args:
            grid: VTK data object representing the base mesh.
        """
        self.original_grid = grid
        self.logger.debug("Original grid set")

    def get_original_grid(self) -> Optional[Any]:
        """Return the original unmodified VTK grid object."""
        return self.original_grid

    def set_refined_mesh(self, mesh: Any) -> None:
        """
        Set the refined mesh object.

        Args:
            mesh: VTK mesh object after refinement.
        """
        self.refined_mesh = mesh
        self.logger.debug("Refined mesh set")

    def get_refined_mesh(self) -> Optional[Any]:
        """Return the refined mesh object or None if not set."""
        return self.refined_mesh

    # -----------------------------
    # Actor Management
    # -----------------------------
    def set_actor(self, actor: Any) -> None:
        """
        Set the main mesh actor.

        Args:
            actor: VTK actor object.
        """
        self.actor = actor
        self.logger.debug("Main actor updated")

    def get_actor(self) -> Optional[Any]:
        """Return the main mesh actor or None if not set."""
        return self.actor


     # -----------------------------
    # Arrow Actors (forces / vectors)
    # -----------------------------
    def add_arrow_actor(self, actor: Any) -> None:
        """
        Add an arrow actor to the internal list.

        Args:
            actor: VTK actor representing an arrow visualization.
        """
        self.arrow_actors.append(actor)
        self.logger.debug("Arrow actor added (total: %d)", len(self.arrow_actors))
        self.update_view()

    def clear_arrow_actors(self) -> None:
        """
        Remove all arrow actors from the internal list.
        This does not remove actors from the renderer itself.
        """
        self.arrow_actors.clear()
        self.logger.debug("All arrow actors cleared")
        self.update_view()

    def get_arrow_actors(self) -> List[Any]:
        """
        Return a list of all current arrow actors.

        Returns:
            A list of VTK arrow actors.
        """
        return list(self.arrow_actors)

    # -----------------------------
    # Tooltip handling
    # -----------------------------
    def enable_tooltip(self, enabled: bool) -> None:
        """
        Enable or disable tooltip visualization.

        Args:
            enabled: True to show tooltips, False to hide them.
        """
        self.tooltip_enabled = enabled
        self.logger.debug("Tooltip enabled set to %s", enabled)

    def is_tooltip_enabled(self) -> bool:
        """Return True if tooltip visualization is currently enabled."""
        return self.tooltip_enabled

    def set_tooltip_actor(self, actor: Any) -> None:
        """
        Set the tooltip actor used for on-hover labels.

        Args:
            actor: VTK actor representing the tooltip label.
        """
        self.tooltip_actor = actor
        self.logger.debug("Tooltip actor set")

    def get_tooltip_actor(self) -> Optional[Any]:
        """Return the tooltip actor or None if not set."""
        return self.tooltip_actor

    # -----------------------------
    # Scalar bar
    # -----------------------------
    def set_scalar_bar(self, scalar_bar: Any) -> None:
        """
        Set the scalar bar actor.

        Args:
            scalar_bar: VTK scalar bar actor.
        """
        self.scalar_bar = scalar_bar
        self.logger.debug("Scalar bar set")

    def get_scalar_bar(self) -> Optional[Any]:
        """Return the scalar bar actor or None if not set."""
        return self.scalar_bar

    def set_scalar_bar_text_actor(self, text_actor: Any) -> None:
        """
        Set the optional scalar bar text label actor.

        Args:
            text_actor: VTK actor for scalar bar label.
        """
        self.scalar_bar_text_actor = text_actor
        self.logger.debug("Scalar bar text actor set")

    def get_scalar_bar_text_actor(self) -> Optional[Any]:
        """Return the scalar bar text actor or None if not set."""
        return self.scalar_bar_text_actor

    # -----------------------------
    # Picker & Orientation
    # -----------------------------
    def set_picker(self, picker: Any) -> None:
        """Set the generic picker instance."""
        self.picker = picker
        self.logger.debug("Generic picker set")

    def get_picker(self) -> Optional[Any]:
        """Return the generic picker instance."""
        return self.picker

    def set_point_picker(self, picker: Any) -> None:
        """Set the point picker used for point selection."""
        self.point_picker = picker
        self.logger.debug("Point picker set")

    def get_point_picker(self) -> Optional[Any]:
        """Return the point picker instance."""
        return self.point_picker

    def set_orientation_widget(self, widget: Any) -> None:
        """Set the orientation widget (e.g., orientation axes)."""
        self.orientation_widget = widget
        self.logger.debug("Orientation widget set")

    def get_orientation_widget(self) -> Optional[Any]:
        """Return the orientation widget or None if not set."""
        return self.orientation_widget

    # -----------------------------
    # Interactor & Style
    # -----------------------------
    def set_interactor_style(self, style: Any) -> None:
        """
        Set the current interactor style.

        Args:
            style: VTK interactor style object.
        """
        self.current_interactor_style = style
        self.logger.debug("Interactor style set")

    def get_interactor_style(self) -> Optional[Any]:
        """Return the current interactor style object or None if not set."""
        return self.current_interactor_style

    def set_interactor(self, interactor: Any) -> None:
        """
        Set the interactor reference.

        Args:
            interactor: VTK interactor instance.
        """
        self.interactor = interactor
        self.logger.debug("Interactor set")

    def get_interactor(self) -> Optional[Any]:
        """Return the interactor reference or None if not set."""
        return self.interactor

    # -----------------------------
    # Wireframe Mode
    # -----------------------------
    def get_wireframe_mode(self) -> bool:
        """Return True if wireframe mode is currently enabled."""
        return self.wireframe_mode

    def set_wireframe_mode(self, mode: bool) -> None:
        """
        Set wireframe mode.

        Args:
            mode: True to enable wireframe rendering, False to disable.
        """
        self.wireframe_mode = mode
        self.logger.debug("Wireframe mode set to %s", mode)

    # -----------------------------
    # Displacement Visualization
    # -----------------------------
    def set_displacement(self, displacement: Any) -> None:
        """
        Set the displacement visualization object.

        Args:
            displacement: representing displacements.
        """
        self.displacement = displacement
        self.logger.debug("Displacement object set")

    def get_displacement(self) -> Optional[Any]:
        """Return the displacement or None if not set."""
        return self.displacement

    # -----------------------------
    # Reset State
    # -----------------------------
    def reset(self) -> None:
        """
        Reset the renderer state to default values.

        It clears actor references, scalar bar, tooltips, and
        removes all props from the renderer if present.
        """
        self.logger.info("Resetting renderer state to defaults")

        self.filename = None
        self.actor = None
        self.mesh_data = None
        self.original_grid = None
        self.refined_mesh = None
        self.arrow_actors.clear()
        self.tooltip_actor = None
        self.scalar_bar = None
        self.scalar_bar_text_actor = None
        self.displacement = None
        self.wireframe_mode = False

        if self.renderer:
            self.renderer.RemoveAllViewProps()
            self.logger.debug("Renderer props cleared")

        self.update_view()


# Global singleton instance of the renderer state
renderer_state = RendererState()





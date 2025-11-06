# -----------------------------------------------------------------------------
# CleanUp Service
# -----------------------------------------------------------------------------
# Description:
#   The CleanUp service provides a centralized utility layer for
#   resetting and clearing the VTK rendering scene.
#
#   It is used by the RendererController to:
#       - Remove all actors (mesh, scalar bar, tooltip)
#       - Reset the camera to a default position and orientation
#       - Reinitialize the VTK interactor when needed
#
#   All operations are executed using the registered renderer_controller
#   accessed through the AppContext.
# -----------------------------------------------------------------------------

import logging
from fem_app.core.app_context import app_context


class CleanUp:
    """
    CleanUp Service
    ---------------
    A utility class that manages:
      - Removing actors from the renderer
      - Resetting camera view
      - Resetting the entire rendering window

    This ensures that the renderer can be restored to a clean state
    when switching between meshes, visualizations, or simulations.
    """

    def __init__(self):
        """Initialize the CleanUp service and its logger."""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("CleanUp service initialized")

    # -------------------------------------------------------------------------
    def clear_actors(self) -> None:
        """
        Remove all VTK actors and the scalar bar from the current renderer scene.

        This includes:
          - All mesh actors
          - Tooltip actor (if present)
          - Scalar bar actor (if present)

        After clearing, the scene is re-rendered if the VTK widget is available.
        """
        renderer = app_context.get_renderer_state().get_renderer()
        if not renderer:
            self.logger.warning("Renderer not set - cannot clear actors")
            return

        self.logger.debug("Clearing all actors from the scene")

        # Traverse through all actors and remove them
        actors = renderer.GetActors()
        actors.InitTraversal()
        actor = actors.GetNextActor()
        while actor:
            renderer.RemoveActor(actor)
            actor = actors.GetNextActor()

        # Remove tooltip actor if present
        tooltip_actor = app_context.get_renderer_state().get_tooltip_actor()
        if tooltip_actor is not None:
            renderer.RemoveActor(tooltip_actor)
            app_context.get_renderer_state().set_tooltip_actor(None)
            self.logger.debug("Tooltip actor removed")

        # Remove scalar bar if present
        scalar_bar = app_context.get_renderer_state().get_scalar_bar()
        if scalar_bar is not None:
            renderer.RemoveActor(scalar_bar)
            app_context.get_renderer_state().set_scalar_bar(None)
            self.logger.debug("Scalar bar removed")

        # Clear mesh actor reference in renderer state
        app_context.get_renderer_state().set_actor(None)

        # Trigger render update
        vtk_widget = app_context.get_renderer_state().get_vtk_widget()
        if vtk_widget:
            vtk_widget.GetRenderWindow().Render()
            self.logger.debug("Scene re-rendered after actor removal")

    # -------------------------------------------------------------------------
    def reset_view(self) -> None:
        """
        Reset the camera to its default position and orientation.

        Default camera parameters:
            Position    = (0, 0, 1)
            Focal Point = (0, 0, 0)
            View Up     = (0, 1, 0)

        This does not remove any actors - it only affects the camera.
        """
        renderer = app_context.get_renderer_state().get_renderer()
        if not renderer:
            self.logger.warning("Renderer not set - cannot reset view")
            return

        self.logger.info("Resetting camera to default view")
        camera = renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)

        vtk_widget = app_context.get_renderer_state().get_vtk_widget()
        if vtk_widget:
            vtk_widget.GetRenderWindow().Render()
            self.logger.debug("Camera reset complete and scene re-rendered")

    # -------------------------------------------------------------------------
    def reset_window(self) -> None:
        """
        Reset the entire rendering window.

        This method:
          - Clears all actors
          - Resets the camera view
          - Reinitializes the interactor
          - Re-renders the scene
        """
        renderer = app_context.get_renderer_state().get_renderer()
        interactor = app_context.get_renderer_state().get_interactor()
        if not renderer or not interactor:
            self.logger.warning("Renderer or interactor not set - cannot reset window")
            return

        self.logger.info("Resetting entire renderer window")

        self.clear_actors()
        self.reset_view()
        interactor.Initialize()

        vtk_widget = app_context.get_renderer_state().get_vtk_widget()
        if vtk_widget:
            vtk_widget.GetRenderWindow().Render()
            self.logger.debug("Render window fully reset")







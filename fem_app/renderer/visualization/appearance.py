# -----------------------------------------------------------------------------
# Appearance Service
# -----------------------------------------------------------------------------
# Description:
#   The Appearance service provides a centralized interface for controlling
#   all visual styling aspects of the renderer, including:
#       - Mesh appearance (wireframe, color)
#       - Background color
#       - Orientation widget initialization
#       - Scalar bar title handling
#       - Arrow visualization 
#
#   All operations are executed using the registered renderer_controller
#   accessed through the AppContext.
# -----------------------------------------------------------------------------

import logging
import vtk
import gc
from fem_app.core.app_context import app_context


class Appearance:
    """
    Centralized appearance manager for the VTK renderer.

    This service controls the visual state of the scene, including:
      - Mesh rendering style and color
      - Renderer background color
      - Orientation widget (axes)
      - Scalar bar title text
      - Arrow and overlay visualization 
    """

    def __init__(self):
        """Initialize the Appearance service and its logger."""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Appearance service initialized")

    # -------------------------------------------------------------------------
    # Mesh Visualization
    # -------------------------------------------------------------------------
    def toggle_wireframe_mode(self, enable: bool) -> None:
        """
        Enable or disable wireframe rendering for the current mesh actor.

        Args:
            enable (bool): True = wireframe mode, False = solid surface
        """
        app_context.get_renderer_state().set_wireframe_mode(enable)
        actor = app_context.get_renderer_state().get_actor()

        if actor is not None:
            prop = actor.GetProperty()
            if enable:
                prop.SetRepresentationToWireframe()
                self.logger.info("Wireframe mode enabled")
            else:
                prop.SetRepresentationToSurface()
                self.logger.info("Wireframe mode disabled")
            app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()
        else:
            self.logger.warning("No actor found - wireframe mode not applied")

    def set_mesh_color(self, rgb_color: tuple) -> None:
        """
        Set the color of the current mesh actor.

        Args:
            rgb_color (tuple): RGB values in [0.0, 1.0].
        """
        actor = app_context.get_renderer_state().get_actor()
        if actor is not None:
            actor.GetProperty().SetColor(rgb_color)
            app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()
            self.logger.info(f"Mesh color set to: {rgb_color}")
        else:
            self.logger.warning("No actor found - mesh color not applied")

    def set_background_color(self, rgb_color: tuple) -> None:
        """
        Set the background color of the renderer.

        Args:
            rgb_color (tuple): RGB values in [0.0, 1.0].
        """
        renderer = app_context.get_renderer_state().get_renderer()
        if renderer is not None:
            renderer.SetBackground(*rgb_color)
            app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()
            self.logger.info(f"Background color set to: {rgb_color}")
        else:
            self.logger.warning("Renderer not set - background color not applied")

    # -------------------------------------------------------------------------
    # Orientation Widget
    # -------------------------------------------------------------------------
    def initialize_orientation_widget(self) -> None:
        """
        Initialize and display an orientation widget (axes) in the lower-left corner.

        The orientation widget:
          - Helps users understand the scene orientation
          - Is interactive but set to non-movable (InteractiveOff)
          - Uses a fixed viewport in the bottom-left corner
        """
        interactor = app_context.get_renderer_state().get_interactor()
        if not interactor:
            self.logger.warning("Cannot initialize orientation widget - no interactor set")
            return

        axes_actor = vtk.vtkAxesActor()
        orientation_widget = vtk.vtkOrientationMarkerWidget()
        orientation_widget.SetOrientationMarker(axes_actor)
        orientation_widget.SetInteractor(interactor)
        orientation_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        orientation_widget.EnabledOn()
        orientation_widget.InteractiveOff()

        app_context.get_renderer_state().set_orientation_widget(orientation_widget)
        self.logger.info("Orientation widget initialized")

    # -------------------------------------------------------------------------
    # Scalar Bar Title
    # -------------------------------------------------------------------------
    def remove_scalar_bar_title(self) -> None:
        """
        Remove the scalar bar title text actor if it exists.

        This is typically called before adding a new title
        to avoid duplicates or overlaps.
        """
        text_actor = app_context.get_renderer_state().get_scalar_bar_text_actor()
        if text_actor is not None:
            app_context.get_renderer_state().get_renderer().RemoveActor(text_actor)
            app_context.get_renderer_state().set_scalar_bar_text_actor(None)
            self.logger.debug("Scalar bar title removed")

    def create_scalar_bar_title(self, title: str, xpos: float = 0.025, ypos: float = 0.95, font_size: int = 14) -> None:
        """
        Create or replace the scalar bar title overlay in the top-left corner of the viewport.

        Args:
            title (str): Title text to display
            xpos (float): X position (normalized display coordinates)
            ypos (float): Y position (normalized display coordinates)
            font_size (int): Font size in points
        """
        self.remove_scalar_bar_title()

        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(title)
        text_actor.GetTextProperty().SetFontSize(font_size)
        text_actor.GetTextProperty().BoldOn()
        text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)

        text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        text_actor.GetPositionCoordinate().SetValue(xpos, ypos)

        app_context.get_renderer_state().get_renderer().AddActor2D(text_actor)
        app_context.get_renderer_state().set_scalar_bar_text_actor(text_actor)

        self.logger.info(f"Scalar bar title created: '{title}'")
    

    # -------------------------------------------------------------------------
    # Mesh Bounds
    # -------------------------------------------------------------------------
    def get_mesh_bounds(self):
        """
        Retrieve the bounding box of the current mesh actor.

        Returns:
            tuple | None: Bounds in the format
            (xmin, xmax, ymin, ymax, zmin, zmax),
            or None if no actor is currently present.
        """
        actor = app_context.get_renderer_state().get_actor()
        if actor:
            bounds = actor.GetBounds()
            self.logger.debug(f"Mesh bounds retrieved: {bounds}")
            return bounds
        self.logger.warning("No actor found - mesh bounds unavailable")
        return None

    # -------------------------------------------------------------------------
    # Arrow Visualization (e.g., for force vectors)
    # -------------------------------------------------------------------------
    def add_arrow(self, start_point: tuple, vector: tuple, scale_factor: float = None) -> None:
        """
        Add a single arrow to the scene, pointing in the given direction.

        Args:
            start_point (tuple): (x, y, z) coordinates of the arrow base.
            vector (tuple): Direction vector of the arrow.
            scale_factor (float, optional): Length scale for the arrow.
            If not provided, it is automatically derived from mesh bounds.
        """
        renderer = app_context.get_renderer_state().get_renderer()
        if not renderer:
            self.logger.warning("Renderer not set - cannot add arrow")
            return

    
        # Normalize the direction vector
        vector_array = [vector[0], vector[1], vector[2]]
        vtk.vtkMath.Normalize(vector_array)
        normalized_vector = vector_array.copy()

        # Determine arrow scale from mesh bounds if not provided
        if scale_factor is None:
            bounds = self.get_mesh_bounds()
            if bounds is not None:
                x_size = bounds[1] - bounds[0]
                y_size = bounds[3] - bounds[2]
                z_size = bounds[5] - bounds[4]
                max_dim = max(x_size, y_size, z_size)
                scale_factor = max_dim * 0.05
            else:
                scale_factor = 1.0

        length = scale_factor

        # Arrow geometry setup
        arrow_source = vtk.vtkArrowSource()
        transform = vtk.vtkTransform()
        transform.Translate(start_point)

        # Compute rotation to align arrow with the direction vector
        x_axis = [1, 0, 0]
        rotation_axis = [0, 0, 0]

        vtk.vtkMath.Cross(x_axis, normalized_vector, rotation_axis)
        angle = vtk.vtkMath.AngleBetweenVectors(x_axis, normalized_vector) * 180.0 / vtk.vtkMath.Pi()

        if vtk.vtkMath.Norm(rotation_axis) < 1e-6:
            dot = vtk.vtkMath.Dot(x_axis, normalized_vector)
            if dot < 0.0:
                rotation_axis = [0, 1, 0]
                transform.RotateWXYZ(180, rotation_axis)

        else:
            vtk.vtkMath.Normalize(rotation_axis)
            transform.RotateWXYZ(angle, rotation_axis)
        
        transform.Scale(length, length, length)

        transform_pd = vtk.vtkTransformPolyDataFilter()
        transform_pd.SetTransform(transform)
        transform_pd.SetInputConnection(arrow_source.GetOutputPort())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(transform_pd.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor((0, 1, 0))  # Green arrow

        renderer.AddActor(actor)
        app_context.get_renderer_state().add_arrow_actor(actor)
        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

        self.logger.info(
            f"Arrow added at {start_point} with direction {vector} and length {length}"
        )

    def remove_arrow_actors(self) -> None:
        """
        Remove all arrow actors from the renderer scene.

        Notes:
            - Iterates through all stored arrow actors in renderer_state
              and removes them from the scene.
            - Frees resources using garbage collection.
            - Triggers a re-render if the widget is available.
        """
        renderer = app_context.get_renderer_state().get_renderer()
        if not renderer:
            self.logger.warning("Renderer not set - cannot remove arrow actors")
            return

        for arrow_actor in app_context.get_renderer_state().get_arrow_actors():
            renderer.RemoveActor(arrow_actor)
        app_context.get_renderer_state().clear_arrow_actors()

        gc.collect()

        vtk_widget = app_context.get_renderer_state().get_vtk_widget()
        if vtk_widget:
            vtk_widget.GetRenderWindow().Render()

        self.logger.debug("All arrow actors removed")














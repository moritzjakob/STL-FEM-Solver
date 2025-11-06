# -----------------------------------------------------------------------------
# Renderer Controller
# -----------------------------------------------------------------------------
# Description:
#   The RendererController provides a high-level API between the GUI
#   and the low-level VTK rendering subsystems.
#
#   Instead of letting multiple parts of the application directly modify
#   the renderer, all rendering-related operations are funneled through
#   this controller. This ensures:
#     - Clean separation of UI and VTK internals
#     - Consistent access to renderer_state
#     - Centralized logic for appearance and scene manipulation
#
# Responsibilities:
#   - Managing appearance (colors, wireframe, background)
#   - Handling mesh loading (STL/XDMF)
#   - Resetting camera, view, and scene
#   - Delegating interaction and rendering updates to service classes
#
# Services:
#   - Appearance          -> visual appearance & rendering parameters
#   - CleanUp             -> scene clearing & reset logic
#   - STLHandler          -> import & visualization of STL files
#   - XDMFHandler         -> import & visualization of FEM/XDMF results
#   - InteractorManager   -> handling interactor events and styles
# -----------------------------------------------------------------------------


import logging
from fem_app.core.app_context import app_context

# ---------------------------------------------
# Service Modules
# ---------------------------------------------
from fem_app.renderer.visualization.appearance import Appearance
from fem_app.renderer.visualization.cleanup_utils import CleanUp
from fem_app.renderer.data.stl_handler import STLHandler
from fem_app.renderer.data.xdmf_handler import XDMFHandler
from fem_app.renderer.interactor.interactor_manager import InteractorManager


class RendererController:
    """
    Central controller for high-level renderer operations.

    This class serves as the primary interface for rendering actions,
    coordinating multiple low-level service modules. It allows other
    parts of the application (UI panels, solvers, tools) to modify
    the rendering scene without direct access to the renderer itself.
    """

    def __init__(self):
        """Initialize the renderer controller and its service modules."""
        self.logger = logging.getLogger(__name__)
        self.logger.debug("RendererController initialized")

        # -----------------------------
        # Service Layer Instances
        # -----------------------------
        self.appearance = Appearance()
        self.cleanup = CleanUp()
        self.stl_handler = STLHandler()
        self.xdmf_handler = XDMFHandler(self.cleanup, self.appearance)
        self.interactor_manager = InteractorManager()

    # -------------------------------------------------------------------------
    # Wireframe & Visualization
    # -------------------------------------------------------------------------
    def toggle_wireframe(self) -> None:
        """
        Toggle the global wireframe rendering mode for the main mesh actor.
        """
        new_state = not app_context.get_renderer_state().get_wireframe_mode()
        self.appearance.toggle_wireframe_mode(new_state)
        app_context.get_renderer_state().set_wireframe_mode(new_state)
        self.logger.info(f"Wireframe mode set to: {new_state}")

    def set_background_color(self, rgb_color: tuple) -> None:
        """
        Set the background color of the renderer.

        Args:
            rgb_color (tuple): (R, G, B) values in range [0.0, 1.0].
        """
        self.appearance.set_background_color(rgb_color)
        self.logger.info(f"Background color updated: {rgb_color}")

    def set_mesh_color(self, rgb_color: tuple) -> None:
        """
        Set the color of the currently loaded mesh actor.

        Args:
            rgb_color (tuple): (R, G, B) values in range [0.0, 1.0].
        """
        self.appearance.set_mesh_color(rgb_color)
        self.logger.info(f"Mesh color updated: {rgb_color}")

    def reset_view(self) -> None:
        """
        Reset the camera view to its default position and orientation.
        """
        self.cleanup.reset_view()
        self.logger.info("View reset executed")

    def reset_window(self) -> None:
        """
        Clear the entire rendering scene and reset camera and interactor.
        """
        self.cleanup.reset_window()
        self.logger.info("Renderer window fully reset")

    # -------------------------------------------------------------------------
    # Data Loading & Mesh Handling
    # -------------------------------------------------------------------------
    def load_stl(self, file_path: str) -> None:
        """
        Load an STL file and visualize it in the renderer.

        Args:
            file_path (str): Path to the STL file.
        """
        app_context.get_renderer_state().set_filename(file_path)
        self.stl_handler.load_stl(file_path)
        self.logger.info(f"STL file loaded: {file_path}")
    
    def refine_mesh(self) -> None:
        """
        Refine the currently loaded STL mesh
        """
        self.stl_handler.refine_mesh()
        self.logger.info("Mesh refinement executed")

    def save_refined_mesh(self) -> None:
        """
        Save the currently refined STL mesh to disk
        """
        filename = app_context.get_renderer_state().get_filename()
        if filename:
            self.stl_handler.save_refined_mesh(filename)
            self.logger.info("Refined mesh saved")
        else:
            self.logger.warning("No filename found - cannot save refined mesh")

    def reset_mesh(self) -> None:
        """
        Reset the mesh refinement state.

        This restores the original mesh geometry and discards
        any refinements or temporary changes made to the mesh.
        """
        self.stl_handler.reset_mesh_state()
        self.logger.info("Mesh refinement reset")

    def load_xdmf(self, file_path: str) -> None:
        """
        Load an XDMF file and visualize it in the renderer.

        Args:
            file_path (str): Path to the XDMF result file
        """
        app_context.get_renderer_state().set_filename(file_path)
        self.xdmf_handler.load_xdmf(file_path)
        self.logger.info(f"XDMF file loaded: {file_path}")

    # -------------------------------------------------------------------------
    # Interaction Styles
    # -------------------------------------------------------------------------
    def set_default_interactor(self) -> None:
        """
        Activate the default camera interaction mode.
        """
        self.interactor_manager.set_default_interactor()
        self.logger.debug("Interactor switched to default camera")

    def set_movement_interactor(self) -> None:
        """
        Activate movement interaction mode.
        """
        self.interactor_manager.set_movement_interactor()
        self.logger.debug("Interactor switched to movement mode")

    def set_boundary_selector_interactor(self) -> None:
        """
        Activate boundary selection interaction mode.
        """
        self.interactor_manager.set_boundary_selector_interactor()
        self.logger.debug("Interactor switched to boundary selector")

    def set_point_selector_interactor(self) -> None:
        """
        Activate point selection interaction mode.
        """
        self.interactor_manager.set_point_selector_interactor()
        self.logger.debug("Interactor switched to point selector")

    def set_area_selector_interactor(self) -> None:
        """
        Activate area selection interaction mode.
        """
        self.interactor_manager.set_area_selector_interactor()
        self.logger.debug("Interactor switched to area selector")

    def set_area_paint_selector_interactor(self) -> None:
        """
        Activate area painting interaction mode.
        """
        self.interactor_manager.set_area_paint_selector_interactor()
        self.logger.debug("Interactor switched to paint cell selector")




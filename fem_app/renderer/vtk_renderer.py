# -----------------------------------------------------------------------------
# VTK Renderer Widget
# -----------------------------------------------------------------------------
# Description:
#   The VTKRenderer class is the main entry point for all VTK-based
#   rendering in the application. It creates the renderer, interactor,
#   and rendering widget and registers them in the global renderer_state.
#
#   This pattern allows other modules (GUI, FEM solvers, post-processing)
#   to access the renderer and visualization components without holding
#   their own references.
#
# Responsibilities:
#   - Initialize vtkRenderer and QVTKRenderWindowInteractor
#   - Set default interaction style and background
#   - Create and register RendererController
#   - Register renderer in global renderer_state
#   - Provide global key event handling ('r' = reset view)
#
#   Rendereris typically accessed through the global 'renderer_state' instance.
# -----------------------------------------------------------------------------

import logging
import vtk
from PySide6.QtWidgets import QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# ---------------------------------------------
# Core State & Controller
# ---------------------------------------------
from fem_app.renderer.renderer_state import renderer_state
from fem_app.renderer.renderer_controller import RendererController


class VTKRenderer(QWidget):
    """
    Main VTK renderer widget.

    This widget:
      - Initializes and configures the VTK rendering pipeline
      - Registers the renderer and its controller in the global renderer_state
      - Acts as the single entry point for all visualization logic
      - Handles global keyboard shortcuts for the 3D view

    The main renderer created here is shared across the application
    through 'renderer_state'.
    """

    def __init__(self) -> None:
        """Initialize the VTK renderer, widget, interactor and controller."""
        super().__init__()

        # -----------------------------
        # 0. Logger
        # -----------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.debug("VTKRenderer initialized")

        # -----------------------------
        # 1. VTK Core Setup
        # -----------------------------
        self.vtk_widget = QVTKRenderWindowInteractor()
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)

        # Set default background color (dark gray)
        self.renderer.SetBackground(0.15, 0.15, 0.15)

        # Interactor setup with Trackball Camera style
        self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

        # Global key shortcuts
        self.interactor.AddObserver("KeyPressEvent", self.on_key_press)

        # Initialize VTK interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

        # -----------------------------
        # 2. Controller Initialization
        # -----------------------------
        self.controller = RendererController()

        # -----------------------------
        # 3. Register Renderer in Global State
        # -----------------------------
        renderer_state.register_renderer(
            renderer=self.renderer,
            renderer_controller=self.controller,
            interactor=self.interactor,
            vtk_widget=self.vtk_widget
        )

        # Initialize orientation widget through controller
        self.controller.appearance.initialize_orientation_widget()

        self.logger.info("VTKRenderer successfully initialized and registered")

    # -------------------------------------------------------------------------
    def get_widget(self) -> QVTKRenderWindowInteractor:
        """
        Return the VTK widget to be embedded in the Qt UI.

        Returns:
            QVTKRenderWindowInteractor: The interactive VTK rendering widget.
        """
        return self.vtk_widget

    # -------------------------------------------------------------------------
    def on_key_press(self, obj, event) -> None:
        """
        Handle global key shortcuts for the VTK interactor.

        Currently supported keys:
            - 'r': Reset the 3D camera view.

        Args:
            obj: VTK interactor object that triggered the event.
            event: Event name ('KeyPressEvent').
        """
        key = self.interactor.GetKeySym()
        if key == 'r':
            self.controller.reset_view()
            self.logger.debug("Key 'r' pressed - camera reset triggered")





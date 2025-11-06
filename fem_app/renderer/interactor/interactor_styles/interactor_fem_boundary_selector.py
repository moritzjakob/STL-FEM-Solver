# -----------------------------------------------------------------------------
# FEM Boundary Selector Interactor Style
# -----------------------------------------------------------------------------
# Description:
#   This interactor style allows the user to:
#
#       - Pick a point on the mesh surface
#       - Determine its plane coordinate (X, Y, or Z)
#       - Render a visual cutting plane in the scene
#       - Store the selection in the FEM application state
#       - Remove or update existing boundary planes
#
#   This tool is used during boundary assignment in FEM preprocess.
#
#   It is typically triggered via the InteractorManager through the
#   RendererController.
# -----------------------------------------------------------------------------

import logging
import vtk
import numpy as np

from fem_app.core.app_context import app_context
from fem_app.gui.controller.sidebar_fem_boundary_controller import update_boundary_coloring


class InteractorFEMBoundarySelectorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    InteractorFEMBoundarySelectorStyle
    ----------------------------------
    Custom VTK interactor style that enables interactive boundary plane selection.

    Features:
        - Pick a mesh point with mouse click
        - Determine its X/Y/Z plane position based on UI selection
        - Render a cutting plane at the selected position
        - Store and manage selection state globally
        - Allow toggling and removal of existing plane
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEM boundary selector interactor initialized")

        # VTK Point Picker for selecting mesh points
        self.point_picker = vtk.vtkPointPicker()
        self.point_picker.SetTolerance(0.01)

        # Register event listener
        self.AddObserver("LeftButtonPressEvent", self.on_left_click_point_selection)

    # -------------------------------------------------------------------------
    def on_left_click_point_selection(self, obj, event):
        """
        Callback for left mouse button press.
        Picks a point on the mesh and determines the plane coordinate.

        Steps:
            1. Check renderer and actor availability
            2. Ensure axis plane is selected via sidebar
            3. Pick the point using VTK point picker
            4. Store selection in app state and update boundary coloring
            5. Handle plane removal if same selection is repeated
        """
        interactor = self.GetInteractor()
        x, y = interactor.GetEventPosition()

        actor = app_context.get_renderer_state().get_actor()
        sidebar = app_context.get_sidebar()

        if actor is None or app_context.get_renderer_state() is None:
            self.logger.warning("Renderer or actor not initialized - cannot select boundary plane")
            self.OnLeftButtonDown()
            return

        # Axis selection required (X, Y, or Z)
        if not (sidebar and (
            sidebar.fem_section.checkbox_x_plane.isChecked() or
            sidebar.fem_section.checkbox_y_plane.isChecked() or
            sidebar.fem_section.checkbox_z_plane.isChecked()
        )):
            self.logger.warning("No axis selected - user must select X, Y, or Z plane")
            self.OnLeftButtonDown()
            return

        # Pick the point on the mesh
        if self.point_picker.Pick(x, y, 0, app_context.get_renderer_state().get_renderer()):
            point_id = self.point_picker.GetPointId()
            self.logger.debug(f"Picked point ID: {point_id}")

            if point_id != -1:
                coords = np.array(actor.GetMapper().GetInput().GetPoint(point_id))
                self.logger.debug(f"Selected point coordinates: {coords}")

                # Determine plane axis
                if sidebar.fem_section.checkbox_x_plane.isChecked():
                    axis = 'x'
                    selected_value = coords[0]
                elif sidebar.fem_section.checkbox_y_plane.isChecked():
                    axis = 'y'
                    selected_value = coords[1]
                else:
                    axis = 'z'
                    selected_value = coords[2]

                # If reselecting the same plane, remove it
                if (app_context.get_app_state().get_selected_boundary_point() is not None and
                    app_context.get_app_state().get_selected_boundary_coords() is not None and
                    abs(app_context.get_app_state().get_selected_boundary_point() - selected_value) < 1e-6):
                    self.logger.info("Same boundary point reselected - removing plane")
                    self.remove_plane()
                    app_context.get_app_state().set_selected_boundary_coords(None)
                    app_context.get_app_state().set_selected_boundary_point(None)
                    return

                # Store new selection
                app_context.get_app_state().set_selected_boundary_point(selected_value)
                app_context.get_app_state().set_selected_boundary_coords(tuple(coords))

                # Optional UI hook to update sidebar visualization
                update_boundary_coloring()

                self.logger.info(f"Boundary plane selected at axis={axis}, value={selected_value}")
            else:
                self.OnLeftButtonDown()
        else:
            self.OnLeftButtonDown()

    # -------------------------------------------------------------------------
    def render_plane(self, position, plane):
        """
        Render a boundary plane at the specified position.

        Args:
            position (float): Plane position along the selected axis.
            plane (str): One of 'x', 'y', or 'z'.
        """
        actor = app_context.get_renderer_state().get_actor()
        cutting_plane = vtk.vtkPlane()

        if plane == 'x':
            cutting_plane.SetNormal(1, 0, 0)
            cutting_plane.SetOrigin(position, 0, 0)
        elif plane == 'y':
            cutting_plane.SetNormal(0, 1, 0)
            cutting_plane.SetOrigin(0, position, 0)
        elif plane == 'z':
            cutting_plane.SetNormal(0, 0, 1)
            cutting_plane.SetOrigin(0, 0, position)
        else:
            self.logger.error(f"Invalid plane axis: {plane}")
            return

        # VTK cutter setup
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(cutting_plane)
        cutter.SetInputData(actor.GetMapper().GetInput())
        cutter.Update()

        cut_mapper = vtk.vtkPolyDataMapper()
        cut_mapper.SetInputConnection(cutter.GetOutputPort())

        plane_actor = vtk.vtkActor()
        plane_actor.SetMapper(cut_mapper)
        plane_actor.GetProperty().SetColor(0, 0, 1)
        plane_actor.GetProperty().SetOpacity(1.0)
        plane_actor.GetProperty().SetEdgeVisibility(True)
        plane_actor.GetProperty().SetLineWidth(15.0)

        app_context.get_renderer_state().get_renderer().AddActor(plane_actor)
        app_context.get_app_state().set_selected_boundary_plane_actor(plane_actor)
        app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()

        self.logger.info("Boundary plane rendered")

    # -------------------------------------------------------------------------
    def remove_plane(self):
        """
        Remove previously rendered boundary plane and space actors
        from the renderer and clear references in app state.
        """
        if app_context.get_app_state().get_selected_boundary_plane_actor():
            app_context.get_renderer_state().get_renderer().RemoveActor(app_context.get_app_state().get_selected_boundary_plane_actor())
            app_context.get_app_state().set_selected_boundary_plane_actor(None)
            self.logger.debug("Removed boundary plane actor")

        if app_context.get_app_state().get_selected_boundary_space_actor():
            app_context.get_renderer_state().get_renderer().RemoveActor(app_context.get_app_state().get_selected_boundary_space_actor())
            app_context.get_app_state().set_selected_boundary_space_actor(None)
            self.logger.debug("Removed boundary space actor")

        app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()
        self.logger.info("Boundary plane(s) removed")

















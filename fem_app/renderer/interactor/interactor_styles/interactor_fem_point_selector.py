# -----------------------------------------------------------------------------
# FEM Point Selector Interactor Style
# -----------------------------------------------------------------------------
# Description:
#   This interactor style enables interactive selection and deselection of mesh
#   points in the 3D viewport. It provides:
#
#       - Picking mesh points via left mouse click
#       - Highlighting selected points with a red glyph
#       - Toggling highlight state by clicking again
#
#   This tool is used during point load assignment in FEM preprocess.
#
#   It is typically triggered via the InteractorManager through the
#   RendererController.
# -----------------------------------------------------------------------------

import logging
import vtk
import numpy as np

from fem_app.core.app_context import app_context
from fem_app.gui.controller.sidebar_fem_force_controller import update_point_scroll_area


class InteractorFEMPointSelectorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    InteractorFEMPointSelectorStyle
    --------------------------------
    Custom VTK interactor style that allows selecting and deselecting mesh points.

    Features:
        - Select points with a single left mouse click
        - Toggle selection state (select/deselect)
        - Highlight selected points with red glyphs
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEM Point Selector interactor initialized")

        # VTK point picker
        self.point_picker = vtk.vtkPointPicker()
        self.point_picker.SetTolerance(0.01)

        # Event binding
        self.AddObserver("LeftButtonPressEvent", self.on_left_click_point_selection)

    # -------------------------------------------------------------------------
    def on_left_click_point_selection(self, obj, event):
        """
        Handle left mouse button click:
        - Pick a point on the mesh
        - Toggle its selection state
        - Update sidebar scroll area (optional)
        """
        interactor = self.GetInteractor()
        x, y = interactor.GetEventPosition()

        actor = app_context.get_renderer_state().get_actor()
        if not actor or not app_context.get_renderer_state():
            self.logger.warning("No actor or renderer available - cannot pick points")
            self.OnLeftButtonDown()
            return

        if self.point_picker.Pick(x, y, 0, app_context.get_renderer_state().get_renderer()):
            point_id = self.point_picker.GetPointId()
            self.logger.debug(f"Picked point ID: {point_id}")

            if point_id != -1:
                # Extract picked point coordinates
                point_coords = np.array(actor.GetMapper().GetInput().GetPoint(point_id))
                self.logger.info(f"Selected vertex coordinates: {point_coords}")

                # Optional UI sync
                sidebar = app_context.get_sidebar()
                if sidebar:
                    update_point_scroll_area(point_coords, selected=True)
                else:
                    self.logger.debug("Sidebar not available - skipping scroll area update")

                # Toggle highlight state
                self._toggle_highlight_point(point_coords)
            else:
                self.OnLeftButtonDown()
        else:
            self.OnLeftButtonDown()

    # -------------------------------------------------------------------------
    def _toggle_highlight_point(self, position):
        """
        Toggle the highlight state of a picked point:
        - If already selected: remove highlight and update UI
        - If new: create glyph actor and highlight it
        """
        sidebar = app_context.get_sidebar()  # Optional for UI updates
        position_tuple = tuple(position)

        highlighted_points = app_context.get_app_state().get_highlighted_points_actor()

        # Deselect existing point
        if position_tuple in highlighted_points:
            self.logger.debug(f"Deselecting point at {position_tuple}")

            if sidebar:
                update_point_scroll_area(position, selected=False)

            highlight_actor = highlighted_points[position_tuple]
            app_context.get_renderer_state().get_renderer().RemoveActor(highlight_actor)
            del highlighted_points[position_tuple]

        # Highlight new point
        else:
            self.logger.debug(f"Highlighting new point at {position_tuple}")

            # Create glyph for highlighting
            points = vtk.vtkPoints()
            points.InsertNextPoint(position)

            point_polydata = vtk.vtkPolyData()
            point_polydata.SetPoints(points)

            glyph_filter = vtk.vtkVertexGlyphFilter()
            glyph_filter.SetInputData(point_polydata)
            glyph_filter.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(glyph_filter.GetOutputPort())

            highlight_actor = vtk.vtkActor()
            highlight_actor.SetMapper(mapper)
            highlight_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red highlight
            highlight_actor.GetProperty().SetPointSize(15)

            app_context.get_renderer_state().get_renderer().AddActor(highlight_actor)
            highlighted_points[position_tuple] = highlight_actor

        app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()














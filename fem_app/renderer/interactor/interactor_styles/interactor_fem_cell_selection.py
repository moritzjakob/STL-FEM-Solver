# -----------------------------------------------------------------------------
# FEM Cell Selector Interactor Style
# -----------------------------------------------------------------------------
# Description:
#   This interactor style allows the user to select or deselect mesh cells
#   interactively by clicking on them in the 3D viewport.
#
#   It provides:
#       - Picking FEM cells using vtkCellPicker and vtkCellLocator
#       - Toggling cell selection with left mouse click
#       - Highlighting selected cells with a red overlay
#       - Storing and removing vertex coordinates of selected cells
#
#   This tool is used during area load assignment in FEM preprocess.
#
#   It is typically triggered via the InteractorManager through the
#   RendererController.
# -----------------------------------------------------------------------------

import logging
import vtk
import numpy as np

from fem_app.core.app_context import app_context


class InteractorFEMCellSelectorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    InteractorFEMCellSelectorStyle
    ------------------------------
    Custom VTK interactor style that allows selecting and deselecting FEM cells.

    Features:
        - Left mouse click to select or deselect a cell
        - Highlights selected cells with a red overlay
        - Stores the vertex coordinates of selected cells
        - Toggle selection by clicking the same cell again
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEM Cell Selector interactor initialized")

        # Initialize cell locator for cell picking
        actor = app_context.get_renderer_state().get_actor()
        if not actor:
            self.logger.warning("No actor present - cell locator not built")
            self.cell_locator = None
        else:
            self.cell_locator = vtk.vtkCellLocator()
            self.cell_locator.SetDataSet(actor.GetMapper().GetInput())
            self.cell_locator.BuildLocator()
            self.logger.debug("Cell locator successfully built")

        # Event binding
        self.AddObserver("LeftButtonPressEvent", self.on_left_click_cell_selection)

    # -------------------------------------------------------------------------
    def on_left_click_cell_selection(self, obj, event):
        """
        Handle left mouse click:
        - Pick cell under cursor
        - Toggle highlight state of the picked cell
        """
        x, y = self.GetInteractor().GetEventPosition()
        pick_pos = self.get_pick_position(x, y)

        if pick_pos is None or self.cell_locator is None:
            self.OnLeftButtonDown()
            return

        cell_id = self.cell_locator.FindCell(pick_pos)
        if cell_id == -1:
            self.OnLeftButtonDown()
            return

        self.logger.debug(f"Picked cell ID: {cell_id}")

        actor = app_context.get_renderer_state().get_actor()
        picked_cell = actor.GetMapper().GetInput().GetCell(cell_id)
        points = picked_cell.GetPoints()
        cell_coords = [np.array(points.GetPoint(i)) for i in range(points.GetNumberOfPoints())]

        self.logger.debug(f"Cell coordinates: {cell_coords}")

        self._toggle_cell_selection(cell_id, cell_coords)

    # -------------------------------------------------------------------------
    def get_pick_position(self, x, y):
        """
        Convert screen coordinates to world coordinates using vtkCellPicker.
        Returns None if picking failed.
        """
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        if picker.Pick(x, y, 0, app_context.get_renderer_state().get_renderer()):
            return picker.GetPickPosition()
        return None

    # -------------------------------------------------------------------------
    def _toggle_cell_selection(self, cell_id, cell_coords):
        """
        Toggle the highlight state of a cell:
        - If already selected -> remove highlight
        - If not selected -> add highlight
        """
        actor = app_context.get_renderer_state().get_actor()

        if actor is None or app_context.get_renderer_state() is None:
            self.logger.warning("Renderer or actor missing - cannot toggle cell selection")
            return

        cell_id_tuple = (cell_id,)
        highlighted_cells = app_context.get_app_state().get_highlighted_cells_actor()

        # Deselect cell if already highlighted
        if cell_id_tuple in highlighted_cells:
            self.logger.debug(f"Deselecting cell ID {cell_id}")
            highlight_actor = highlighted_cells[cell_id_tuple]
            app_context.get_renderer_state().get_renderer().RemoveActor(highlight_actor)
            del highlighted_cells[cell_id_tuple]

            app_context.get_app_state().cells_vertices_values = [
                vertices for vertices in app_context.get_app_state().get_cells_vertices_values()
                if not np.array_equal(vertices, cell_coords)
            ]

        # Select and highlight new cell
        else:
            self.logger.debug(f"Selecting and highlighting cell ID {cell_id}")
            self._create_highlight_actor(actor, cell_id, cell_id_tuple, cell_coords)

        app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()

    # -------------------------------------------------------------------------
    def _create_highlight_actor(self, actor, cell_id, cell_id_tuple, cell_coords):
        """
        Create and store a red highlight actor for the selected cell.
        """
        renderer = app_context.get_renderer_state().get_renderer()
        poly_data = actor.GetMapper().GetInput()

        # Build selection object
        cell_ids = vtk.vtkIdTypeArray()
        cell_ids.InsertNextValue(cell_id)

        selection_node = vtk.vtkSelectionNode()
        selection_node.SetFieldType(vtk.vtkSelectionNode.CELL)
        selection_node.SetContentType(vtk.vtkSelectionNode.INDICES)
        selection_node.SetSelectionList(cell_ids)

        selection = vtk.vtkSelection()
        selection.AddNode(selection_node)

        # Extract selected cell
        extract_selection = vtk.vtkExtractSelection()
        extract_selection.SetInputData(0, poly_data)
        extract_selection.SetInputData(1, selection)
        extract_selection.Update()

        selected = vtk.vtkUnstructuredGrid()
        selected.ShallowCopy(extract_selection.GetOutput())

        # Create highlight actor
        selected_mapper = vtk.vtkDataSetMapper()
        selected_mapper.SetInputData(selected)

        selected_actor = vtk.vtkActor()
        selected_actor.SetMapper(selected_mapper)
        selected_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red
        selected_actor.GetProperty().SetLineWidth(2.0)

        # Add to scene and state
        renderer.AddActor(selected_actor)
        app_context.get_app_state().get_highlighted_cells_actor()[cell_id_tuple] = selected_actor
        app_context.get_app_state().get_cells_vertices_values().append(cell_coords)

        self.logger.debug(f"Cell ID {cell_id} highlighted and stored")














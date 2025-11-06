# -----------------------------------------------------------------------------
# FEM Cell Paint Selector Interactor Style
# -----------------------------------------------------------------------------
# Description:
#   This interactor style enables the user to "paint" cells on the mesh interactively.
#   It supports:
#
#       - Highlighting cells by dragging the mouse (draw mode)
#       - Erasing previously highlighted cells (erase mode)
#       - Tracking vertex coordinates of selected cells
#       - Maintaining highlight actors for visual feedback
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


class InteractorFEMCellPaintSelectorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    InteractorFEMCellPaintSelectorStyle
    -----------------------------------
    Custom VTK interactor style that allows interactive painting of FEM mesh cells.

    Features:
        - Paint cells by holding left mouse button and moving cursor
        - Erase highlighted cells in erase mode
        - Highlight selected cells in red
        - Track selected cell vertices for later processing
        - Manage highlight actors for rendering feedback
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("FEM Cell Paint Selector interactor initialized")

        self.is_left_button_pressed = False
        self.brush_size = 0.0  # Brush radius 

        actor = app_context.get_renderer_state().get_actor()
        if not actor:
            self.logger.warning("No actor present at initialization - cell locator not built")
            self.cell_locator = None
        else:
            self.cell_locator = vtk.vtkStaticCellLocator()
            self.cell_locator.SetDataSet(actor.GetMapper().GetInput())
            self.cell_locator.BuildLocator()
            self.logger.debug("Cell locator built successfully")

        # Event observers
        self.AddObserver("LeftButtonPressEvent", self.on_left_button_press)
        self.AddObserver("LeftButtonReleaseEvent", self.on_left_button_release)
        self.AddObserver("MouseMoveEvent", self.on_mouse_move)
        self.AddObserver("KeyPressEvent", self.on_key_press)

    # -------------------------------------------------------------------------
    def on_left_button_press(self, obj, event):
        """
        Handle left mouse button press.
        Enables painting mode and highlights the picked cells if valid.
        """
        self.is_left_button_pressed = True
        x, y = self.GetInteractor().GetEventPosition()
        pick_pos = self.get_pick_position(x, y)
        if pick_pos is not None:
            cell_ids = self.pick_cells_within_radius(pick_pos)
            if cell_ids:
                self._highlight_or_erase_cells(cell_ids)
            else:
                self.OnLeftButtonDown()
        else:
            self.OnLeftButtonDown()

    # -------------------------------------------------------------------------
    def on_left_button_release(self, obj, event):
        """
        Handle left mouse button release.
        Ends painting mode.
        """
        self.is_left_button_pressed = False
        self.OnLeftButtonUp()

    # -------------------------------------------------------------------------
    def on_mouse_move(self, obj, event):
        """
        While the left button is pressed, paint or erase cells under the cursor.
        """
        if self.is_left_button_pressed:
            x, y = self.GetInteractor().GetEventPosition()
            pick_pos = self.get_pick_position(x, y)
            if pick_pos is not None:
                cell_ids = self.pick_cells_within_radius(pick_pos)
                if cell_ids:
                    self._highlight_or_erase_cells(cell_ids)
                else:
                    self.OnMouseMove()

    # -------------------------------------------------------------------------
    def pick_cell_with_locator(self, pick_pos):
        """
        Find the cell ID corresponding to a picked 3D position.
        Returns -1 if no valid cell is found.
        """
        if not self.cell_locator:
            self.logger.warning("Cell locator not initialized")
            return -1
        return self.cell_locator.FindCell(pick_pos)

    def pick_cells_within_radius(self, pick_pos):
        """
        Pick all cell IDs within the brush radius (if brush_size > 0), otherwise pick a single cell.
        Returns a list of cell IDs. Works with vtkStaticCellLocator or falls back if unavailable.
        """
        if not self.cell_locator:
            self.logger.warning("Cell locator not initialized")
            return []

        if self.brush_size > 0.0:       
            bounds = [
                pick_pos[0] - self.brush_size, pick_pos[0] + self.brush_size,
                pick_pos[1] - self.brush_size, pick_pos[1] + self.brush_size,
                pick_pos[2] - self.brush_size, pick_pos[2] + self.brush_size,
            ]
            temp_ids = vtk.vtkIdList()
            self.cell_locator.FindCellsWithinBounds(bounds, temp_ids)
            return [temp_ids.GetId(i) for i in range(temp_ids.GetNumberOfIds())]
            
        else:
            cell_id = self.cell_locator.FindCell(pick_pos)
        return [cell_id] if cell_id != -1 else []

    # -------------------------------------------------------------------------
    def get_pick_position(self, x, y):
        """
        Convert a 2D mouse position into a 3D world coordinate.
        """
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        picker.Pick(x, y, 0, app_context.get_renderer_state().get_renderer())
        return picker.GetPickPosition()

    # -------------------------------------------------------------------------
    def _highlight_or_erase_cells(self, cell_ids):
        """
        Highlight or erase multiple cells based on the current UI mode (draw/erase).
        """
        actor = app_context.get_renderer_state().get_actor()
        sidebar = app_context.get_sidebar()  

        if actor is None or app_context.get_renderer_state() is None:
            self.logger.warning("Renderer or actor not available - cannot modify cells")
            return

        poly_data = actor.GetMapper().GetInput()
        # For erasing, collect cell_id_tuples to delete after loop
        to_delete = []
        for cell_id in cell_ids:
            picked_cell = poly_data.GetCell(cell_id)
            if picked_cell is None:
                continue
            points = picked_cell.GetPoints()
            cell_coords = [np.array(points.GetPoint(i)) for i in range(points.GetNumberOfPoints())]
            cell_id_tuple = (cell_id,)

            # Drawing mode (checkbox)
            if sidebar and sidebar.fem_section.checkbox_draw.isChecked():
                if cell_id_tuple not in app_context.get_app_state().get_highlighted_cells_actor():
                    self.logger.debug(f"Highlighting cell ID {cell_id}")
                    self._create_highlight_actor(poly_data, cell_id, cell_id_tuple, cell_coords)

            # Erasing mode (checkbox)
            elif sidebar and sidebar.fem_section.checkbox_erase.isChecked():
                if cell_id_tuple in app_context.get_app_state().get_highlighted_cells_actor():
                    self.logger.debug(f"Erasing highlight for cell ID {cell_id}")
                    highlight_actor = app_context.get_app_state().get_highlighted_cells_actor()[cell_id_tuple]
                    app_context.get_renderer_state().get_renderer().RemoveActor(highlight_actor)
                    del app_context.get_app_state().get_highlighted_cells_actor()[cell_id_tuple]
                    # Remove from cells_vertices_values
                    app_context.get_app_state().cells_vertices_values = [
                        vertices for vertices in app_context.get_app_state().get_cells_vertices_values()
                        if not np.array_equal(vertices, cell_coords)
                    ]

        app_context.get_renderer_state().get_renderer().GetRenderWindow().Render()

    # -------------------------------------------------------------------------
    def _create_highlight_actor(self, poly_data, cell_id, cell_id_tuple, cell_coords):
        """
        Create a highlight actor for a given cell and store it in app state.
        """
        cell_ids = vtk.vtkIdTypeArray()
        cell_ids.InsertNextValue(cell_id)

        selection_node = vtk.vtkSelectionNode()
        selection_node.SetFieldType(vtk.vtkSelectionNode.CELL)
        selection_node.SetContentType(vtk.vtkSelectionNode.INDICES)
        selection_node.SetSelectionList(cell_ids)

        selection = vtk.vtkSelection()
        selection.AddNode(selection_node)

        extract_selection = vtk.vtkExtractSelection()
        extract_selection.SetInputData(0, poly_data)
        extract_selection.SetInputData(1, selection)
        extract_selection.Update()

        selected = vtk.vtkUnstructuredGrid()
        selected.ShallowCopy(extract_selection.GetOutput())

        selected_mapper = vtk.vtkDataSetMapper()
        selected_mapper.SetInputData(selected)

        selected_actor = vtk.vtkActor()
        selected_actor.SetMapper(selected_mapper)
        selected_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # red highlight

        app_context.get_renderer_state().get_renderer().AddActor(selected_actor)
        app_context.get_app_state().get_highlighted_cells_actor()[cell_id_tuple] = selected_actor
        app_context.get_app_state().get_cells_vertices_values().append(cell_coords)

        self.logger.debug(f"Cell ID {cell_id} highlighted and stored")


    def on_key_press(self, obj, event):
        """
        Handle key press events for brush size adjustment.
        '-' to decrease, '+' to increase brush size.
        """
        key = self.GetInteractor().GetKeySym()

        if key in ["minus", "underscore"]:  
            self.brush_size = 0.0
            self.logger.info(f"Brush size decreased to {self.brush_size}")

        elif key in ["plus", "equal"]:  
            self.brush_size = 0.01
            self.logger.info(f"Brush size increased to {self.brush_size}")







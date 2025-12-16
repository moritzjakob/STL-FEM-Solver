# -----------------------------------------------------------------------------
# STL Handler Service
# -----------------------------------------------------------------------------
# Description:
#   This service handles all STL-related operations in the FEM application.
#   It is responsible for:
#       - Loading STL meshes into the VTK renderer
#       - Refining mesh geometry through subdivision
#       - Updating the renderer after mesh modifications
#       - Saving refined meshes back to disk
#       - Resetting mesh state when needed
#
#   All operations are executed using the registered renderer_controller
#   accessed through the AppContext.
# -----------------------------------------------------------------------------

import os
import logging
import vtk
from stl import mesh
from PySide6.QtWidgets import QMessageBox
from fem_app.core.app_context import app_context



class STLHandler:
    """
    STLHandler
    ----------
    Service for handling STL file operations:
      - Loading STL meshes
      - Refining mesh geometry
      - Saving refined meshes
      - Resetting mesh state

    This class encapsulates all STL-specific functionality to keep
    renderer logic clean and centralized.
    """

    def __init__(self):
        """
        Initialize the STL handler with a cleanup service.
        """

        self.logger = logging.getLogger(__name__)
        self.logger.debug("STLHandler service initialized")

    # -------------------------------------------------------------------------
    def load_stl(self, file_name: str) -> None:
        """
        Load an STL file into the renderer and prepare the scene.

        Args:
            file_name (str): Absolute path to the STL file.

        Steps:
            1. Reset scene and mesh state.
            2. Convert STL to binary for robust reading.
            3. Load mesh using VTK.
            4. Create actor and add it to the renderer.
            5. Store mesh data and file reference in application state.
        """
        self.logger.info(f"Loading STL file: {file_name}")

        # Reset scene and mesh state
        app_context.get_renderer_state().get_renderer_controller().cleanup.reset_window()
        self.reset_mesh_state()
        app_context.get_renderer_state().get_renderer_controller().appearance.remove_scalar_bar_title()

        # Remove tooltip if present
        if app_context.get_renderer_state().get_tooltip_actor():
            app_context.get_renderer_state().get_tooltip_actor().VisibilityOff()
            app_context.get_renderer_state().set_tooltip_actor(None)
            self.logger.debug("Tooltip actor removed")

        # Convert STL to binary for more reliable reading
        binary_mesh = mesh.Mesh.from_file(file_name)
        file_base, _ = os.path.splitext(file_name)
        binary_mesh_file = f"{file_base}_binary.stl"
        binary_mesh.save(binary_mesh_file, mode=mesh.stl.Mode.BINARY)

        # Read STL file using VTK
        reader = vtk.vtkSTLReader()
        reader.SetFileName(binary_mesh_file)
        reader.Update()

        # Store mesh data in state
        mesh_data = reader.GetOutput()
        app_context.get_renderer_state().set_mesh_data(mesh_data)
        num_points = mesh_data.GetNumberOfPoints()
        self.logger.warning(f"STL mesh loaded with {num_points} vertices")

        # Create actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(mesh_data)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 1.0, 1.0)

        # Respect current wireframe mode
        if app_context.get_renderer_state().get_wireframe_mode():
            actor.GetProperty().SetRepresentationToWireframe()
        else:
            actor.GetProperty().SetRepresentationToSurface()

        # Add actor to scene
        app_context.get_renderer_state().get_renderer().AddActor(actor)
        app_context.get_renderer_state().set_actor(actor)
        app_context.get_renderer_state().get_renderer().ResetCamera()
        app_context.get_renderer_state().get_interactor().Initialize()
        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

        # Store current file in AppState
        app_context.get_app_state().set_current_file(file_name)
        self.logger.debug("Current file path stored in AppState.")

        # Cleanup temp file
        os.remove(binary_mesh_file)
        self.logger.debug(f"Temporary STL file removed: {binary_mesh_file}")

    # -------------------------------------------------------------------------
    def update_screen_for_stl(self, mesh_data: vtk.vtkPolyData) -> None:
        """
        Update the renderer to display the provided STL mesh data.

        Args:
            mesh_data (vtk.vtkPolyData): The mesh to display.
        """
        self.logger.debug("Updating STL display on screen")

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(mesh_data)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Keep the last used representation
        if app_context.get_renderer_state().get_wireframe_mode():
            actor.GetProperty().SetRepresentationToWireframe()
        else:
            actor.GetProperty().SetRepresentationToSurface()

        # Clear previous actors and display the new one
        app_context.get_renderer_state().get_renderer_controller().cleanup.clear_actors()
        app_context.get_renderer_state().get_renderer().AddActor(actor)
        app_context.get_renderer_state().set_actor(actor)
        app_context.get_renderer_state().get_renderer().ResetCamera()
        app_context.get_renderer_state().get_interactor().Initialize()
        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

        self.logger.info("STL screen updated with refined mesh")

    # -------------------------------------------------------------------------
    def subdivide_mesh(self, subdivisions: int):
        """
        Subdivide (refine) the current mesh.

        Args:
            subdivisions (int): Number of subdivision levels to apply.

        Returns:
            vtk.vtkPolyData | None: The refined mesh, or None if no actor is present.
        """
        actor = app_context.get_renderer_state().get_actor()
        if not actor:
            self.logger.warning("No actor present - cannot subdivide mesh")
            return None

        self.logger.info(f"Subdividing mesh with {subdivisions} levels")

        mesh_data = actor.GetMapper().GetInput()
        subdiv_filter = vtk.vtkLinearSubdivisionFilter()
        subdiv_filter.SetInputData(mesh_data)
        subdiv_filter.SetNumberOfSubdivisions(subdivisions)
        subdiv_filter.Update()

        return subdiv_filter.GetOutput()

    # -------------------------------------------------------------------------
    def refine_mesh(self) -> None:
        """
        Refine the mesh by a fixed factor (2 subdivisions)
        and update the renderer with the refined result.
        """
        self.logger.info("Refining mesh")
        refined_mesh = self.subdivide_mesh(2)
        if refined_mesh:
            app_context.get_renderer_state().set_refined_mesh(refined_mesh)
            self.update_screen_for_stl(refined_mesh)
            self.logger.info("Mesh refinement complete")
        else:
            self.logger.warning("Mesh refinement failed - no mesh present")

    # -------------------------------------------------------------------------
    def save_refined_mesh(self, original_filename: str) -> None:
        """
        Save the refined mesh to a new STL file.

        Args:
            original_filename (str): The original STL filename.
        """
        refined_mesh = app_context.get_renderer_state().get_refined_mesh()
        main_window = app_context.get_main_window()  #

        if not refined_mesh:
            self.logger.warning("No refined mesh found - nothing to save")
            if main_window:
                QMessageBox.warning(main_window, "Warning", "No refined mesh found - nothing to save.")
            return

        base_name, _ = os.path.splitext(original_filename)
        refined_filename = f"{base_name}_refined.stl"

        writer = vtk.vtkSTLWriter()
        writer.SetFileName(refined_filename)
        writer.SetInputData(refined_mesh)
        writer.Write()

        self.logger.info(f"Refined mesh saved as: {refined_filename}")

        if main_window:
            QMessageBox.information(main_window, "Mesh Saved", f"Refined mesh saved as:\n{refined_filename}")

    # -------------------------------------------------------------------------
    def reset_refinement_of_mesh(self) -> None:
        """
        Reset the refined mesh reference in the renderer state.
        """
        app_context.get_renderer_state().set_refined_mesh(None)
        self.logger.debug("Refined mesh reset")

    # -------------------------------------------------------------------------
    def reset_mesh_state(self) -> None:
        """
        Reset all mesh-related state variables in the renderer state.
        """
        app_context.get_renderer_state().set_refined_mesh(None)
        app_context.get_renderer_state().set_mesh_data(None)
        app_context.get_renderer_state().set_actor(None)
        self.logger.info("Mesh state reset")









# -----------------------------------------------------------------------------
# XDMF Handler Service
# -----------------------------------------------------------------------------
# Description:
#   This service handles the loading and visualization of simulation result
#   files in XDMF format. 
#   It is responsible for:
#       - Von Mises stress visualization
#       - Displacement visualization (color map & wireframe overlay)
#       - Stress and strain tensor component visualization
#       - Tooltip interaction for scalar fields
#       - Live mesh deformation based on displacement multiplier
#
#   All operations are executed using the registered renderer_controller
#   accessed through the AppContext.
# -----------------------------------------------------------------------------

import os
import logging
import vtk
from fem_app.core.app_context import app_context


class XDMFHandler:
    """
    XDMFHandler
    -----------
    High-level service for loading and visualizing XDMF simulation result files.

    This class encapsulates the entire visualization pipeline for XDMF files,
    including:
        - Reading unstructured grids from disk
        - Applying scalar field visualizations (Von Mises, stress, strain)
        - Applying displacement-based deformation
        - Managing wireframe overlays and lookup tables
        - Adding and updating scalar bars
        - Tooltip and picker setup for interactive inspection
        - Supporting live deformation updates via displacement multiplier

    This handler keeps renderer-specific operations separated from UI logic
    and is accessed through the 'RendererController'.
    """

    def __init__(self, cleanup, appearance):
        """
        Initialize handler with cleanup and appearance services.

        Args:
            cleanup (CleanUp): Service to reset and clear renderer state.
            appearance (Appearance): Service for visual styling and overlays.
        """
        self.cleanup = cleanup
        self.appearance = appearance
        self.logger = logging.getLogger(__name__)
        self.logger.debug("XDMFHandler service initialized")

    # -------------------------------------------------------------------------
    def load_xdmf(
        self,
        file_name: str,
        show_von_mises: bool = False,
        apply_displacement: bool = False,
        displacement_multiplier: float = 1.0,
        show_displacement_color_map: bool = False,
        show_displacement_wireframe: bool = False,
        min_von_mises: float = None,
        max_von_mises: float = None,
        show_stress: bool = False,
        show_strain: bool = False,
        stress_component: int = 0,
        strain_component: int = 0
    ) -> None:
        """
        Load an XDMF file and configure the visualization based on selected modes.

        Args:
            file_name (str): Path to the XDMF file.
            show_von_mises (bool): Display Von Mises stress field.
            apply_displacement (bool): Apply displacement deformation to mesh.
            displacement_multiplier (float): Scale factor for displacements.
            show_displacement_color_map (bool): Color mesh based on displacement magnitude.
            show_displacement_wireframe (bool): Overlay wireframe for displacement.
            min_von_mises (float, optional): Minimum scalar range for Von Mises visualization.
            max_von_mises (float, optional): Maximum scalar range for Von Mises visualization.
            show_stress (bool): Display stress tensor component.
            show_strain (bool): Display strain tensor component.
            stress_component (int): Index of stress tensor component to visualize.
            strain_component (int): Index of strain tensor component to visualize.
        """
        self.logger.info(f"Loading XDMF file: {file_name}")

        # Reset renderer and GUI state
        self.cleanup.reset_window()

        # Lookup table for scalar visualization
        lookup_table = self._create_lookup_table()

        # Read XDMF file and extract data
        unstructured_grid, point_data, original_grid = self._read_xdmf(file_name)
        if not unstructured_grid:
            self.logger.error(f"Failed to load XDMF file: {file_name}")
            return

        # Remove old scalar bar text if present
        self.appearance.remove_scalar_bar_title()

        # Extract relevant arrays (displacement, Von Mises, stress, strain)
        displacement_array, von_mises_array, stress_tensor_array, strain_tensor_array = \
            self._get_arrays(point_data)

        # Apply deformation if requested
        self._apply_displacement(
            unstructured_grid,
            displacement_array,
            apply_displacement,
            displacement_multiplier
        )

        # Create mapper for visualization
        mapper = self._create_mapper(unstructured_grid)

        # Handle selected visualization modes
        self._handle_visualization_modes(
            mapper,
            point_data,
            lookup_table,
            displacement_array,
            von_mises_array,
            stress_tensor_array,
            strain_tensor_array,
            show_von_mises,
            show_displacement_color_map,
            show_displacement_wireframe,
            show_stress,
            show_strain,
            min_von_mises,
            max_von_mises,
            stress_component,
            strain_component,
            original_grid
        )

        # Enable tooltip for scalar-based visualizations
        app_context.get_renderer_state().tooltip_enabled = any([
            show_von_mises,
            show_stress,
            show_strain,
            show_displacement_color_map,
            show_displacement_wireframe
        ])

        # Initialize tooltip & picker if required
        self._setup_tooltip_and_picker()

        # Finalize rendering
        actor = app_context.get_renderer_state().get_actor()
        actor.SetMapper(mapper)
        app_context.get_renderer_state().get_renderer().AddActor(actor)
        app_context.get_renderer_state().get_renderer().ResetCamera()
        app_context.get_renderer_state().get_interactor().Initialize()
        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

        # Store file reference
        app_context.get_app_state().set_current_file(file_name)
        self.logger.debug("Current file path stored in AppState.")
        self.logger.info("XDMF visualization loaded successfully")

    # -------------------------------------------------------------------------
    # Helper Functions
    # -------------------------------------------------------------------------
    def _create_lookup_table(self) -> vtk.vtkLookupTable:
        """
        Create a custom lookup table for scalar visualization.

        Returns:
            vtk.vtkLookupTable: Lookup table used for scalar color mapping.
        """
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)
        lut.Build()
        color_stops = [
            (0.0, (0.0, 0.0, 1.0)),   # blue
            (0.25, (0.0, 1.0, 1.0)),  # cyan
            (0.5, (0.0, 1.0, 0.0)),   # green
            (0.75, (1.0, 1.0, 0.0)),  # yellow
            (1.0, (1.0, 0.0, 0.0))    # red
        ]

        # Fill the lookup table with interpolated colors
        for i in range(256):
            t = i / 255.0
            for j in range(len(color_stops) - 1):
                t0, c0 = color_stops[j]
                t1, c1 = color_stops[j + 1]
                if t0 <= t <= t1:
                    # Linear interpolation between c0 and c1
                    f = (t - t0) / (t1 - t0)
                    r = c0[0] + f * (c1[0] - c0[0])
                    g = c0[1] + f * (c1[1] - c0[1])
                    b = c0[2] + f * (c1[2] - c0[2])
                    lut.SetTableValue(i, r, g, b, 1.0)
                    break
        return lut

    def _read_xdmf(self, file_name: str):
        """
        Load an XDMF file and return its unstructured grid and point data.

        Args:
            file_name (str): Path to the XDMF file.

        Returns:
            - vtk.vtkUnstructuredGrid | None
            - vtk.vtkPointData | None
            - vtk.vtkUnstructuredGrid (deep copy of original)
        """
        if not os.path.isfile(file_name):
            self.logger.error(f"File not found: {file_name}")
            return None, None, None

        reader = vtk.vtkXdmfReader()
        try:
            reader.SetFileName(file_name)
            reader.Update()
        except Exception as e:
            self.logger.exception(f"Error reading XDMF file: {e}")
            return None, None, None

        unstructured_grid = reader.GetOutput()
        point_data = unstructured_grid.GetPointData()

        # Keep a deep copy of the original grid (before deformation)
        app_context.get_renderer_state().set_original_grid(vtk.vtkUnstructuredGrid())
        app_context.get_renderer_state().get_original_grid().DeepCopy(unstructured_grid)

        self.logger.debug("XDMF file successfully read")
        return unstructured_grid, point_data, app_context.get_renderer_state().get_original_grid()

    def _get_arrays(self, point_data):
        """
        Find and return displacement, Von Mises, stress, and strain arrays.

        Args:
            point_data (vtk.vtkPointData): Point data from the unstructured grid.

        Returns:
            - displacement_array
            - von_mises_array
            - stress_array
            - strain_array
        """
        app_context.get_renderer_state().displacement = von_mises = stress = strain = None
        for i in range(point_data.GetNumberOfArrays()):
            array = point_data.GetArray(i)
            name = array.GetName()
            if name == "Displacement":
                app_context.get_renderer_state().set_displacement(array)
            elif name == "VonMisesStress":
                von_mises = array
            elif name == "StressTensor":
                stress = array
            elif name == "StrainTensor":
                strain = array

        self.logger.debug(
            f"Arrays found: displacement={app_context.get_renderer_state().get_displacement() is not None}, "
            f"vonMises={von_mises is not None}, stress={stress is not None}, strain={strain is not None}"
        )
        return app_context.get_renderer_state().get_displacement(), von_mises, stress, strain

    def _apply_displacement(self, grid, displacement_array, apply: bool, multiplier: float) -> None:
        """
        Apply nodal displacement to the mesh points.

        Args:
            grid (vtk.vtkUnstructuredGrid): Mesh grid to deform.
            displacement_array (vtk.vtkDataArray): Displacement vectors.
            apply (bool): Whether to apply displacement.
            multiplier (float): Displacement scaling factor.
        """
        if apply and displacement_array:
            vtk_points = grid.GetPoints()
            for i in range(vtk_points.GetNumberOfPoints()):
                x, y, z = vtk_points.GetPoint(i)
                dx, dy, dz = displacement_array.GetTuple(i)
                vtk_points.SetPoint(i, x + multiplier * dx, y + multiplier * dy, z + multiplier * dz)
            self.logger.debug(f"Applied displacement with multiplier={multiplier}")

    def _create_mapper(self, grid) -> vtk.vtkDataSetMapper:
        """
        Create a VTK dataset mapper for the given grid.

        Args:
            grid (vtk.vtkUnstructuredGrid): The mesh grid to map.

        Returns:
            vtk.vtkDataSetMapper: Configured mapper for rendering.
        """
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(grid)
        return mapper

    # -----------------------------------------------------------------------------
    # Visualization Modes
    # -----------------------------------------------------------------------------
    def _handle_visualization_modes(
        self, mapper, point_data, lookup_table,
        displacement_array, von_mises_array, stress_tensor_array, strain_tensor_array,
        show_von_mises, show_displacement_color_map, show_displacement_wireframe,
        show_stress, show_strain, min_von_mises, max_von_mises,
        stress_component, strain_component, original_grid
    ):
        """
        Handle all supported visualization modes in a defined priority order.

        Visualization Priority:
            1. Displacement Color Map
            2. Displacement Wireframe Overlay
            3. Von Mises Stress
            4. Stress Tensor Component
            5. Strain Tensor Component
            6. Default (no scalar visualization)

        This ensures that only one visualization mode is active at a time.
        """
        if displacement_array and show_displacement_color_map:
            self._show_displacement_colormap(mapper, point_data, displacement_array, lookup_table)
        elif show_displacement_wireframe and displacement_array:
            self._show_wireframe_overlay(mapper, point_data, displacement_array, lookup_table, original_grid)
        elif show_von_mises and von_mises_array:
            self._show_von_mises(mapper, point_data, von_mises_array, lookup_table, min_von_mises, max_von_mises)
        elif show_stress and stress_tensor_array:
            self._show_stress_tensor(mapper, point_data, stress_tensor_array, lookup_table, stress_component)
        elif show_strain and strain_tensor_array:
            self._show_strain_tensor(mapper, point_data, strain_tensor_array, lookup_table, strain_component)
        else:
            app_context.get_renderer_state().set_actor(vtk.vtkActor())
            app_context.get_renderer_state().get_actor().GetProperty().SetColor(1.0, 1.0, 1.0)
            mapper.ScalarVisibilityOff()
            self.logger.debug("No scalar visualization selected")

    # -------------------------------------------------------------------------
    # Visualization Helpers
    # -------------------------------------------------------------------------
    def _show_displacement_colormap(self, mapper, point_data, displacement_array, lookup_table):
        """
        Display the displacement magnitude as a color map on the mesh.

        Args:
            mapper (vtk.vtkDataSetMapper): Mapper to configure.
            point_data (vtk.vtkPointData): Point data for scalar arrays.
            displacement_array (vtk.vtkDataArray): Displacement vectors.
            lookup_table (vtk.vtkLookupTable): Lookup table for color mapping.
        """
        self.logger.info("Showing displacement magnitude colormap")
        self.appearance.create_scalar_bar_title("Displacement Magnitude")

        # Compute displacement magnitude
        disp_mag_array = vtk.vtkDoubleArray()
        disp_mag_array.SetName("Displacement Magnitude")
        disp_mag_array.SetNumberOfComponents(1)
        disp_mag_array.SetNumberOfTuples(displacement_array.GetNumberOfTuples())
        for i in range(displacement_array.GetNumberOfTuples()):
            dx, dy, dz = displacement_array.GetTuple(i)
            disp_mag_array.SetTuple1(i, (dx**2 + dy**2 + dz**2) ** 0.5)

        point_data.AddArray(disp_mag_array)
        point_data.SetActiveScalars("Displacement Magnitude")

        mapper.SelectColorArray("Displacement Magnitude")
        mapper.SetScalarModeToUsePointData()
        mapper.SetScalarRange(disp_mag_array.GetRange())
        mapper.SetLookupTable(lookup_table)

        # Add scalar bar to renderer
        self._add_scalar_bar(lookup_table)

    def _show_wireframe_overlay(self, mapper, point_data, displacement_array, lookup_table, original_grid):
        """
        Overlay a wireframe of the undeformed mesh on top of the deformed displacement colormap.
        """
        self.logger.info("Showing displacement wireframe overlay")

        wireframe_actor = vtk.vtkActor()
        wireframe_mapper = vtk.vtkDataSetMapper()
        wireframe_mapper.SetInputData(original_grid)
        wireframe_mapper.ScalarVisibilityOff()

        wireframe_actor.SetMapper(wireframe_mapper)
        wireframe_actor.GetProperty().SetRepresentationToWireframe()
        wireframe_actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        wireframe_actor.GetProperty().SetLineWidth(1.5)
        wireframe_actor.GetProperty().SetOpacity(0.3)

        app_context.get_renderer_state().get_renderer().AddActor(wireframe_actor)
        self._show_displacement_colormap(mapper, point_data, displacement_array, lookup_table)

    def _show_von_mises(self, mapper, point_data, von_mises_array, lookup_table, min_von_mises, max_von_mises):
        """
        Display Von Mises stress as scalar field visualization.
        """
        self.logger.info("Showing Von Mises stress visualization")
        self.appearance.create_scalar_bar_title("Von Mises Stress")
        point_data.SetActiveScalars(von_mises_array.GetName())
        mapper.SelectColorArray(von_mises_array.GetName())
        mapper.SetScalarModeToUsePointData()

        min_val = min_von_mises or von_mises_array.GetRange()[0]
        max_val = max_von_mises or von_mises_array.GetRange()[1]
        mapper.SetScalarRange(min_val, max_val)
        mapper.SetLookupTable(lookup_table)

        self._add_scalar_bar(lookup_table)

    def _show_stress_tensor(self, mapper, point_data, stress_tensor_array, lookup_table, stress_component):
        """
        Display a specific component of the stress tensor.
        """
        self.logger.info(f"Showing stress tensor component [{stress_component}]")
        self.appearance.create_scalar_bar_title(f"StressTensor[{stress_component}]")
        point_data.SetActiveScalars(stress_tensor_array.GetName())
        mapper.SelectColorArray(stress_tensor_array.GetName())
        mapper.SetScalarModeToUsePointData()
        mapper.ColorByArrayComponent(stress_tensor_array.GetName(), stress_component)
        scalar_range = stress_tensor_array.GetRange(stress_component)
        mapper.SetScalarRange(scalar_range[0], scalar_range[1])
        mapper.SetLookupTable(lookup_table)
        self._add_scalar_bar(lookup_table)

    def _show_strain_tensor(self, mapper, point_data, strain_tensor_array, lookup_table, strain_component):
        """
        Display a specific component of the strain tensor.
        """
        self.logger.info(f"Showing strain tensor component [{strain_component}]")
        self.appearance.create_scalar_bar_title(f"StrainTensor[{strain_component}]")
        point_data.SetActiveScalars(strain_tensor_array.GetName())
        mapper.SelectColorArray(strain_tensor_array.GetName())
        mapper.SetScalarModeToUsePointData()
        mapper.ColorByArrayComponent(strain_tensor_array.GetName(), strain_component)
        scalar_range = strain_tensor_array.GetRange(strain_component)
        mapper.SetScalarRange(scalar_range[0], scalar_range[1])
        mapper.SetLookupTable(lookup_table)
        self._add_scalar_bar(lookup_table)

    def _add_scalar_bar(self, lookup_table):
        """
        Add a scalar bar actor for scalar visualizations.
        """
        app_context.get_renderer_state().set_actor(vtk.vtkActor())
        app_context.get_renderer_state().set_scalar_bar(vtk.vtkScalarBarActor())
        bar = app_context.get_renderer_state().get_scalar_bar()
        bar.SetLookupTable(lookup_table)
        bar.SetNumberOfLabels(5)
        bar.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        bar.SetPosition(0.85, 0.1)
        bar.SetWidth(0.1)
        bar.SetHeight(0.8)
        app_context.get_renderer_state().get_renderer().AddActor(bar)

    # -------------------------------------------------------------------------
    # Live Deformation
    # -------------------------------------------------------------------------
    def _apply_deformation_live(self, multiplier):
        """
        Apply live deformation to the mesh using the original grid and the
        currently loaded displacement array. This allows dynamic deformation
        updates, when the slider is used to scale displacement.

        Args:
            multiplier (float): Displacement scaling factor.
        """
        self.logger.debug("Applying live deformation with multiplier=%s", multiplier)

        if not hasattr(app_context.get_renderer_state(), "original_grid") or app_context.get_renderer_state().get_original_grid() is None:
            self.logger.warning("No original_grid found in renderer_state. Cannot apply deformation.")
            return

        actor = app_context.get_renderer_state().get_actor()
        if actor is None or actor.GetMapper() is None:
            self.logger.warning("No actor or mapper found in renderer_state. Cannot apply deformation.")
            return

        dataset = actor.GetMapper().GetInput()
        if dataset is None:
            self.logger.warning("No dataset found in actor's mapper. Cannot apply deformation.")
            return

        displacement_array = dataset.GetPointData().GetArray("Displacement")
        if displacement_array is None:
            self.logger.warning("No 'Displacement' array found in dataset. Cannot apply deformation.")
            return

        original_points = app_context.get_renderer_state().get_original_grid().GetPoints()
        current_points = dataset.GetPoints()
        if original_points is None or current_points is None:
            self.logger.warning("Points not found in original_grid or dataset. Cannot apply deformation.")
            return

        num_points = original_points.GetNumberOfPoints()
        for i in range(num_points):
            px, py, pz = original_points.GetPoint(i)
            dx, dy, dz = displacement_array.GetTuple(i)
            current_points.SetPoint(i, px + multiplier * dx, py + multiplier * dy, pz + multiplier * dz)

        current_points.Modified()
        dataset.Modified()
        app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()
        self.logger.info("Live deformation applied with multiplier %s", multiplier)

    # -------------------------------------------------------------------------
    # Tooltip & Picker
    # -------------------------------------------------------------------------
    def _setup_tooltip_and_picker(self):
        """
        Initialize tooltip and point picker if scalar visualization is active.
        """
        if not app_context.get_renderer_state().is_tooltip_enabled():
            self.logger.debug("Tooltip disabled - skipping picker setup")
            return

        # Remove existing tooltip actor if present
        if app_context.get_renderer_state().get_tooltip_actor():
            app_context.get_renderer_state().get_renderer().RemoveActor(app_context.get_renderer_state().get_tooltip_actor())

        # Create tooltip actor
        tooltip_actor = vtk.vtkTextActor()
        tooltip_actor.GetTextProperty().SetFontSize(14)
        tooltip_actor.GetTextProperty().SetColor(1, 1, 1)
        tooltip_actor.SetInput("")
        app_context.get_renderer_state().set_tooltip_actor(tooltip_actor)
        app_context.get_renderer_state().get_renderer().AddActor2D(tooltip_actor)

        # Initialize point picker
        app_context.get_renderer_state().set_picker(vtk.vtkPointPicker())

        def mouse_move_callback(obj, event):
            if not app_context.get_renderer_state().is_tooltip_enabled() or not tooltip_actor:
                return

            actor = app_context.get_renderer_state().get_actor()
            if not actor or not actor.GetMapper():
                return

            x, y = app_context.get_renderer_state().get_interactor().GetEventPosition()
            picker = app_context.get_renderer_state().get_picker()

            if picker.Pick(x, y, 0, app_context.get_renderer_state().get_renderer()):
                pid = picker.GetPointId()
                if pid >= 0:
                    active_scalars = actor.GetMapper().GetInput().GetPointData().GetScalars()
                    if active_scalars:
                        num_comp = active_scalars.GetNumberOfComponents()
                        if num_comp == 1:
                            value = active_scalars.GetTuple1(pid)
                        elif num_comp == 9:
                            comp_idx = getattr(self, "current_tensor_component", 0)
                            value = active_scalars.GetTuple(pid)[comp_idx]
                        else:
                            value = active_scalars.GetTuple(pid)[0]
                        tooltip_actor.SetInput(f"{value:.5f}")
                        tooltip_actor.SetPosition(x + 10, y + 10)
                    else:
                        tooltip_actor.SetInput("")
                else:
                    tooltip_actor.SetInput("")
            app_context.get_renderer_state().get_vtk_widget().GetRenderWindow().Render()

        app_context.get_renderer_state().get_interactor().AddObserver("MouseMoveEvent", mouse_move_callback)
        self.logger.debug("Tooltip and picker initialized")






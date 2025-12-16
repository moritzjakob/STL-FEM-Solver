# -----------------------------------------------------------------------------
# Object Movement Interactor Style
# -----------------------------------------------------------------------------
# Description:
#   This interactor style enables interactive translation and rotation
#   of 3D actors in the renderer. It was implemented at the beginning with the idea 
#   to allow FEM Analysis with 2 Objects (one fixed, one moving and applying the force).
#
#   It provides:
#       - Left-click to select an actor
#       - Axis toggling (X, Y, Z) and rotation mode via keyboard shortcuts or sidebar
#       - Dragging to translate or rotate the selected actor
#       - Visual feedback through on-screen axis buttons
#
#   This tool is used to move around the XDMF object. 
#
#   It is typically triggered via the InteractorManager through the
#   RendererController.
#
# Controls:
#   - Left Mouse Button       -> Select and drag actor
#   - X / Y / Z keys          -> Toggle movement axes
#   - D key                   -> Toggle rotation mode
# -----------------------------------------------------------------------------

import logging
import vtk
import math

from fem_app.core.app_context import app_context


class InteractorObjectMovementStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    InteractorObjectMovementStyle
    -----------------------------
    Custom VTK interactor style for interactive object movement and rotation.

    Features:
        - Select actor with left mouse click
        - Translate or rotate actor by dragging
        - Toggle movement/rotation axes with keyboard shortcuts or sidebar
        - On-screen axis button indicators for feedback
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Object Movement interactor initialized")

        # Interaction state
        self.is_dragging = False
        self.previous_mouse_position = None
        self.move_scale = 0.01
        self.rotation_scale = 0.5

        # UI axis button references
        self.x_button = None
        self.y_button = None
        self.z_button = None
        self.rotate_button = None

        if app_context.get_renderer_state().get_renderer():
            self._create_buttons()

        # Event bindings
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        self.AddObserver("MouseMoveEvent", self.mouse_move_event)
        self.AddObserver("KeyPressEvent", self.on_key_press_edit_event)

    # -------------------------------------------------------------------------
    def _create_buttons(self):
        """
        Create on-screen axis buttons (X, Y, Z, Rotate) for visual feedback.
        """
        def make_button(label, xpos):
            actor = vtk.vtkTextActor()
            actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
            actor.SetPosition(xpos, 0.9)
            actor.GetTextProperty().SetColor(1, 0, 0)  # red = inactive
            actor.GetTextProperty().SetFontSize(24)
            actor.SetInput(label)
            app_context.get_renderer_state().get_renderer().AddActor(actor)
            return actor

        self.x_button = make_button("X", 0.1)
        self.y_button = make_button("Y", 0.2)
        self.z_button = make_button("Z", 0.3)
        self.rotate_button = make_button("Rotate", 0.4)
        self.logger.debug("Movement buttons created")

    # -------------------------------------------------------------------------
    def _update_button_colors(self):
        """
        Update on-screen button colors based on current movement/rotation state.
        Green = active, Red = inactive.
        """
        if not app_context.get_renderer_state().get_renderer():
            return

        def set_color(actor, active):
            actor.GetTextProperty().SetColor(0, 1, 0) if active else actor.GetTextProperty().SetColor(1, 0, 0)

        set_color(self.x_button, app_context.get_app_state().get_movement_axis()["X"])
        set_color(self.y_button, app_context.get_app_state().get_movement_axis()["Y"])
        set_color(self.z_button, app_context.get_app_state().get_movement_axis()["Z"])
        set_color(self.rotate_button, app_context.get_app_state().is_rotation_mode_enabled())

        self.GetInteractor().GetRenderWindow().Render()

    # -------------------------------------------------------------------------
    def left_button_press_event(self, obj, event):
        """
        Select actor under the mouse cursor and enable dragging.
        """
        click_pos = self.GetInteractor().GetEventPosition()
        picker = vtk.vtkCellPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, app_context.get_renderer_state().get_renderer())
        picked_actor = picker.GetActor()

        # Reset previous actor highlight
        if app_context.get_renderer_state().get_actor():
            prev_actor = app_context.get_renderer_state().get_actor()
            prev_actor.GetProperty().SetColor(1, 1, 1)
            prev_actor.GetProperty().EdgeVisibilityOff()

        app_context.get_renderer_state().set_actor(picked_actor)

        # Highlight new actor
        if picked_actor:
            picked_actor.GetProperty().SetColor(0, 1, 0)
            picked_actor.GetProperty().EdgeVisibilityOn()
            self.is_dragging = True
            self.previous_mouse_position = click_pos
            self.logger.info("Actor selected for dragging/rotating")
        else:
            self.OnLeftButtonDown()

        self._sync_with_sidebar()
        self._update_button_colors()

    # -------------------------------------------------------------------------
    def _sync_with_sidebar(self):
        """
        Synchronize axis selection and rotation mode with sidebar UI.
        """
        sidebar = app_context.get_sidebar()
        if sidebar:
            app_context.get_app_state().set_movement_axis("X", sidebar.edit_section.x_movement_checkbox.isChecked())
            app_context.get_app_state().set_movement_axis("Y", sidebar.edit_section.y_movement_checkbox.isChecked())
            app_context.get_app_state().set_movement_axis("Z", sidebar.edit_section.z_movement_checkbox.isChecked())
            app_context.get_app_state().enable_rotation_mode(sidebar.edit_section.r_movement_checkbox.isChecked())

    # -------------------------------------------------------------------------
    def left_button_release_event(self, obj, event):
        """
        Handle mouse release:
        - Stop dragging or rotation if active
        - Otherwise fall back to default camera control
        """
        if self.is_dragging:
            self.is_dragging = False
            self.logger.debug("Dragging finished.")
        elif hasattr(self, 'rotate_mode') and self.rotate_mode:
            self.rotate_mode = False
            self.logger.debug("Rotation mode disabled.")
        else:
            self.OnLeftButtonUp()
            self.logger.debug("Default camera interaction triggered on mouse release.")

    # -------------------------------------------------------------------------
    def mouse_move_event(self, obj, event):
        """
        Translate or rotate actor while dragging, depending on the current mode.
        """
        actor = app_context.get_renderer_state().get_actor()
        self._sync_with_sidebar()

        if self.is_dragging and actor:
            current_pos = self.GetInteractor().GetEventPosition()
            dx = current_pos[0] - self.previous_mouse_position[0] if self.previous_mouse_position else 0
            dy = current_pos[1] - self.previous_mouse_position[1] if self.previous_mouse_position else 0

            if app_context.get_app_state().is_rotation_mode_enabled():
                self._rotate_actor_by_drag(dx, dy)
            else:
                self._translate_actor_by_drag(dx, dy)

            self.previous_mouse_position = current_pos
        else:
            self.OnMouseMove()

    # -------------------------------------------------------------------------
    def _translate_actor_by_drag(self, dx, dy):
        """
        Translate actor along active axes according to mouse drag distance.
        """
        actor = app_context.get_renderer_state().get_actor()
        if not actor:
            return

        pos = list(actor.GetPosition())
        axis_state = app_context.get_app_state().get_movement_axis()

        if axis_state["X"]:
            pos[0] += dx * self.move_scale
        if axis_state["Y"]:
            pos[1] += dy * self.move_scale
        if axis_state["Z"]:
            pos[2] += (dx + dy) * self.move_scale * 0.5

        actor.SetPosition(pos)
        self.GetInteractor().GetRenderWindow().Render()
        self.logger.debug(f"Actor translated to {pos}")

    # -------------------------------------------------------------------------
    def _rotate_actor_by_drag(self, dx, dy):
        """
        Rotate actor around active axes according to mouse drag distance.
        """
        actor = app_context.get_renderer_state().get_actor()
        if not actor:
            return

        transform = vtk.vtkTransform()
        transform.Identity()

        rotation_x = dy * self.rotation_scale
        rotation_y = dx * self.rotation_scale
        axis_state = app_context.get_app_state().get_movement_axis()

        if axis_state["X"]:
            transform.RotateX(rotation_x)
        if axis_state["Y"]:
            transform.RotateY(rotation_y)
        if axis_state["Z"]:
            transform.RotateZ(rotation_x + rotation_y)

        current_transform = actor.GetUserTransform()
        if not current_transform:
            current_transform = vtk.vtkTransform()
            actor.SetUserTransform(current_transform)
        current_transform.Concatenate(transform)

        self.GetInteractor().GetRenderWindow().Render()
        self.logger.debug(f"Actor rotated: Δx={rotation_x:.2f}, Δy={rotation_y:.2f}")

    # -------------------------------------------------------------------------
    def on_key_press_edit_event(self, obj, event):
        """
        Handle keyboard shortcuts for toggling movement axes and rotation mode.
        """
        key = self.GetInteractor().GetKeySym()
        sidebar = app_context.get_sidebar()

        if key == 'x':
            new_state = not app_context.get_app_state().get_movement_axis()["X"]
            app_context.get_app_state().set_movement_axis("X", new_state)
            if sidebar:
                sidebar.edit_section.x_movement_checkbox.setChecked(new_state)

        elif key == 'y':
            new_state = not app_context.get_app_state().get_movement_axis()["Y"]
            app_context.get_app_state().set_movement_axis("Y", new_state)
            if sidebar:
                sidebar.edit_section.y_movement_checkbox.setChecked(new_state)

        elif key == 'z':
            new_state = not app_context.get_app_state().get_movement_axis()["Z"]
            app_context.get_app_state().set_movement_axis("Z", new_state)
            if sidebar:
                sidebar.edit_section.z_movement_checkbox.setChecked(new_state)

        elif key == 'd':
            new_state = not app_context.get_app_state().is_rotation_mode_enabled()
            app_context.get_app_state().enable_rotation_mode(new_state)
            if sidebar:
                sidebar.edit_section.r_movement_checkbox.setChecked(new_state)

        else:
            self.logger.debug(f"Unused key pressed: {key}")
            return

        self._update_button_colors()
        self.GetInteractor().GetRenderWindow().Render()

    # -------------------------------------------------------------------------
    def reset_state(self):
        """
        Reset the interactor state:
        - Deselect actor and remove highlight
        - Remove axis buttons
        - Reset axis and rotation mode flags
        """
        actor = app_context.get_renderer_state().get_actor()

        if actor:
            actor.GetProperty().SetColor(1, 1, 1)
            actor.GetProperty().EdgeVisibilityOff()
            app_context.get_renderer_state().set_actor(None)

        if app_context.get_renderer_state():
            app_context.get_renderer_state().get_renderer().RemoveActor(self.x_button)
            app_context.get_renderer_state().get_renderer().RemoveActor(self.y_button)
            app_context.get_renderer_state().get_renderer().RemoveActor(self.z_button)
            app_context.get_renderer_state().get_renderer().RemoveActor(self.rotate_button)

        app_context.get_app_state().movement_axis = {"X": False, "Y": False, "Z": False}
        app_context.get_app_state().enable_rotation_mode(False)

        self.is_dragging = False
        self.previous_mouse_position = None

        self.GetInteractor().GetRenderWindow().Render()
        self.logger.debug("Object Movement interactor reset and UI buttons removed")











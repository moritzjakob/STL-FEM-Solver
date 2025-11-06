# -----------------------------------------------------------------------------
# Application Context
# -----------------------------------------------------------------------------
# Description:
#   This module provides a singleton AppContext class that acts as the central
#   hub for managing shared application state. It bundles:
#     - GUI component references (main window, sidebar, header)
#     - App state (simulation control and metadata)
#     - Renderer state (VTK and visualization data)
#
#   AppContext allows different parts of the application (GUI, solvers,
#   utilities) to access or update global state in a structured way without
#   tight coupling.
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import Any, Optional

from fem_app.gui.gui_state.app_state import AppState, app_state
from fem_app.renderer.renderer_state import RendererState, renderer_state

logger = logging.getLogger(__name__)


class AppContext:
    """
    Central application context (Singleton).

    Acts as a single source for:
        - GUI component references
        - App state (AppState)å
        - Renderer state (RendererState)

    This class provides accessor and registration methods for these
    components and exposes global utilities
    """

    def __init__(self) -> None:
        """
        Initialize the application context with default state and no GUI references.
        """

        # GUI components
        self._main_window: Optional[Any] = None
        self._sidebar: Optional[Any] = None
        self._header: Optional[Any] = None

        # Core state
        self._app_state: AppState = app_state
        self._renderer_state: RendererState = renderer_state

        logger.debug("AppContext initialized")
    
    # -----------------------------
    # GUI Components
    # -----------------------------
    def register_main_window(self, main_window: Any) -> None:
        """
        Register the main application window instance.

        Args:
            main_window: The QMainWindow instance of the GUI.
        """
        self._main_window = main_window
        logger.debug("Main window registered")

    def get_main_window(self) -> Optional[Any]:
        """
        Return the registered main window instance.

        Returns:
            QMainWindow or None if not registered.
        """
        return self._main_window

    def register_sidebar(self, sidebar: Any) -> None:
        """
        Register the sidebar widget instance.

        Args:
            sidebar: The sidebar QWidget.
        """
        self._sidebar = sidebar
        logger.debug("Sidebar registered")

    def get_sidebar(self) -> Optional[Any]:
        """
        Return the registered sidebar widget.

        Returns:
            Sidebar QWidget or None if not registered.
        """
        return self._sidebar

    def register_header(self, header: Any) -> None:
        """
        Register the header widget instance.

        Args:
            header: The header QWidget.
        """
        self._header = header
        logger.debug("Header registered")

    def get_header(self) -> Optional[Any]:
        """
        Return the registered header widget.

        Returns:
            Header QWidget or None if not registered.
        """
        return self._header

    def clear_gui_references(self) -> None:
        """
        Clear references to all registered GUI components.
        """
        self._main_window = None
        self._sidebar = None
        self._header = None
        logger.debug("GUI references cleared")

    # -----------------------------
    # App State
    # -----------------------------
    def register_app_state(self, state: AppState) -> None:
        """
        Register a custom App state instance.

        Args:
            state: An instance of AppState.
        """
        self._app_state = state
        logger.debug("AppState registered")

    def get_app_state(self) -> AppState:
        """
        Return the global App state object.

        Returns:
            AppState: Shared App state object.
        """
        return self._app_state

    def reset_app_state(self) -> None:
        """
        Reset the App state to its default values.
        """
        if self._app_state is not None:
            self._app_state.reset()
            logger.debug("AppState reset via AppContext")

    # -----------------------------
    # Renderer State
    # -----------------------------
    def register_renderer_state(self, state: RendererState) -> None:
        """
        Register a custom RendererState instance.

        Args:
            state: An instance of RendererState.
        """
        self._renderer_state = state
        logger.debug("RendererState registered")

    def get_renderer_state(self) -> RendererState:
        """
        Return the registered renderer state object.

        Returns:
            RendererState: Shared visualization and rendering state.
        """
        return self._renderer_state

    def reset_renderer_state(self) -> None:
        """
        Reset the renderer state to its default values.
        """
        if self._renderer_state is not None:
            self._renderer_state.reset()
            logger.debug("RendererState reset via AppContext")

    # -----------------------------
    # Combined Utilities
    # -----------------------------
    def reset_all(self) -> None:
        """
        Reset both FEM application and renderer states.
        Does not clear GUI references automatically.
        """
        self.reset_app_state()
        self.reset_renderer_state()
        logger.info("All application states have been reset")


# Singleton instance of the application context
app_context = AppContext()








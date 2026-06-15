from __future__ import annotations

from enum import Enum

"""Keyboard controller types and helpers.

This module provides the KeyboardCommand enum used to represent
operator keyboard actions that control the ScenarioRunner and Shows.
"""


class KeyboardCommand(Enum):
    """Operator keyboard commands.

    Values match the ScenarioCommand values used by ScenarioRunner.
    """

    PAUSE = "pause"

    RESUME = "resume"

    NEXT_SHOW = "next_show"

    PREVIOUS_SHOW = "previous_show"

    RESTART_SHOW = "restart_show"

    JUMP_TO_SHOW = "jump_to_show"

    LAND = "land"

    EMERGENCY = "emergency"


from .controller import KeyboardController

__all__ = ["KeyboardCommand", "KeyboardController"]

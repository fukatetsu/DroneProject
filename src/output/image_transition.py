from __future__ import annotations

from typing import Any

import cv2
import numpy as np


class ImageTransition:
    """
    Image transition processor.

    This class generates intermediate frames between two images.
    It does not manage rendering, timing, or display.

    Responsibilities:
        - Blend two images
        - Generate transition effects
        - Apply easing functions

    Non-responsibilities:
        - Loading images
        - Displaying images
        - Managing asyncio tasks

    Example:
        transition = ImageTransition()

        frame = transition.create_frame(
            image_a,
            image_b,
            progress=0.5,
            effect="fade",
        )

    Attributes:
        None
    """


    def create_frame(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
        effect: str,
    ) -> np.ndarray:
        """
        Create a transition frame.

        Args:
            img_from:
                Source image.
                Displayed when progress is 0.0.

            img_to:
                Destination image.
                Displayed when progress is 1.0.

            progress:
                Transition progress.

                Range:
                    0.0 -> img_from
                    1.0 -> img_to

            effect:
                Transition effect name.

                Supported:
                    - fade
                    - wipe_left
                    - wipe_right
                    - wipe_fade_left

        Returns:
            Generated image frame.
        """

        if effect == "fade":

            return self._fade(
                img_from,
                img_to,
                progress,
            )


        if effect == "wipe_left":

            return self._wipe_left(
                img_from,
                img_to,
                progress,
            )


        if effect == "wipe_right":

            return self._wipe_right(
                img_from,
                img_to,
                progress,
            )


        if effect == "wipe_fade_left":

            return self._wipe_fade_left(
                img_from,
                img_to,
                progress,
            )
        if effect == "wipe_fade_right":

            return self._wipe_fade_right(
                img_from,
                img_to,
                progress,
            )

        raise ValueError(
            f"Unknown transition effect: {effect}"
        )



    def apply_easing(
        self,
        progress: float,
        easing: str,
    ) -> float:
        """
        Apply easing function.

        Args:
            progress:
                Linear progress.
                Range: 0.0 - 1.0

            easing:
                Easing function name.

                Supported:
                    - linear
                    - ease_in
                    - ease_out
                    - ease_in_out

        Returns:
            Modified progress value.
        """

        progress = max(
            0.0,
            min(
                1.0,
                progress,
            ),
        )


        if easing == "linear":

            return progress


        if easing == "ease_in":

            return progress * progress


        if easing == "ease_out":

            return (
                1
                -
                (1-progress) ** 2
            )


        if easing == "ease_in_out":

            return (
                3 * progress ** 2
                -
                2 * progress ** 3
            )


        raise ValueError(
            f"Unknown easing: {easing}"
        )



    def _fade(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """
        Alpha blend transition.

        Example:
            progress=0.5

            result =
                img_from * 0.5
                +
                img_to * 0.5
        """

        return cv2.addWeighted(
            img_from,
            1-progress,
            img_to,
            progress,
            0,
        )



    def _wipe_left(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """
        Replace image from left to right.

        The destination image appears from the left side.
        """

        height, width, _ = img_from.shape

        edge = int(
            width * progress
        )


        result = img_from.copy()

        result[:, :edge] = img_to[:, :edge]

        return result



    def _wipe_right(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """
        Replace image from right to left.
        """

        height, width, _ = img_from.shape

        edge = int(
            width * (1-progress)
        )


        result = img_from.copy()

        result[:, edge:] = img_to[:, edge:]

        return result

    def _wipe_fade_left(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """
        Left-to-right wipe with feather.
        """

        h, w = img_from.shape[:2]

        feather = max(2, int(w * 0.05))
        edge = progress * w

        x = np.arange(w, dtype=np.float32)

        mask = np.zeros(w, dtype=np.float32)

        # 完全に切り替わった領域
        mask[x <= edge - feather] = 1.0

        # フェザー領域
        idx = (x > edge - feather) & (x < edge)
        mask[idx] = (edge - x[idx]) / feather

        mask = np.broadcast_to(mask, (h, w))[..., None]

        result = (
            img_from.astype(np.float32) * (1.0 - mask)
            + img_to.astype(np.float32) * mask
        )

        return result.astype(np.uint8)

    def _wipe_fade_right(
        self,
        img_from: np.ndarray,
        img_to: np.ndarray,
        progress: float,
    ) -> np.ndarray:
        """
        Right-to-left wipe with feather.
        """

        h, w = img_from.shape[:2]

        feather = max(2, int(w * 0.05))
        edge = (1.0 - progress) * w

        x = np.arange(w, dtype=np.float32)

        mask = np.zeros(w, dtype=np.float32)

        # 完全に切り替わった領域
        mask[x >= edge + feather] = 1.0

        # フェザー領域
        idx = (x < edge + feather) & (x > edge)
        mask[idx] = (x[idx] - edge) / feather

        mask = np.broadcast_to(mask, (h, w))[..., None]

        result = (
            img_from.astype(np.float32) * (1.0 - mask)
            + img_to.astype(np.float32) * mask
        )

        return result.astype(np.uint8)
"""Conservative color correction for underwater photogrammetry images."""

from __future__ import annotations

from typing import Any


def enhance_underwater(image: Any) -> Any:
    """Apply the established OpenReef underwater correction sequence."""
    import cv2
    import numpy as np

    image_float = image.astype(np.float32) / 255.0
    blue, green, red = cv2.split(image_float)
    red = red + 0.12 * (green - red) * (1.0 - red)
    corrected = cv2.merge([blue, green, np.clip(red, 0, 1)])
    corrected = np.clip(corrected * 255.0, 0, 255).astype(np.uint8)

    image_float = corrected.astype(np.float32)
    blue, green, red = cv2.split(image_float)
    mean_gray = (np.mean(blue) + np.mean(green) + np.mean(red)) / 3.0
    blue *= mean_gray / max(np.mean(blue), 1e-6)
    green *= mean_gray / max(np.mean(green), 1e-6)
    red *= mean_gray / max(np.mean(red), 1e-6)
    balanced = np.clip(cv2.merge([blue, green, red]), 0, 255).astype(np.uint8)

    lab = cv2.cvtColor(balanced, cv2.COLOR_BGR2LAB)
    luminance, channel_a, channel_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    corrected = cv2.cvtColor(
        cv2.merge([clahe.apply(luminance), channel_a, channel_b]),
        cv2.COLOR_LAB2BGR,
    )

    gamma_table = np.array(
        [((value / 255.0) ** (1.0 / 0.95)) * 255 for value in np.arange(256)]
    ).astype(np.uint8)
    corrected = cv2.LUT(corrected, gamma_table)
    blurred = cv2.GaussianBlur(corrected, (0, 0), 1.0)
    sharpened = cv2.addWeighted(corrected, 1.10, blurred, -0.10, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)

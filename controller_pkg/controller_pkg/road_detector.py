import cv2
import numpy as np


def detect_road(frame):
    """
    Detect the road centre from a camera image.

    Args:
        frame: OpenCV BGR image.

    Returns:
        error: Horizontal error relative to image centre,
               or None if no road is detected.
        debug_frame: Image with detection visualizations.
        mask: Binary road detection mask.
    """

    height, width = frame.shape[:2]

    # Convert BGR image to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Initial grey-road thresholds
    lower_grey = np.array([0, 0, 40])
    upper_grey = np.array([179, 65, 210])

    # Binary mask: white = candidate road
    mask = cv2.inRange(hsv, lower_grey, upper_grey)

    # Select a horizontal row near the robot
    row = int(height * 0.85)

    chosen_row = mask[row, :]

    # Find all candidate road pixels
    road_positions = np.where(chosen_row == 255)[0]

    debug_frame = frame.copy()

    # Draw the image centre
    image_center = width // 2

    cv2.line(
        debug_frame,
        (image_center, 0),
        (image_center, height),
        (0, 0, 255),
        2
    )

    if len(road_positions) == 0:
        return None, debug_frame, mask

    # Find road centre
    road_center = int(np.mean(road_positions))

    # Calculate horizontal error
    error = road_center - image_center

    # Draw selected detection row
    cv2.line(
        debug_frame,
        (0, row),
        (width, row),
        (255, 0, 0),
        2
    )

    # Draw detected road centre
    cv2.circle(
        debug_frame,
        (road_center, row),
        10,
        (0, 255, 0),
        -1
    )

    cv2.putText(
        debug_frame,
        f"Error: {error}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )

    return error, debug_frame, mask
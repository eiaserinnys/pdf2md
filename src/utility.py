def check_overlap(rect1, rect2):
    # Rectangles are defined as (x1, y1, x2, y2)
    x1_rect1, y1_rect1, x2_rect1, y2_rect1 = rect1
    x1_rect2, y1_rect2, x2_rect2, y2_rect2 = rect2

    # Check if one rectangle is to the right of the other
    if x1_rect1 > x2_rect2 or x1_rect2 > x2_rect1:
        return False

    # Check if one rectangle is above the other
    if y1_rect1 > y2_rect2 or y1_rect2 > y2_rect1:
        return False

    return True

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

def get_image_extent(widget, pix):
    window_width = max(widget.winfo_width(), 1)  # ensure width is at least 1
    window_height = max(widget.winfo_height(), 1)  # ensure height is at least 1

    window_ratio = window_width / window_height
    page_ratio = pix.width / pix.height

    if window_ratio < page_ratio:
        # Window is relatively taller than the page, so scale based on width
        new_width = window_width
        new_height = max(int(window_width / page_ratio), 1)  # ensure height is at least 1
    else:
        # Window is relatively wider than the page, so scale based on height
        new_height = window_height
        new_width = max(int(window_height * page_ratio), 1)  # ensure width is at least 1

    return new_width, new_height

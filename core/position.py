def get_open_position_side(position_data):
    """
    Returns:
    - "long"
    - "short"
    - None (no position)
    """
    if not position_data:
        return None

    for pos in position_data:
        size = float(pos.get("total", 0))
        if size > 0:
            return pos.get("holdSide")  # long / short

    return None

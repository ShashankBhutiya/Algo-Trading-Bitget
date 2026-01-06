def calculate_position_size(
    balance,
    risk_pct,
    stop_loss_pct,
    price
):
    risk_amount = balance * risk_pct
    position_value = risk_amount / stop_loss_pct
    size = position_value / price
    return round(size, 4)

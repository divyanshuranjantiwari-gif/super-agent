def calculate_position_size(ml_confidence, super_score, regime):
    """
    Calculates the suggested position size (as a percentage of portfolio)
    using a simplified Kelly Criterion heuristic adjusted for market regime.
    
    Args:
        ml_confidence: float (0.0 to 1.0) representing the win probability
        super_score: float (-1.0 to 1.0)
        regime: str ('BULL', 'BEAR', 'HIGH_VOL', 'CHOPPY')
        
    Returns:
        float: Position size percentage (e.g., 5.0 for 5%)
    """
    # If ML confidence is missing, use super_score as a proxy for probability
    if ml_confidence is None:
        if super_score >= 0.5:
            win_prob = 0.55
        elif super_score > 0.15:
            win_prob = 0.45
        else:
            return 0.0
    else:
        win_prob = ml_confidence
        
    # Baseline Kelly Formula (Simplified): Edge / Odds
    # Assume average win is 3% and average loss is 1.5% (Reward:Risk = 2:1)
    # Kelly % = WinProb - (LossProb / (Reward/Risk))
    loss_prob = 1.0 - win_prob
    reward_risk_ratio = 2.0
    
    kelly_fraction = win_prob - (loss_prob / reward_risk_ratio)
    
    if kelly_fraction <= 0:
        return 0.0
        
    # Convert to percentage and apply a fractional Kelly (Half-Kelly) for safety
    base_allocation = (kelly_fraction * 100) / 2.0
    
    # Adjust for market regime
    if regime == 'BULL':
        multiplier = 1.0
    elif regime == 'CHOPPY':
        multiplier = 0.5   # Halve the size in choppy markets
    elif regime == 'BEAR' or regime == 'HIGH_VOL':
        multiplier = 0.25  # Quarter size in dangerous markets
    else:
        multiplier = 0.5
        
    final_allocation = base_allocation * multiplier
    
    # Cap maximum single trade allocation to 10%
    return min(max(round(final_allocation, 1), 0.0), 10.0)

if __name__ == "__main__":
    print(f"Test 1 (90% conf, BULL): {calculate_position_size(0.9, 0.8, 'BULL')}%")
    print(f"Test 2 (60% conf, BULL): {calculate_position_size(0.6, 0.6, 'BULL')}%")
    print(f"Test 3 (60% conf, BEAR): {calculate_position_size(0.6, 0.6, 'BEAR')}%")
    print(f"Test 4 (40% conf, BULL): {calculate_position_size(0.4, 0.4, 'BULL')}%")

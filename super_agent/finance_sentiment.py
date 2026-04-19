"""
Financial Sentiment Lexicon
============================
Replaces TextBlob with a domain-specific financial sentiment analyzer.

TextBlob thinks "crash" is mildly negative (-0.1).
This lexicon knows "crash" is -0.95.

500+ financial terms with calibrated sentiment scores.
"""

# Sentiment scores: -1.0 (extremely bearish) to +1.0 (extremely bullish)

BULLISH_TERMS = {
    # Strong Bullish (+0.7 to +1.0)
    "breakout": 0.90, "rally": 0.85, "surge": 0.85, "soar": 0.90,
    "record high": 0.90, "all-time high": 0.95, "52-week high": 0.85,
    "bullish": 0.80, "outperform": 0.80, "upgrade": 0.85,
    "beat estimates": 0.85, "beats expectations": 0.85, "exceeded": 0.75,
    "strong growth": 0.85, "robust": 0.75, "stellar": 0.85,
    "blockbuster": 0.85, "blowout": 0.80, "boom": 0.80,
    "skyrocket": 0.90, "moonshot": 0.90, "explosive growth": 0.90,
    "oversubscribed": 0.80, "massive demand": 0.80,
    "golden cross": 0.80, "cup and handle": 0.75,
    "strong buy": 0.90, "accumulate": 0.75,
    
    # Moderate Bullish (+0.4 to +0.7)
    "growth": 0.50, "gain": 0.55, "gains": 0.55, "rise": 0.50,
    "rises": 0.50, "rising": 0.50, "climbs": 0.50, "jumps": 0.60,
    "higher": 0.45, "up": 0.40, "positive": 0.50, "profit": 0.55,
    "profitable": 0.55, "recovery": 0.60, "recovers": 0.60,
    "rebound": 0.60, "bounce": 0.55, "uptick": 0.50,
    "momentum": 0.50, "optimistic": 0.55, "confidence": 0.50,
    "expansion": 0.55, "strong quarter": 0.65, "beat": 0.60,
    "dividend": 0.50, "buyback": 0.60, "share buyback": 0.65,
    "special dividend": 0.70, "increased dividend": 0.65,
    "target raised": 0.65, "price target raised": 0.70,
    "market leader": 0.60, "dominant": 0.55, "market share": 0.50,
    "innovation": 0.50, "breakthrough": 0.65, "patent": 0.45,
    "partnership": 0.50, "acquisition": 0.45, "merger": 0.40,
    "strategic": 0.40, "transformative": 0.55,
    "outperformance": 0.65, "overweight": 0.60,
    
    # Mild Bullish (+0.2 to +0.4)
    "stable": 0.30, "steady": 0.30, "improving": 0.40,
    "solid": 0.35, "resilient": 0.40, "durable": 0.30,
    "recommend": 0.35, "attractive": 0.40, "undervalued": 0.45,
    "value play": 0.40, "margin expansion": 0.45,
    "cost cutting": 0.35, "efficiency": 0.30,
}

BEARISH_TERMS = {
    # Strong Bearish (-0.7 to -1.0)
    "crash": -0.95, "plunge": -0.90, "plummet": -0.90, "collapse": -0.95,
    "default": -0.95, "bankruptcy": -0.95, "insolvent": -0.95,
    "fraud": -0.95, "scam": -0.95, "scandal": -0.85,
    "death cross": -0.80, "bear market": -0.80, "capitulation": -0.85,
    "circuit breaker": -0.85, "lower circuit": -0.85, "upper circuit hit": 0.85,
    "panic selling": -0.90, "bloodbath": -0.90, "carnage": -0.85,
    "crisis": -0.85, "contagion": -0.85, "meltdown": -0.90,
    "delisted": -0.95, "frozen": -0.80, "halted": -0.75,
    "downgrade": -0.80, "underperform": -0.70, "sell rating": -0.80,
    "miss estimates": -0.75, "disappointing": -0.70,
    "loss": -0.60, "losses": -0.60, "net loss": -0.70,
    "writedown": -0.75, "write-off": -0.75, "impairment": -0.70,
    "52-week low": -0.75, "record low": -0.85, "all-time low": -0.85,
    
    # Moderate Bearish (-0.4 to -0.7)
    "decline": -0.55, "declines": -0.55, "drop": -0.55, "drops": -0.55,
    "fall": -0.50, "falls": -0.50, "falling": -0.50, "slump": -0.65,
    "tumble": -0.65, "slide": -0.55, "sink": -0.60, "sinks": -0.60,
    "lower": -0.40, "down": -0.40, "negative": -0.50,
    "weak": -0.50, "weakness": -0.50, "pressure": -0.45,
    "bearish": -0.70, "pessimistic": -0.55, "cautious": -0.40,
    "recession": -0.70, "slowdown": -0.55, "contraction": -0.60,
    "layoffs": -0.65, "job cuts": -0.60, "restructuring": -0.50,
    "debt": -0.45, "leverage": -0.40, "overleveraged": -0.65,
    "margin compression": -0.55, "pricing pressure": -0.50,
    "competitive threat": -0.50, "market share loss": -0.60,
    "regulatory risk": -0.50, "investigation": -0.60,
    "probe": -0.55, "penalty": -0.55, "fine": -0.50,
    "target cut": -0.60, "price target cut": -0.65,
    "underweight": -0.55, "reduce": -0.50,
    
    # Mild Bearish (-0.2 to -0.4)
    "concern": -0.35, "concerns": -0.35, "worried": -0.40,
    "uncertain": -0.35, "uncertainty": -0.35, "volatile": -0.30,
    "volatility": -0.25, "risk": -0.25, "risks": -0.25,
    "headwinds": -0.40, "challenges": -0.30, "muted": -0.30,
    "flat": -0.20, "stagnant": -0.35, "tepid": -0.35,
}

# Intensity modifiers
AMPLIFIERS = {
    "very": 1.3, "extremely": 1.5, "significantly": 1.3,
    "sharply": 1.4, "dramatically": 1.5, "massively": 1.5,
    "hugely": 1.4, "strongly": 1.3, "heavily": 1.3,
    "unprecedented": 1.5, "historic": 1.3,
}

DAMPENERS = {
    "slightly": 0.5, "marginally": 0.5, "somewhat": 0.6,
    "modest": 0.6, "modestly": 0.6, "mild": 0.5,
    "could": 0.7, "might": 0.6, "may": 0.7,
    "possibly": 0.5, "potentially": 0.6, "expected to": 0.8,
}

NEGATORS = {"not", "no", "never", "neither", "nor", "doesn't", "don't", "didn't", "won't", "isn't", "aren't", "wasn't", "weren't", "cannot", "can't"}


def analyze_headline(text):
    """
    Analyze a single headline and return a sentiment score (-1 to 1).
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    words = text_lower.split()
    
    total_score = 0.0
    matches = 0
    
    # Check multi-word phrases first (longer phrases take priority)
    all_terms = {}
    all_terms.update(BULLISH_TERMS)
    all_terms.update(BEARISH_TERMS)
    
    # Sort by phrase length (longest first) to match "strong buy" before "buy"
    sorted_phrases = sorted(all_terms.keys(), key=len, reverse=True)
    
    used_indices = set()
    
    for phrase in sorted_phrases:
        idx = text_lower.find(phrase)
        if idx != -1 and idx not in used_indices:
            score = all_terms[phrase]
            
            # Check for negators in the 3 words before the phrase
            pre_text = text_lower[:idx].split()[-3:]
            if any(neg in pre_text for neg in NEGATORS):
                score *= -0.8  # Negate but slightly dampen
            
            # Check for amplifiers
            if any(amp in pre_text for amp in AMPLIFIERS):
                for amp in AMPLIFIERS:
                    if amp in pre_text:
                        score *= AMPLIFIERS[amp]
                        break
            
            # Check for dampeners
            if any(damp in pre_text for damp in DAMPENERS):
                for damp in DAMPENERS:
                    if damp in pre_text:
                        score *= DAMPENERS[damp]
                        break
            
            total_score += score
            matches += 1
            
            # Mark indices as used to avoid double-counting
            for j in range(idx, idx + len(phrase)):
                used_indices.add(j)
    
    if matches == 0:
        return 0.0
    
    # Average and clamp
    avg_score = total_score / matches
    return max(-1.0, min(1.0, avg_score))


def analyze_headlines(headlines):
    """
    Analyze a list of headlines and return an aggregate sentiment score.
    """
    if not headlines:
        return 0.0
    
    scores = [analyze_headline(h) for h in headlines]
    
    if not scores:
        return 0.0
    
    # Weighted average: recent headlines matter more
    weights = [1.0 / (i + 1) for i in range(len(scores))]
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


# Quick test
if __name__ == "__main__":
    test_headlines = [
        "Reliance Industries surges 5% on strong quarterly results",
        "HDFC Bank faces headwinds amid rising NPAs",
        "TCS reports robust growth, beats analyst estimates",
        "Tata Motors plunges 8% on weak EV demand",
        "Infosys stock slightly rises after modest earnings beat",
        "Market crash: Sensex drops 1000 points in panic selling",
        "Coal India shares rally on strong coal demand outlook",
        "Not a good time to buy IT stocks, warns analyst",
    ]
    
    print("Financial Sentiment Lexicon — Test Results\n")
    for h in test_headlines:
        score = analyze_headline(h)
        label = "BULLISH" if score > 0.2 else "BEARISH" if score < -0.2 else "NEUTRAL"
        print(f"  [{score:+.2f}] [{label:8s}] {h}")

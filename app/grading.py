def get_performance_level(score: float) -> str:
    """Convert percentage score to Lakeview / CBC performance level."""
    if score is None:
        return ""
    score = float(score)
    if score >= 90:
        return "EE1"
    elif score >= 75:
        return "EE2"
    elif score >= 65:
        return "ME1"
    elif score >= 50:
        return "ME2"
    elif score >= 35:
        return "AE1"
    elif score >= 20:
        return "AE2"
    elif score >= 10:
        return "BE1"
    else:
        return "BE2"


def get_level_description(level: str) -> str:
    descriptions = {
        "EE1": "Exceeding Expectations 1 (90-100%)",
        "EE2": "Exceeding Expectations 2 (75-89%)",
        "ME1": "Meeting Expectations 1 (65-74%)",
        "ME2": "Meeting Expectations 2 (50-64%)",
        "AE1": "Approaching Expectations 1 (35-49%)",
        "AE2": "Approaching Expectations 2 (20-34%)",
        "BE1": "Below Expectations 1 (10-19%)",
        "BE2": "Below Expectations 2 (0-9%)",
    }
    return descriptions.get(level, level)


LEVEL_POINTS = {
    "EE1": 8,
    "EE2": 7,
    "ME1": 6,
    "ME2": 5,
    "AE1": 4,
    "AE2": 3,
    "BE1": 2,
    "BE2": 1,
}

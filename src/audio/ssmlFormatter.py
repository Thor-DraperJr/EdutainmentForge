def add_emphasis(text: str, level: str = "moderate") -> str:
    """Wrap text with emphasis SSML tag."""
    return f"<emphasis level='{level}'>{text}</emphasis>"

def add_pause(duration_ms: int) -> str:
    """Insert a pause of specified duration."""
    return f"<break time='{duration_ms}ms'/>"

def adjust_prosody(text: str, rate: str = "medium", pitch: str = "medium") -> str:
    """Adjust prosody of text."""
    return f"<prosody rate='{rate}' pitch='{pitch}'>{text}</prosody>"
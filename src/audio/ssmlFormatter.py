def add_emphasis(text: str, level: str = "moderate") -> str:
    """Wrap text with emphasis SSML tag."""
    return f"<emphasis level='{level}'>{text}</emphasis>"

def add_pause(duration_ms: int) -> str:
    """Insert a pause of specified duration."""
    return f"<break time='{duration_ms}ms'/>"

def adjust_prosody(text: str, rate: str = "medium", pitch: str = "medium") -> str:
    """Adjust prosody of text."""
    return f"<prosody rate='{rate}' pitch='{pitch}'>{text}</prosody>"

# Example usage in existing formatter function:
def format_ssml(text: str) -> str:
    # ...existing code...
    ssml_text = add_emphasis(ssml_text, "strong")
    ssml_text += add_pause(500)
    ssml_text = adjust_prosody(ssml_text, rate="slow", pitch="medium")
    # ...existing code...
    return ssml_text
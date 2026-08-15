"""
Deterministic Voice Command Parser
Maps natural-language transcripts to structured video control intents.
"""
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Standard Intent Constants
class CommandIntent:
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TOGGLE_PLAYBACK = "TOGGLE_PLAYBACK"
    REWIND = "REWIND"
    FORWARD = "FORWARD"
    SEEK_TO = "SEEK_TO"
    RESTART = "RESTART"
    NEXT = "NEXT"
    PREVIOUS = "PREVIOUS"
    MUTE = "MUTE"
    UNMUTE = "UNMUTE"
    VOLUME_UP = "VOLUME_UP"
    VOLUME_DOWN = "VOLUME_DOWN"
    SPEED_UP = "SPEED_UP"
    SPEED_DOWN = "SPEED_DOWN"
    SET_SPEED = "SET_SPEED"
    FULLSCREEN = "FULLSCREEN"
    EXIT_FULLSCREEN = "EXIT_FULLSCREEN"
    UNKNOWN = "UNKNOWN"

# Word-to-number mapping dictionary
NUMBER_WORDS = {
    "zero": 0, "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "half": 0.5,
}

def extract_time_seconds(text: str, default: int = 10) -> int:
    """
    Extracts time duration in seconds from phrases like:
    - '20 seconds', '20s', 'twenty seconds'
    - '1 minute', '2 minutes', 'a minute', 'half a minute'
    """
    # 1. Check for minutes (e.g. '2 minutes', 'a minute', 'half a minute')
    min_match = re.search(r"(\d+(?:\.\d+)?|\b(?:one|two|three|four|five|ten|a|an|half)\b)\s*(?:min|minute|minutes)", text)
    if min_match:
        val_str = min_match.group(1).lower()
        if val_str in NUMBER_WORDS:
            return int(NUMBER_WORDS[val_str] * 60)
        try:
            return int(float(val_str) * 60)
        except ValueError:
            return 60

    # 2. Check for numeric digits + seconds (e.g. '20 seconds', '20s', '20 sec')
    sec_match = re.search(r"(\d+)\s*(?:s|sec|secs|second|seconds)?", text)
    if sec_match:
        val = int(sec_match.group(1))
        if val > 0:
            return val

    # 3. Check for number words + seconds (e.g. 'twenty seconds', 'ten secs', 'thirty seconds')
    for word, num in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\s*(?:s|sec|secs|second|seconds)\b", text):
            return int(num)

    # 4. Check for compound words (e.g., 'twenty five seconds')
    compound_match = re.search(r"\b(twenty|thirty|forty|fifty)\s+(one|two|three|four|five|six|seven|eight|nine)\s*(?:s|sec|secs|second|seconds)?\b", text)
    if compound_match:
        tens = NUMBER_WORDS.get(compound_match.group(1), 0)
        ones = NUMBER_WORDS.get(compound_match.group(2), 0)
        return tens + ones

    return default

def extract_speed_value(text: str) -> Optional[float]:
    """
    Extracts playback rate multiplier (e.g., '1.5x', '1.25', '2x', 'normal', 'double', 'half').
    """
    if "normal" in text or "regular" in text or "1x" in text:
        return 1.0
    if "double" in text or "2x" in text:
        return 2.0
    if "half" in text or "0.5x" in text:
        return 0.5

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|times|speed)?", text)
    if match:
        try:
            val = float(match.group(1))
            if 0.25 <= val <= 2.0:
                return val
        except ValueError:
            pass
    return None

def parse_command(raw_text: str) -> Dict[str, Any]:
    """
    Parses natural language speech text into a structured action dictionary.
    Returns: {"intent": <CommandIntent>, "value": <Optional value>, "raw": <text>}
    """
    text = raw_text.lower().strip()
    # Strip optional wake word prefix if STT included it
    text = re.sub(r"^(?:hey\s+)?(?:youtube|u\s*tube)[,\s]*", "", text).strip()

    if not text:
        return {"intent": CommandIntent.UNKNOWN, "raw": raw_text}

    # 1. PLAY / RESUME
    if re.search(r"\b(?:play|resume|continue|start\s+playing|unpause)\b", text) and not re.search(r"\breplay\b", text):
        return {"intent": CommandIntent.PLAY, "raw": raw_text}

    # 2. PAUSE / STOP
    if re.search(r"\b(?:pause|stop|freeze|hold\s+on|wait)\b", text):
        return {"intent": CommandIntent.PAUSE, "raw": raw_text}

    # 3. REWIND / GO BACK / JUMP BACK
    if re.search(r"\b(?:go\s+back|rewind|back|jump\s+back|take\s+me\s+back|skip\s+back|replay\s+the\s+last)\b", text):
        seconds = extract_time_seconds(text, default=10)
        return {"intent": CommandIntent.REWIND, "value": seconds, "raw": raw_text}

    # 4. FORWARD / SKIP AHEAD / FAST FORWARD
    if re.search(r"\b(?:forward|go\s+forward|skip\s+ahead|skip|jump\s+ahead|fast\s+forward|ahead)\b", text) and not re.search(r"\bskip\s+video\b", text):
        seconds = extract_time_seconds(text, default=10)
        return {"intent": CommandIntent.FORWARD, "value": seconds, "raw": raw_text}

    # 5. RESTART / REPLAY THAT / START OVER
    if re.search(r"\b(?:restart|start\s+over|from\s+the\s+beginning|replay\s+that|replay|play\s+again)\b", text):
        return {"intent": CommandIntent.RESTART, "raw": raw_text}

    # 6. SPEED UP
    if re.search(r"\b(?:speed\s+up|faster|make\s+it\s+faster|increase\s+speed|quicker)\b", text):
        return {"intent": CommandIntent.SPEED_UP, "value": 0.25, "raw": raw_text}

    # 7. SPEED DOWN / SLOW DOWN
    if re.search(r"\b(?:slow\s+down|slower|make\s+it\s+slower|decrease\s+speed|speed\s+down)\b", text):
        return {"intent": CommandIntent.SPEED_DOWN, "value": 0.25, "raw": raw_text}

    # 8. SET SPEED (explicit rate e.g. "set speed to 1.5")
    if re.search(r"\b(?:set\s+speed|playback\s+rate|speed\s+to)\b", text):
        rate = extract_speed_value(text)
        if rate is not None:
            return {"intent": CommandIntent.SET_SPEED, "value": rate, "raw": raw_text}

    # 9. MUTE / SILENCE
    if re.search(r"\b(?:mute|silence|be\s+quiet|shut\s+up|turn\s+off\s+sound)\b", text):
        return {"intent": CommandIntent.MUTE, "raw": raw_text}

    # 10. UNMUTE / SOUND ON
    if re.search(r"\b(?:unmute|sound\s+on|turn\s+on\s+sound|turn\s+sound\s+back\s+on)\b", text):
        return {"intent": CommandIntent.UNMUTE, "raw": raw_text}

    # 11. VOLUME UP / LOUDER
    if re.search(r"\b(?:volume\s+up|louder|turn\s+it\s+up|increase\s+volume|turn\s+up)\b", text):
        return {"intent": CommandIntent.VOLUME_UP, "value": 0.1, "raw": raw_text}

    # 12. VOLUME DOWN / QUIETER
    if re.search(r"\b(?:volume\s+down|quieter|lower\s+volume|turn\s+it\s+down|decrease\s+volume|turn\s+down)\b", text):
        return {"intent": CommandIntent.VOLUME_DOWN, "value": 0.1, "raw": raw_text}

    # 13. FULLSCREEN (ENTER)
    if re.search(r"\b(?:full\s*screen|make\s+it\s+full\s*screen|enter\s+full\s*screen|maximize)\b", text) and not re.search(r"\b(?:exit|leave|close)\b", text):
        return {"intent": CommandIntent.FULLSCREEN, "raw": raw_text}

    # 14. FULLSCREEN (EXIT)
    if re.search(r"\b(?:exit\s+full\s*screen|leave\s+full\s*screen|minimize|normal\s*screen)\b", text):
        return {"intent": CommandIntent.EXIT_FULLSCREEN, "raw": raw_text}

    # 15. NEXT VIDEO
    if re.search(r"\b(?:next\s+video|next\s+track|next|skip\s+video)\b", text):
        return {"intent": CommandIntent.NEXT, "raw": raw_text}

    # 16. PREVIOUS VIDEO
    if re.search(r"\b(?:previous\s+video|previous|go\s+back\s+a\s+video|last\s+video)\b", text):
        return {"intent": CommandIntent.PREVIOUS, "raw": raw_text}

    return {"intent": CommandIntent.UNKNOWN, "raw": raw_text}

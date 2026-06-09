from typing import TypedDict, List, Dict, Any, Union


# ============================================================
# EVENT TYPES (SAFE CONSTANTS)
# ============================================================
class EventType:
    STATE_PATCH = "state_patch"
    NARRATION = "narration"
    CHOICES = "choices"
    JOURNAL = "journal"
    END = "end_state"


# ============================================================
# STATE PATCH EVENT
# ============================================================
class StatePatchEvent(TypedDict):
    type: str
    payload: Dict[str, Any]


# ============================================================
# NARRATION EVENT
# ============================================================
class NarrationEvent(TypedDict):
    type: str
    payload: Dict[str, str]


# ============================================================
# CHOICES EVENT
# ============================================================
class ChoiceItem(TypedDict):
    type: str
    text: str
    consequence: str
    deltaHealth: int
    deltaAcclim: int
    deltaEnergy: int
    deltaTrust: int
    deltaStorm: int


class ChoicesEvent(TypedDict):
    type: str
    payload: List[ChoiceItem]


# ============================================================
# JOURNAL EVENT
# ============================================================
class JournalEvent(TypedDict):
    type: str
    payload: Dict[str, str]


# ============================================================
# END EVENT
# ============================================================
class EndEvent(TypedDict):
    type: str
    payload: Dict[str, str]


# ============================================================
# UNION TYPE (OPTIONAL BUT POWERFUL)
# ============================================================
GameEvent = Union[
    StatePatchEvent,
    NarrationEvent,
    ChoicesEvent,
    JournalEvent,
    EndEvent,
]
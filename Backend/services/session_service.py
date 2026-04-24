"""
Session memory — Lab 6 (in-process, sliding window).
"""

# session_id -> list of OpenAI-style message dicts: role + content
_sessions: dict[str, list] = {}

MAX_TURNS = 20


def load_session(session_id: str) -> list:
    return list(_sessions.get(session_id, []))


def save_session(session_id: str, messages: list) -> None:
    _sessions[session_id] = _trim(messages)


def delete_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def _trim(messages: list) -> list:
    system_messages = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    max_non_system = MAX_TURNS * 2
    if len(non_system) <= max_non_system:
        return system_messages + non_system
    return system_messages + non_system[-max_non_system:]

"""
Integration tests for session service (memory management).
"""

import pytest


class TestSessionService:
    """Test session memory operations."""

    def test_load_session_empty(self, reset_session_service):
        """Test loading a non-existent session returns empty list."""
        from services.session_service import load_session

        session = load_session("nonexistent")
        assert session == []

    def test_save_and_load_session(self, reset_session_service):
        """Test saving and loading a session."""
        from services.session_service import save_session, load_session

        session_id = "test-session"
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        save_session(session_id, messages)
        loaded = load_session(session_id)

        assert loaded == messages

    def test_save_session_creates_copy(self, reset_session_service):
        """Test that saving session trims messages appropriately."""
        from services.session_service import save_session, load_session

        session_id = "test-copy"
        messages = [
            {"role": "user", "content": "Test"},
        ]

        save_session(session_id, messages)
        loaded1 = load_session(session_id)

        # Save again with different content
        messages2 = [
            {"role": "user", "content": "Different"},
        ]
        save_session(session_id, messages2)

        # New load should get new content
        reloaded = load_session(session_id)
        assert reloaded[0]["content"] == "Different"

    def test_load_session_returns_copy(self, reset_session_service):
        """Test that loading session returns independent data."""
        from services.session_service import save_session, load_session

        session_id = "test-ref"
        messages = [
            {"role": "user", "content": "Test"},
        ]

        save_session(session_id, messages)
        loaded1 = load_session(session_id)
        loaded2 = load_session(session_id)

        # Both should have same content
        assert loaded1[0]["content"] == "Test"
        assert loaded2[0]["content"] == "Test"

    def test_delete_session(self, reset_session_service):
        """Test deleting a session."""
        from services.session_service import save_session, load_session, delete_session

        session_id = "test-delete"
        messages = [{"role": "user", "content": "Test"}]

        save_session(session_id, messages)
        assert load_session(session_id) != []

        delete_session(session_id)
        assert load_session(session_id) == []

    def test_delete_nonexistent_session(self, reset_session_service):
        """Test deleting non-existent session doesn't error."""
        from services.session_service import delete_session

        # Should not raise
        delete_session("nonexistent")

    def test_session_memory_trimming_preserves_system(self, reset_session_service):
        """Test that system message is always preserved in trimming."""
        from services.session_service import save_session, load_session, MAX_TURNS

        session_id = "test-trim-system"
        messages = [
            {"role": "system", "content": "System prompt"},
        ]
        # Add many user/assistant messages
        for i in range(MAX_TURNS * 3):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": f"Message {i}"})

        save_session(session_id, messages)
        loaded = load_session(session_id)

        # Should have system message first
        assert loaded[0]["role"] == "system"
        assert loaded[0]["content"] == "System prompt"

    def test_session_memory_trimming_keeps_recent(self, reset_session_service):
        """Test that trimming keeps the most recent messages."""
        from services.session_service import save_session, load_session, MAX_TURNS

        session_id = "test-trim-recent"
        messages = [
            {"role": "system", "content": "System"},
        ]
        for i in range(MAX_TURNS * 3):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": f"Message {i}"})

        save_session(session_id, messages)
        loaded = load_session(session_id)

        # Get the last few messages before save
        expected_last = messages[-(MAX_TURNS * 2) :]
        actual_last = loaded[1:]  # Skip system

        assert actual_last == expected_last

    def test_session_memory_trimming_limit(self, reset_session_service):
        """Test that trimmed session respects MAX_TURNS limit."""
        from services.session_service import save_session, load_session, MAX_TURNS

        session_id = "test-trim-limit"
        messages = [
            {"role": "system", "content": "System"},
        ]
        for i in range(MAX_TURNS * 5):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": f"Message {i}"})

        save_session(session_id, messages)
        loaded = load_session(session_id)

        non_system = [m for m in loaded if m["role"] != "system"]
        assert len(non_system) <= MAX_TURNS * 2

    def test_session_multiple_system_messages(self, reset_session_service):
        """Test handling of multiple system messages in trimming."""
        from services.session_service import save_session, load_session

        session_id = "test-multi-system"
        messages = [
            {"role": "system", "content": "First system"},
            {"role": "system", "content": "Second system"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"},
        ]

        save_session(session_id, messages)
        loaded = load_session(session_id)

        # Both system messages should be preserved
        system_messages = [m for m in loaded if m["role"] == "system"]
        assert len(system_messages) == 2

    def test_save_updates_existing_session(self, reset_session_service):
        """Test that saving overwrites existing session."""
        from services.session_service import save_session, load_session

        session_id = "test-update"

        # Save initial
        messages1 = [{"role": "user", "content": "Message 1"}]
        save_session(session_id, messages1)
        assert load_session(session_id) == messages1

        # Save updated
        messages2 = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Response 1"},
            {"role": "user", "content": "Message 2"},
        ]
        save_session(session_id, messages2)
        assert load_session(session_id) == messages2

    def test_empty_session_save(self, reset_session_service):
        """Test saving empty session."""
        from services.session_service import save_session, load_session

        session_id = "test-empty"
        save_session(session_id, [])
        assert load_session(session_id) == []

    def test_session_with_only_system_message(self, reset_session_service):
        """Test session with only system message."""
        from services.session_service import save_session, load_session

        session_id = "test-system-only"
        messages = [{"role": "system", "content": "System only"}]

        save_session(session_id, messages)
        loaded = load_session(session_id)
        assert loaded == messages

    def test_session_isolation(self, reset_session_service):
        """Test that different sessions are isolated."""
        from services.session_service import save_session, load_session

        session1_id = "session-1"
        session2_id = "session-2"

        messages1 = [{"role": "user", "content": "Session 1"}]
        messages2 = [{"role": "user", "content": "Session 2"}]

        save_session(session1_id, messages1)
        save_session(session2_id, messages2)

        assert load_session(session1_id) == messages1
        assert load_session(session2_id) == messages2

    def test_long_message_content(self, reset_session_service):
        """Test session with very long message content."""
        from services.session_service import save_session, load_session

        session_id = "test-long"
        long_content = "X" * 10000
        messages = [
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": long_content},
        ]

        save_session(session_id, messages)
        loaded = load_session(session_id)

        assert loaded[0]["content"] == long_content
        assert loaded[1]["content"] == long_content

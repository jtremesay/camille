import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = [pytest.mark.django_db(transaction=True)]

from camille.mattermost import Mattermost


@pytest.fixture
def mattermost():
    """Create a Mattermost instance with mocked HTTP client."""
    mm = Mattermost.__new__(Mattermost)
    mm.client_http = AsyncMock()
    mm.client_ws = AsyncMock()
    mm.me_mm_id = "bot_mm_id"
    mm.me_name = "Camille"
    mm.current_seq = 0
    mm.agent = MagicMock()
    return mm


class TestHandleEvent:
    async def test_dispatches_to_handler(self, mattermost):
        mattermost.on_test_event = AsyncMock()
        await mattermost.handle_event("test_event", {"key": "value"})
        mattermost.on_test_event.assert_called_once_with({"key": "value"})

    async def test_ignores_unknown_event(self, mattermost):
        # Should not raise
        await mattermost.handle_event("nonexistent_event", {})


class TestHandleCommands:
    async def test_non_dm_ignored(self, mattermost):
        result = await mattermost.handle_commands(
            "O", "!/help", None, "chan", "root", "sender"
        )
        assert result is False

    async def test_non_command_ignored(self, mattermost):
        result = await mattermost.handle_commands(
            "D", "hello", None, "chan", "root", "sender"
        )
        assert result is False

    async def test_help_command(self, mattermost):
        mattermost.send_message = AsyncMock()
        result = await mattermost.handle_commands(
            "D", "!/help", None, "chan", "root", "sender"
        )
        assert result is True
        mattermost.send_message.assert_called_once()
        msg = mattermost.send_message.call_args[0][1]
        assert "Available commands" in msg

    async def test_link_command_unlinked_user(self, mattermost):
        mattermost.send_message = AsyncMock()
        with patch("camille.mattermost.settings") as mock_settings:
            mock_settings.MAIN_HOST = "example.com"
            result = await mattermost.handle_commands(
                "D", "!/link", None, "chan", "root", "sender_mm"
            )
        assert result is True
        msg = mattermost.send_message.call_args[0][1]
        assert "link" in msg.lower()

    async def test_link_command_already_linked(self, mattermost, user):
        mattermost.send_message = AsyncMock()
        result = await mattermost.handle_commands(
            "D", "!/link", user, "chan", "root", "sender_mm"
        )
        assert result is True
        msg = mattermost.send_message.call_args[0][1]
        assert "already linked" in msg.lower()

    async def test_reset_password_no_user(self, mattermost):
        mattermost.send_message = AsyncMock()
        result = await mattermost.handle_commands(
            "D", "!/reset_password", None, "chan", "root", "sender_mm"
        )
        assert result is True
        msg = mattermost.send_message.call_args[0][1]
        assert "not linked" in msg.lower()

    async def test_reset_password_with_user(self, mattermost, user):
        mattermost.send_message = AsyncMock()
        with patch("camille.mattermost.settings") as mock_settings:
            mock_settings.MAIN_HOST = "example.com"
            result = await mattermost.handle_commands(
                "D", "!/reset_password", user, "chan", "root", "sender_mm"
            )
        assert result is True
        msg = mattermost.send_message.call_args[0][1]
        assert "reset" in msg.lower()

    async def test_unknown_command(self, mattermost):
        mattermost.send_message = AsyncMock()
        result = await mattermost.handle_commands(
            "D", "!/foobar", None, "chan", "root", "sender_mm"
        )
        assert result is True
        msg = mattermost.send_message.call_args[0][1]
        assert "Unknown command" in msg


class TestWsSend:
    async def test_ws_send_increments_seq(self, mattermost):
        await mattermost.ws_send("user_typing", {"channel_id": "chan"})
        assert mattermost.current_seq == 1
        mattermost.client_ws.send_json.assert_called_once_with(
            {
                "action": "user_typing",
                "data": {"channel_id": "chan"},
                "seq": 1,
            }
        )

    async def test_ws_send_multiple(self, mattermost):
        await mattermost.ws_send("a", {})
        await mattermost.ws_send("b", {})
        assert mattermost.current_seq == 2


class TestOnPosted:
    async def test_ignores_unmentioned(self, mattermost):
        mattermost.send_message = AsyncMock()
        await mattermost.on_posted(
            {
                "mentions": "[]",
                "sender_name": "@user",
                "post": '{"user_id":"other","channel_id":"c","root_id":"","id":"p","message":"hi","create_at":0}',
                "channel_type": "O",
                "channel_display_name": "General",
            }
        )
        mattermost.send_message.assert_not_called()

    async def test_ignores_system_messages(self, mattermost):
        mattermost.send_message = AsyncMock()
        await mattermost.on_posted(
            {
                "mentions": f'["{mattermost.me_mm_id}"]',
                "sender_name": "System",
                "post": '{"user_id":"sys","channel_id":"c","root_id":"","id":"p","message":"joined","create_at":0}',
                "channel_type": "O",
                "channel_display_name": "General",
            }
        )
        mattermost.send_message.assert_not_called()

    async def test_ignores_own_messages(self, mattermost):
        mattermost.send_message = AsyncMock()
        await mattermost.on_posted(
            {
                "mentions": f'["{mattermost.me_mm_id}"]',
                "sender_name": "@bot",
                "post": f'{{"user_id":"{mattermost.me_mm_id}","channel_id":"c","root_id":"","id":"p","message":"hi","create_at":0}}',
                "channel_type": "O",
                "channel_display_name": "General",
            }
        )
        mattermost.send_message.assert_not_called()

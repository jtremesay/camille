# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
from pathlib import Path
from typing import Optional

from aiofile import async_open
from aiohttp import ClientSession
from aiohttp.client import _WSRequestContextManager

logger = logging.getLogger(__name__)


class MattermostAPIClient:
    """Mattermost API client"""

    def __init__(self, host, api_token) -> None:
        """Initialize the API client

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        me = await api.get_user("me")
        await api.post_post("channel-id", f"Hello!, I'm {me['first_name']}")
        await api.close()

        Args:
            host (str): Mattermost host, e.g. https://mattermost.example.com
            api_token (str): API token
        """
        self.session = ClientSession(
            base_url=host,
            headers={"Authorization": "Bearer " + api_token},
        )

    async def close(self) -> None:
        """Close the API client

        Must be call before exiting the asyncio event loop
        """
        await self.session.close()

    def ws_connect(self, **kwargs) -> _WSRequestContextManager:
        """Connect to the Mattermost websocket API

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        async with api.ws_connect() as ws:
            async for message in ws:
                print(message)
        await api.close()

        Args:
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.ws_connect

        """
        return self.session.ws_connect("/api/v4/websocket", **kwargs)

    async def get(self, path: str, **kwargs) -> dict:
        """Perform a GET request to the Mattermost API

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        me = await api.get("users/me")
        print(me)
        await api.close()

        Args:
            path (str): API path, e.g. "users/me"
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.get

        Returns:
            dict: JSON response
        """
        logger.debug("GET %s", path)
        return await (await self.session.get("/api/v4/" + path, **kwargs)).json()

    async def post(self, path, **kwargs):
        """Perform a POST request to the Mattermost API

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        await api.post("posts", json=dict(channel_id="channel-id", message="Hello!"))
        await api.close()

        Args:
            path (str): API path, e.g. "posts"
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.post

        Returns:
            dict: JSON response
        """

        logger.debug("POST %s %s", path, kwargs.get("params"))
        return await (await self.session.post("/api/v4/" + path, **kwargs)).json()

    async def delete(self, path, **kwargs) -> dict:
        """Perform a DELETE request to the Mattermost API

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        await api.delete("posts/post-id")
        await api.close()

        Args:
            path (str): API path, e.g. "posts/post-id"
            **kwargs: Additional arguments to pass to aiohttp.ClientSession.delete

        Returns:
            dict: JSON response
        """
        logger.debug("DELETE %s", path)
        return await (await self.session.delete("/api/v4/" + path, **kwargs)).json()

    async def get_user(self, user_id: str) -> dict:
        """Get user information

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        me = await api.get_user("me")
        print(me)
        await api.close()

        Args:
            user_id (str): User ID

        Returns:
            dict: User information
        """
        return await self.get(f"users/{user_id}")

    async def get_user_channels(self, user_id: str, team_id: str) -> dict:
        """Get user channels

        Args:
            user_id (str): User ID
            team_id (str): Team ID

        Returns:
            dict: User channels
        """
        return await self.get(f"users/{user_id}/teams/{team_id}/channels")

    async def get_teams(self) -> list[dict]:
        """Get teams

        Returns:
            list[dict]: Teams
        """
        return await self.get("teams")

    async def get_channels(self, team_id: int) -> list[dict]:
        """Get channels

        Args:
            team_id (int): Team ID
        """
        return await self.get(f"teams/{team_id}/channels")

    async def get_post(self, post_id: str) -> dict:
        """Get post

        Args:
            post_id (str): Post ID

        Returns:
            dict: Post
        """
        return await self.get(f"posts/{post_id}")

    async def delete_post(self, post_id: str) -> dict:
        """Delete post

        Args:
            post_id (str): Post ID

        Returns:
            dict: Post
        """
        return await self.delete(f"posts/{post_id}")

    async def get_posts(
        self,
        channel_id: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        since: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        include_deleted: Optional[str] = None,
    ) -> dict:
        """Get posts

        Args:
            channel_id (str): Channel ID
            page (int): Page number
            per_page (int): Number of posts per page
            since (int): Since timestamp
            before (str): Before post ID
            after (str): After post ID
            include_deleted (str): Include deleted posts
        Returns:
            dict: Posts
        """
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if since is not None:
            params["since"] = since
        if before is not None:
            params["before"] = before
        if after is not None:
            params["after"] = after
        if include_deleted is not None:
            params["include_deleted"] = include_deleted

        return await self.get(f"channels/{channel_id}/posts", params=params)

    async def post_post(self, channel_id, message, **kwargs):
        """Post a message to a channel
        https://api.mattermost.com/#tag/posts/operation/CreatePost

        Args:
            channel_id (str): Channel ID
            message (str): Message
            **kwargs: Additional arguments to pass to the post

        Returns:
            dict: Post
        """
        return await self.post(
            f"posts", json=dict(channel_id=channel_id, message=message, **kwargs)
        )

    async def get_thread(
        self,
        post_id: str,
        direction: Optional[str] = None,
        per_page: Optional[int] = None,
        from_post: Optional[str] = None,
        from_create_at: Optional[int] = None,
        skip_fetch_threads: Optional[bool] = None,
        collapsed_threads: Optional[bool] = None,
        collapsed_threads_extended: Optional[bool] = None,
    ) -> dict:
        """Get thread

        Args:
            post_id (str): Post ID

        Returns:
            dict: Thread
        """
        params = {}
        if direction is not None:
            params["direction"] = direction
        if per_page is not None:
            params["perPage"] = per_page
        if from_post is not None:
            params["fromPost"] = from_post
        if from_create_at is not None:
            params["fromCreateAt"] = from_create_at
        if skip_fetch_threads is not None:
            params["skipFetchThreads"] = skip_fetch_threads
        if collapsed_threads is not None:
            params["collapsedThreads"] = collapsed_threads
        if collapsed_threads_extended is not None:
            params["collapsedThreadsExtended"] = collapsed_threads_extended

        return await self.get(f"posts/{post_id}/thread")

    async def upload_file(self, channel_id: str, file_path: str) -> dict:
        """Upload a file to a channel

        api = MattermostAPIClient("https://mattermost.example.com", "api-token")
        r = await api.upload_file("channel-id", "file.txt")
        await api.post_post("channel-id", "Here is the file", file_ids=[fi["id"] for fi in r["file_infos"]])
        await api.close()

        Args:
            channel_id (str): Channel ID
            file_path (str): File path

        Returns:
            dict: File info
        """
        async with async_open(file_path, "rb") as f:
            return await self.post(
                "files",
                params={
                    "channel_id": channel_id,
                    "filename": Path(file_path).name,
                },
                data=await f.read(),
            )

    async def get_channel_members(
        self,
        channel_id: str,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> dict:
        """Get channel members

        Args:
            channel_id (str): Channel ID
            page (int): Page number
            per_page (int): Number of members per page


        Returns:
            dict: Channel members
        """
        params = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page

        return await self.get(f"channels/{channel_id}/members", params=params)

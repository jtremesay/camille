import logging

from camille.models import (
    MattermostChannel,
    MattermostChannelMember,
    MattermostServer,
    MattermostTeam,
    MattermostUser,
)
from mattermost import Mattermost

logger = logging.getLogger(__name__)


async def sync_mm_server(server: MattermostServer, mm: Mattermost):
    """Sync Mattermost server data from the perspective of the authenticated bot user."""

    try:
        # Get current user
        me = await mm.get_me()
        logger.info(f"Syncing from user perspective: {me.username}")

        # Sync the current user
        user_obj, created = await MattermostUser.objects.aget_or_create(
            server=server,
            user_id=me.id,
            defaults={
                "username": me.username,
                "display_name": me.nickname or me.username,
                "first_name": me.first_name,
                "last_name": me.last_name,
            },
        )
        if not created:
            user_obj.username = me.username
            user_obj.display_name = me.nickname or me.username
            user_obj.first_name = me.first_name
            user_obj.last_name = me.last_name
            await user_obj.asave()

        logger.info(f"User synced: {me.username}")

        # Get teams for current user
        teams = await mm.get_teams(me.id)
        logger.info(f"Found {len(teams)} teams")

        for team in teams:
            try:
                # Sync team
                team_obj, created = await MattermostTeam.objects.aget_or_create(
                    server=server,
                    team_id=team.id,
                    defaults={
                        "name": team.name,
                        "display_name": team.display_name,
                    },
                )
                if not created:
                    team_obj.name = team.name
                    team_obj.display_name = team.display_name
                    await team_obj.asave()

                # Get channels for this team
                channels = await mm.get_channels_for_user(me.id, team.id)
                logger.info(f"Found {len(channels)} channels in team {team.name}")

                for channel in channels:
                    try:
                        # Sync channel
                        (
                            channel_obj,
                            created,
                        ) = await MattermostChannel.objects.aget_or_create(
                            team=team_obj,
                            channel_id=channel.id,
                            defaults={
                                "kind": channel.type,
                                "name": channel.name,
                                "display_name": channel.display_name,
                                "header": channel.header,
                                "purpose": channel.purpose,
                            },
                        )
                        if not created:
                            channel_obj.kind = channel.type
                            channel_obj.name = channel.name
                            channel_obj.display_name = channel.display_name
                            channel_obj.header = channel.header
                            channel_obj.purpose = channel.purpose
                            await channel_obj.asave()

                        # Get channel members
                        members = await mm.get_channel_members(channel.id)
                        logger.info(
                            f"Found {len(members)} members in channel {channel.name}"
                        )

                        for member in members:
                            try:
                                # Get user details
                                user = await mm.get_user(member.user_id)

                                # Sync user
                                (
                                    member_user_obj,
                                    created,
                                ) = await MattermostUser.objects.aget_or_create(
                                    server=server,
                                    user_id=user.id,
                                    defaults={
                                        "username": user.username,
                                        "display_name": user.nickname or user.username,
                                        "first_name": user.first_name,
                                        "last_name": user.last_name,
                                    },
                                )
                                if not created:
                                    member_user_obj.username = user.username
                                    member_user_obj.display_name = (
                                        user.nickname or user.username
                                    )
                                    member_user_obj.first_name = user.first_name
                                    member_user_obj.last_name = user.last_name
                                    await member_user_obj.asave()

                                # Sync channel member
                                await MattermostChannelMember.objects.aget_or_create(
                                    channel=channel_obj,
                                    user=member_user_obj,
                                )

                            except Exception as e:
                                logger.error(
                                    f"Error syncing member {member.user_id} in channel {channel.name}: {e}"
                                )
                                continue

                    except Exception as e:
                        logger.error(
                            f"Error syncing channel {channel.name} in team {team.name}: {e}"
                        )
                        continue

            except Exception as e:
                logger.error(f"Error syncing team {team.name}: {e}")
                continue

        logger.info("Mattermost server sync completed")

    except Exception as e:
        logger.error(f"Error syncing Mattermost server: {e}")
        raise

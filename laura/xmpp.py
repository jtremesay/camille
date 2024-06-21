import json

from slixmpp import ClientXMPP

from laura import settings as laura_settings
from laura.agent import Agent, Messages, SystemMessage
from laura.models import XMPPChannel, XMPPMessage


async def aget_llm_messages_for_channel(channel: XMPPChannel) -> Messages:
    llm_messages = Messages()
    llm_messages |= SystemMessage.default()

    # Build the history of messages
    xmpp_llm_messages = Messages()
    async for xmpp_message in channel.xmppmessage_set.order_by("-timestamp")[
        : laura_settings.LLM_MESSAGES_COUNT
    ]:
        xmpp_llm_messages |= xmpp_message.as_message()
    llm_messages |= reversed(xmpp_llm_messages)

    return llm_messages


class XMPPBot(ClientXMPP):
    def __init__(self):
        super().__init__(
            laura_settings.XMPP_JID,
            laura_settings.XMPP_PASSWORD,
        )
        self.joined_channels = set()
        self.agent = Agent()

        # Register plugins
        self.register_plugin("xep_0045")  # MUC
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0199")  # Ping

        # Register event handlers
        self.add_event_handler("session_start", self.on_session_start)
        self.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.add_event_handler("groupchat_subject", self.on_groupchat_subject)

    async def on_session_start(self, event):
        self.send_presence()
        await self.get_roster()

        # Join MUC channels
        for channel in laura_settings.XMPP_CHANNELS:
            await self.plugin["xep_0045"].join_muc(channel, laura_settings.NAME)

    async def on_groupchat_message(self, msg):
        # Ignore our own message
        sender = msg["from"].resource
        if sender == laura_settings.NAME:
            return

        channel = (await XMPPChannel.objects.aget_or_create(jid=msg["from"].bare))[0]
        message_body = msg["body"]

        # Is it a command?
        prefix = f"!{laura_settings.NAME} "
        if message_body.startswith(prefix):
            command, *args = message_body[len(prefix) :].split(" ", 1)
            if args:
                args = args[0]
            print(f"Command: {command} Args: {args}")

            if command == "help" or not command:
                self.send_chat_message(
                    channel,
                    "Available commands:\n"
                    + f"!{laura_settings.NAME} help: Display this help message\n"
                    + f"!{laura_settings.NAME} model: Display the current LLM model\n"
                    + f"!{laura_settings.NAME} set_model <model>: Set the LLM model\n"
                    + f"!{laura_settings.NAME} prompt: Display the current prompt\n"
                    + f"!{laura_settings.NAME} set_prompt <prompt>: Set the prompt\n"
                    + f"!{laura_settings.NAME} error: Display an error message\n",
                )
            elif command == "model":
                self.send_chat_message(
                    channel, f"Current LLM model: {channel.get_model()}"
                )
            elif command == "set_model":
                if not args:
                    channel.model = None
                    await channel.asave()
                    self.send_chat_message(
                        channel,
                        f"LLM model reset to default ({laura_settings.LLM_MODEL})",
                    )
                else:
                    channel.model = args
                    await channel.asave()
                    self.send_chat_message(channel, f"LLM model set to {channel.model}")
            elif command == "prompt":
                self.send_chat_message(
                    channel, f"Current prompt: {channel.get_prompt()}"
                )
            elif command == "set_prompt":
                if not args:
                    channel.prompt = None
                    await channel.asave()
                    self.send_chat_message(
                        channel,
                        f"Prompt reset to default:\n{laura_settings.LLM_PROMPT}",
                    )
                else:
                    channel.prompt = args
                    await channel.asave()
                    self.send_chat_message(channel, f"Prompt set to:\n{channel.prompt}")
            else:
                self.send_chat_message(
                    channel, f"ERRO CRÍTICO: não entendo sua solicitação: {command}"
                )

            # Ignore the message
            return

        # Save the message
        await XMPPMessage.objects.acreate(
            channel=channel,
            sender=sender,
            role="user",
            body=message_body,
        )

        # Don't react to messages that don't mention the bot in the beginning or end
        #  of the message, or the bot is not required to be mentioned
        if (
            laura_settings.NEED_MENTION
            and (
                laura_settings.NAME
                not in message_body[0 : len(laura_settings.NAME) + 20].lower()
            )
            and (
                laura_settings.NAME
                not in message_body[-len(laura_settings.NAME) - 20 :].lower()
            )
        ):
            return

        # Build the history of messages
        llm_messages = await aget_llm_messages_for_channel(channel)
        response = self.agent.process(channel.get_model(), llm_messages)
        if response is None:
            return

        xmpp_message = XMPPMessage.from_message(channel, laura_settings.NAME, response)
        await xmpp_message.asave()

        # Send the response
        self.send_chat_message(channel, response.content)

    def send_chat_message(self, channel: XMPPChannel, message: str):
        self.send_message(mto=channel, mbody=message, mtype="groupchat")

    async def on_groupchat_subject(self, msg):
        # The subject is sent when updated or joining a channel
        # Use the later to detect joining

        channel_jid = msg["from"]
        if channel_jid not in self.joined_channels:
            self.joined_channels.add(channel_jid)

            channel = (await XMPPChannel.objects.aget_or_create(jid=channel_jid))[0]

            if laura_settings.PRINT_BANNER:
                body = f"Language Analysis and Understanding Robot Assistant / model '{channel.get_model()}' / Ready to assist!"
                msg.reply(body).send()

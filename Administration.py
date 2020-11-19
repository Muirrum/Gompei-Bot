from GompeiFunctions import make_ordinal, time_delta_string, load_json, save_json, parse_id
from Permissions import moderator_perms, administrator_perms
from discord.ext import commands
from datetime import timedelta
from datetime import datetime


import pytimeparse
import dateparser
import asyncio
import discord
import Config
import typing
import os


class Administration(commands.Cog):
    """
    Administration tools
    """

    def __init__(self, bot):
        self.warns = load_json(os.path.join("config", "warns.json"))
        self.bot = bot

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def echo(self, ctx, channel: discord.TextChannel, *, msg):
        """
        Forwards message / attachments appended to the command to the given channel
        Usage: .echo <channel> <message>

        :param ctx: context object
        :param channel: channel to send the message to
        :param msg: message to send
        """
        # Check for attachments to forward
        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        if len(msg) > 0:
            message = await channel.send(msg, files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        elif len(attachments) > 0:
            message = await channel.send(files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        else:
            await ctx.send("No content to send.")

    @commands.command(pass_context=True, aliases=["echoEdit", "editEcho"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def echo_edit(self, ctx, bot_msg: discord.Message, *, msg):
        """
        Edits a message sent by the bot with the message given
        Usage: .echoEdit <messageLink> <message>

        :param ctx: context object
        :param bot_msg: link or id of the message to edit
        :param msg: message to edit to
        """
        # Check if Gompei is author of the message
        if bot_msg.author.id != self.bot.user.id:
            await ctx.send("Cannot edit a message that is not my own")
        else:
            await bot_msg.edit(content=msg)
            await ctx.send("Message edited (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(bot_msg.channel.id) + "/" + str(bot_msg.id) + ">)")

    @commands.command(pass_context=True, aliases=["echoPM", "pmEcho"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def echo_pm(self, ctx, user: typing.Union[discord.User, discord.Member], *, msg):
        """
        Forwards given message / attachments to give user
        Usage: .echoPM <user> <message>

        :param ctx: context object
        :param user: user to send message to
        :param msg: message to send
        """
        # Read attachments and message
        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        # Send message to user via DM
        if len(msg) > 0:
            message = await user.send(msg, files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/@me/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        elif len(attachments) > 0:
            message = await user.send(files=attachments)
            await ctx.send("Message sent (<https://discordapp.com/channels/@me/" + str(message.channel.id) + "/" + str(message.id) + ">)")
        else:
            await ctx.send("No content to send")

        await ctx.message.add_reaction("👍")

    @commands.guild_only()
    @commands.command(pass_context=True, aliases=["pmEdit", "editPM"])
    @commands.check(moderator_perms)
    async def pm_edit(self, ctx, user: typing.Union[discord.Member, discord.User], message_link, *, msg):
        """
        Edits a PM message sent to a user
        Usage: .pmEdit <user> <messageLink>

        :param ctx: context object
        :param user: user that the message was sent to
        :param message_link: link to the message
        :param msg: message to edit to
        """
        # Get message ID from message_link
        message_id = int(message_link[message_link.rfind("/") + 1:])

        channel = user.dm_channel
        if channel is None:
            channel = await user.create_dm()

        message = await channel.fetch_message(message_id)
        if message is None:
            await ctx.send("Not a valid link to message")
        else:
            if message.author.id != self.bot.user.id:
                await ctx.send("Cannot edit a message that is not my own")
            else:
                await message.edit(content=msg)
                await ctx.send("Message edited (<https://discordapp.com/channels/" + str(ctx.guild.id) + "/" + str(channel.id) + "/" + str(message_id) + ">)")

    @commands.command(pass_context=True, aliases=["echoReact", "react"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def echo_react(self, ctx, message: discord.Message, emote: typing.Union[discord.Emoji, str]):
        """
        Adds a reaction to a message
        Usage: .echoReact <message> <emote>

        :param ctx: context object
        :param message: message link or ID
        :param emote: emote to react with
        """
        await message.add_reaction(emote)
        await ctx.message.add_reaction("👍")

    @commands.command(pass_context=True, aliases=["echoRemoveReact", "reactRemove"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def echo_remove_react(self, ctx, message: discord.Message, emote: typing.Union[discord.Emoji, str]):
        """
        Removes the bots reaction from a message
        Usage: .echoRemoveReact <message> <emote>

        :param ctx: context object
        :param message: message link or ID
        :param emote: emote to un-react with
        """
        await message.remove_reaction(emote)
        await ctx.message.add_reaction("👍")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def purge(self, ctx, channel: typing.Optional[discord.TextChannel], *, number: int = 0):
        """
        Deletes given number of messages in a channel
        Usage: .purge (channel) <number>

        :param ctx: context object
        :param channel: (optional) channel to purge from
        :param number: number of messages to purge
        """
        if channel is None:
            await ctx.channel.purge(limit=int(number) + 1)
        else:
            await channel.purge(limit=int(number))

    @commands.command(pass_context=True, aliases=["selectivePurge", "spurge"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def selective_purge(self, ctx, target: typing.Union[discord.User, discord.TextChannel], user: typing.Optional[discord.User], *, number: int = 0):
        """
        Purges messages from a specific user in a channel
        Usage: .spurge (channel) <user> <number>

        :param ctx: context object
        :param target: member or channel to purge from
        :param user: user to purge if a channel is given
        :param number: number of messages to purge
        """
        messages = []
        count = 0

        if isinstance(target, discord.User):
            channel = ctx.message.channel
            messages.append(ctx.message)
            user = target
        else:
            channel = target

        old_message = (await channel.history(limit=1).flatten())[0].created_at

        while count < int(number):
            async for message in channel.history(limit=int(number), before=old_message, oldest_first=False):
                if message.author.id == user.id:
                    count += 1
                    messages.append(message)

                    if count == int(number):
                        break

                old_message = message.created_at

        await channel.delete_messages(messages)

    @commands.command(pass_context=True, aliases=["tPurge", "timePurge"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def time_purge(self, ctx, channel: typing.Optional[discord.TextChannel], *, time1, time2=None):
        """
        Purges messages from a time range in a channel
        Usage: .timePurge (channel) <startTime> (endTime)

        :param ctx: context object
        :param channel: (optional) channel to purge from
        :param time1: time to start purge at
        :param time2: (optional) time to end purge at
        """
        if channel is None:
            channel = ctx.message.channel

        after_date = dateparser.parse(time1)

        if after_date is None:
            await ctx.send("Not a valid after time/date")
            return

        if time2 is None:
            offset = datetime.utcnow() - datetime.now()
            messages = await channel.history(limit=None, after=after_date + offset).flatten()
        else:
            before_date = dateparser.parse(time2)

            if before_date is None:
                await ctx.send("Not a valid before time/date")
                return

            offset = datetime.utcnow() - datetime.now()
            messages = await channel.history(limit=None, after=after_date + offset, before=before_date + offset).flatten()

        if len(messages) == 0:
            await ctx.send("There are no messages to purge in this time frame")
            return

        response = "You are about to purge " + str(len(messages)) + " message(s) from " + channel.name
        if time2 is None:
            response += " after " + str(after_date) + ".\n"
        else:
            response += " between " + str(after_date) + " and " + str(before_date) + ".\n"

        response += "The purge will start at <" + messages[0].jump_url + "> and end at <" + messages[-1].jump_url + ">.\n\nAre you sure you want to proceed? (Y/N)"

        def check_author(message):
            return message.author.id == ctx.author.id

        query = await ctx.send(response)

        response = await self.bot.wait_for('message', check=check_author)
        if response.content.lower() == "y" or response.content.lower() == "yes":
            if channel.id == ctx.channel.id:
                messages.append(response)
                messages.append(query)
                await channel.delete_messages(messages)
            else:
                await channel.delete_messages(messages)
                await ctx.send("Successfully purged messages")
        else:
            await ctx.send("Cancelled purging messages")

    @commands.command(pass_context=True, aliases=["mPurge", "messagePurge"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def message_purge(self, ctx, start_message: discord.TextChannel, end_message: discord.TextChannel = None):
        """
        Purges messages from an inclusive range of messages
        Usage: .messagePurge <startMessage> (endMessage)

        :param ctx: context object
        :param start_message: first message to purge
        :param end_message: (optional) last message to purge
        """
        if end_message is None:
            messages = await start_message.channel.history(limit=None, after=start_message.created_at).flatten()
        else:
            if start_message.channel.id != end_message.channel.id:
                await ctx.send("End message is not in the same channel as the start message")
                return

            messages = await start_message.channel.history(limit=None, after=start_message.created_at, before=end_message.created_at).flatten()
            messages.append(end_message)

        messages.insert(0, start_message)

        if len(messages) == 0:
            await ctx.send("You've selected no messages to purge")
            return

        response = "You are about to purge " + str(len(messages)) + " message(s) from " + start_message.channel.name

        response += "\nThe purge will start at <" + messages[0].jump_url + "> and end at <" + messages[-1].jump_url + ">.\n\nAre you sure you want to proceed? (Y/N)"

        def check_author(message):
            return message.author.id == ctx.author.id

        query = await ctx.send(response)

        response = await self.bot.wait_for('message', check=check_author)

        if response.content.lower() == "y" or response.content.lower() == "yes":
            if start_message.channel.id == ctx.channel.id:
                messages.append(response)
                messages.append(query)
                await start_message.channel.delete_messages(messages)
            else:
                await start_message.channel.delete_messages(messages)
                await ctx.send("Successfully purged messages")
        else:
            await ctx.send("Cancelled purging messages")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def mute(self, ctx, member: discord.Member, time, *, reason):
        """
        Mutes a member for the given time and reason
        Usage: .mute <member> <time> <reason>

        :param ctx: context object
        :param member: member to mute
        :param time: time to mute for
        :param reason: reason for the mute (dm'ed to the user)
        """
        muted_role = ctx.guild.get_role(615956736616038432)
        mod_log = ctx.guild.get_channel(Config.settings["mod_log"])

        # Is user already muted
        if muted_role in member.roles:
            await ctx.send("This member is already muted")
            return

        # Check role hierarchy
        if ctx.author.top_role.position <= member.top_role.position:
            await ctx.send("You're not high enough in the role hierarchy to do that.")
            return

        username = member.name + "#" + str(member.discriminator)

        seconds = pytimeparse.parse(time)
        if seconds is None:
            await ctx.send("Not a valid time, try again")

        delta = timedelta(seconds=seconds)
        if len(reason) < 1:
            await ctx.send("You must include a reason for the mute")
            return

        mute_time = time_delta_string(datetime.utcnow(), datetime.utcnow() + delta)

        mute_embed = discord.Embed(title="Member muted", color=0xbe4041)
        mute_embed.description = "**Muted:** <@" + str(member.id) + ">\n**Time:** " + mute_time + "\n**__Reason__**\n> " + reason + "\n\n**Muter:** <@" + str(ctx.author.id) + ">"
        mute_embed.set_footer(text="ID: " + str(member.id))
        mute_embed.timestamp = datetime.utcnow()

        await member.add_roles(muted_role)
        await ctx.send("**Muted** user **" + username + "** for **" + mute_time + "** for: **" + reason + "**")
        await mod_log.send(embed=mute_embed)
        await member.send("**You were muted in the WPI Discord Server for " + mute_time + ". Reason:**\n> " + reason + "\n\nYou can respond here to contact WPI Discord staff.")

        await asyncio.sleep(seconds)

        await member.remove_roles(muted_role)
        await ctx.send("**Unmuted** user **" + username + "**")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def warn(self, ctx, member: discord.Member, *, reason):
        """
        Warns a specific user for given reason
        Usage: .warn <member> <reason>

        :param ctx: context object
        :param member: member of the server to warn
        :param reason: reason to log and DM
        """
        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        if len(reason) > 0:
            await member.send("You were warned in the WPI Discord Server. Reason:\n> " + reason, files=attachments)
        else:
            await ctx.send("No warning to send")
            return

        if str(member.id) in self.warns:
            self.warns[str(member.id)].append(reason)
        else:
            self.warns[str(member.id)] = [reason]

        save_json(os.path.join("config", "warns.json"), self.warns)

        await ctx.send("Warning sent to " + member.display_name + " (" + str(member.id) + "), this is their " + make_ordinal(len(self.warns[str(member.id)])) + " warning")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def warns(self, ctx, user: typing.Union[discord.Member, discord.User] = None):
        """
        List the warns for the server or a user
        Usage: .warns (user)

        :param ctx: context object
        :param user: (optional) user in the server
        """
        message = ""
        if user is None:
            if len(self.warns) == 0:
                message = "There are no warnings on this server"
            for user in self.warns:
                message += "Warnings for <@" + user + ">\n"
                count = 1
                for warn in self.warns[user]:
                    message += "__**" + str(count) + ".**__\n" + warn + "\n\n"
                    count += 1

                message += "\n\n"
        else:
            if str(user.id) in self.warns:
                message = "Warnings for <@" + str(user.id) + ">\n"
                for warn in self.warns[str(user.id)]:
                    message += "> " + warn + "\n"
            else:
                message = "This user does not exist or has no warnings"

        if len(message) > 2000:
            n = 2000
            for index in range(0, len(message), n):
                await ctx.send(message[index: index + n])
        else:
            await ctx.send(message)

    @commands.command(pass_context=True, aliases=["warnNote"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def warn_note(self, ctx, user: typing.Union[discord.Member, discord.User], *, reason):
        """
        Adds a warning to a user without DM'ing them
        Usage: .warnNote <user> <reason>

        :param ctx: context object
        :param user: user to add a note for
        :param reason: reason for the note
        """
        attachments = []
        if len(ctx.message.attachments) > 0:
            for i in ctx.message.attachments:
                attachments.append(await i.to_file())

        if str(user.id) in self.warns:
            self.warns[str(user.id)].append(reason)
        else:
            self.warns[str(user.id)] = [reason]

        save_json(os.path.join("config", "warns.json"), self.warns)

        if isinstance(user, discord.Member):
            await ctx.send("Warning added for " + user.display_name + " (" + str(user.id) + "), this is their " + make_ordinal(len(self.warns[str(user.id)])) + " warning")
        else:
            await ctx.send("Warning added for " + user.name + " (" + str(user.id) + "), this is their " + make_ordinal(len(self.warns[str(user.id)])) + " warning")

    @commands.command(pass_context=True, aliases=["clearWarn"])
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def clear_warn(self, ctx, user: typing.Union[discord.Member, discord.User]):
        """
        Clears the warnings for a user
        Usage: .clearWarn <user>

        :param ctx: context object
        :param user: user to clear warns for
        """
        if str(user.id) in self.warns:
            del self.warns[str(user.id)]
            await ctx.send("Cleared warnings for <@" + str(user.id) + ">")
            save_json(os.path.join("config", "warns.json"), self.warns)
        else:
            await ctx.send("This user does not exist or has no warnings")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def lockdown(self, ctx, channel: discord.TextChannel = None):
        """
        Locks down a channel so users cannot send messages in it
        Usage: .lockdown (channel)

        :param ctx: context object
        :param channel: (optional) channel to lockdown
        """
        if channel is None:
            lock_channel = ctx.channel
        else:
            lock_channel = channel

        overwrite = lock_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            await ctx.send("Channel is already locked down!")
        else:
            overwrite.update(send_messages=False)
            await lock_channel.send(":lock: **This channel is now locked**")
            await lock_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """
        Unlocks a channel that is locked
        Usage: .unlock (channel)

        :param ctx: context object
        :param channel: (optional) channel to unlock
        """
        if channel is None:
            lock_channel = ctx.channel
        else:
            lock_channel = channel

        overwrite = lock_channel.overwrites_for(ctx.guild.default_role)
        if overwrite.send_messages is False:
            overwrite.update(send_messages=None)
            await lock_channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await lock_channel.send(":unlock: **Unlocked the channel**")
        else:
            await ctx.send("Channel is not locked")

    @commands.command(pass_context=True)
    @commands.check(moderator_perms)
    @commands.guild_only()
    async def slowmode(self, ctx, channel: typing.Optional[discord.TextChannel], *, time):
        """
        Sets the slowmode in a channel
        Usage: .slowmode (channel) <time>

        :param ctx: context object
        :param channel: (optional) channel to set slowmode on
        :param time: time for the slowmode
        """
        if channel is None:
            channel = ctx.message.channel

        seconds = pytimeparse.parse(time)
        if seconds is None:
            await ctx.send("Not a valid time format, try again")
        elif seconds > 21600:
            await ctx.send("Slowmode delay is too long")
        else:
            await channel.edit(slowmode_delay=seconds)
            await ctx.send("Successfully set slowmode delay to " + str(seconds) + " seconds in #" + channel.name)

    @commands.command(pass_context=True)
    @commands.check(administrator_perms)
    @commands.guild_only()
    async def kick(self, ctx, member: discord.Member, *, reason):
        """
        Kicks a user from the server with a DM'ed reason
        Usage: .kick <member> <reason>

        :param ctx: context object
        :param member: member to kick
        :param reason: reason to kick, DM'ed to user
        """
        if len(reason) < 1:
            await ctx.send("Must include a reason with the kick")
        else:
            await member.send(member.guild.name + " kicked you for reason:\n> " + reason)
            await member.kick(reason=reason)
            await ctx.send("Successfully kicked user " + member.name + member.discriminator)

    @commands.command(pass_context=True)
    @commands.check(administrator_perms)
    @commands.guild_only()
    async def ban(self, ctx, member: discord.Member, *, reason):
        """
        Bans a user from the server, requires a reason as well
        Usage: .ban <member> <reason>

        :param ctx: context object
        :param member: member to ban
        :param reason: reason for the ban, DM'ed to user
        """
        if len(reason) < 1:
            await ctx.send("Must include a reason with the ban")
        else:
            await member.send(member.guild.name + " banned you for reason:\n> " + reason)
            await member.kick(reason=reason)
            await ctx.send("Successfully banned user " + member.name + member.discriminator)

    @commands.command(pass_context=True, name="modLog")
    @commands.check(administrator_perms)
    @commands.guild_only()
    async def change_mod_log(self, ctx, channel: discord.TextChannel):
        """
        Changes the channel in which to log mod actions into
        Usage: .modLog <channel>

        :param ctx: context object
        :param channel: channel
        """
        if Config.settings["mod_log"] != channel.id:
            Config.set_mod_log(channel)
            await ctx.send("Successfully updated mod log channel")
        else:
            await ctx.send("This is already the mod log channel")

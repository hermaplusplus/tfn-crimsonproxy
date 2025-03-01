import discord
from discord import app_commands
from discord import ui
from discord import utils

from typing import Optional

from datetime import datetime, timedelta

import time

import json
import csv

import requests

import math

import os

import subprocess

import random

SETTINGS = json.load(open("settings.json", "r"))

from byond2json import player2dict as getPlayerData

PRIORITY_GUILDS = [discord.Object(id=342787099407155202), discord.Object(id=1343630476497391646)]
TESTING_GUILD_ID = 342787099407155202
TESTING_ROLE_ID = 342788067297329154
HEAD_STAFF_ROLE_ID = 1343639309663604857
STAFF_ROLE_ID = 1343638775892545647

PROD = True

STAFF_HELP_MESSAGE = """
**Commands:**
`/help` shows this message.

**Staff Commands:**
`/lookup` shows some details of BYOND account by Ckey and its associated Discord user.
`/ccdb` lists CCDB bans for a BYOND account by Ckey.

**FAQ:**

Q: *Who should I direct technical questions to?*
A: <@188796089380503555>.

Q: *How can I help pay for the upkeep of the bot?*
A: https://sponsor.herma.moe/
"""

class Client(discord.Client):

    def __init__(self, *, intents: discord. Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        for i in PRIORITY_GUILDS:
            self.tree.copy_global_to(guild=i)
            await self.tree.sync(guild=i)
        print("Command tree sync completed")

intents = discord.Intents.all()
client = Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Breaching the Arcanum"
        )
    )

@app_commands.checks.has_any_role(
    TESTING_ROLE_ID,
    HEAD_STAFF_ROLE_ID,
    STAFF_ROLE_ID
)
@app_commands.describe(ckey="BYOND Username")
@app_commands.describe(public="If enabled, the output will be visible to all users.")
@client.tree.command(description="Shows some details of BYOND account by Ckey.")
async def lookup(interaction: discord.Interaction, ckey: Optional[str],  public: Optional[bool] = False):
    await interaction.response.defer(ephemeral=True if not public else False)
    if PROD or interaction.guild.id == TESTING_GUILD_ID:
        if ckey is not None:
            await interaction.followup.send("You must specify a Ckey.", ephemeral=True)
            return
        else:
            try:
                playerData = getPlayerData(ckey)
            except:
                await interaction.followup.send("The Ckey you specified couldn't be found.", ephemeral=True)
                return
        ccdb = requests.get(f"https://centcom.melonmesa.com/ban/search/{ckey}")
        embs = []
        emb = discord.Embed()
        if ckey is not None:
            emb.add_field(name="Ckey", value=f"`{playerData['ckey']}`", inline=True)
            emb.add_field(name="Account Creation Date", value=f"<t:{str(int(time.mktime(datetime.strptime(playerData['joined'], '%Y-%m-%d').timetuple())))}:d> (<t:{str(int(time.mktime(datetime.strptime(playerData['joined'], '%Y-%m-%d').timetuple())))}:R>)", inline=True)
        else:
            emb.add_field(name="Ckey", value=f"Not registered!", inline=False)
        if ckey is not None:
            emb.add_field(name="\u200B", value="\u200B")
        if ccdb.status_code == 200 and ckey is not None:
            ccdbdata = ccdb.json()
            if len(ccdbdata) == 0:
                emb.add_field(name="CCDB Bans", value=f"No bans found on CCDB.", inline=False)
            else:
                activebans = 0
                totalbans = 0
                for ban in ccdbdata:
                    if ban['active']:
                        activebans += 1
                    totalbans += 1
                emb.add_field(name="CCDB Bans", value=f"[{activebans} active, {totalbans-activebans} expired bans found on CCDB.](https://centcom.melonmesa.com/viewer/view/{ckey.replace(' ', '%20')})", inline=False)
        embs.append(emb)
        await interaction.followup.send(embeds=embs, ephemeral=True if not public else False)
    else:
        await interaction.followup.send("This command isn't currently available in this server - check back later!", ephemeral=True)

@app_commands.checks.has_any_role(
    TESTING_ROLE_ID,
    HEAD_STAFF_ROLE_ID,
    STAFF_ROLE_ID
)
@app_commands.describe(ckey="BYOND Username")
@app_commands.describe(page="Page Number")
@app_commands.describe(public="If enabled, the output will be visible to all users.")
@client.tree.command(description="Lists CCDB bans for a BYOND account by Ckey. Pagination begins at 1. Times displayed are in UTC.")
async def ccdb(interaction: discord.Interaction, ckey: str, page: Optional[int] = 1, public: Optional[bool] = False):
    await interaction.response.defer(ephemeral=True if not public else False)
    if PROD or interaction.guild.id == TESTING_GUILD_ID:
        try:
            playerData = getPlayerData(ckey)
        except:
            await interaction.followup.send("The Ckey you specified couldn't be found.", ephemeral=True)
            return
        ccdb = requests.get(f"https://centcom.melonmesa.com/ban/search/{ckey}")
        embs = []
        emb = discord.Embed()
        if ccdb.status_code == 200:
            ccdbdata = ccdb.json()
            for ban in ccdbdata:
                banstatus = "Active" if ban['active'] else "Expired"
                if "unbannedBy" in ban.keys():
                    banstatus = "Unbanned"
                emb = discord.Embed(title=f"{ban['type']} Ban | {ban['sourceName']} | {banstatus}", description=f"{ban['reason']}", colour=(discord.Colour.from_rgb(108, 186, 67) if banstatus == "Active" else (discord.Colour.from_rgb(213, 167, 70) if banstatus == "Expired" else discord.Colour.from_rgb(84, 151, 224))))
                emb.add_field(name="Banned", value=f"{ban['bannedOn'].replace('T',' ').replace('Z','')}", inline=True)
                emb.add_field(name="Admin", value=f"{ban['bannedBy']}", inline=True)
                if "expires" in ban.keys():
                    emb.add_field(name="Expires", value=f"{ban['expires'].replace('T',' ').replace('Z','')}", inline=True)
                if "banID" in ban.keys():
                    emb.add_field(name="Original Ban ID", value=f"`{ban['banID']}`", inline=True)
                if "unbannedBy" in ban.keys():
                    emb.add_field(name="Unbanned By", value=f"{ban['unbannedBy']}", inline=True)
                embs.append(emb)
        if len(embs) == 0:
            await interaction.followup.send(f"No bans found on CCDB for **`{ckey}`**.", embeds=embs, ephemeral=True if not public else False)
        if len(embs) > 0 and len(embs) <= 10:
            await interaction.followup.send(f"{len(embs)} bans found on CCDB for **`{ckey}`**.", embeds=embs, ephemeral=True if not public else False)
        if len(embs) > 10:
            maxpages = math.ceil(len(embs)/10)
            await interaction.followup.send(f"{len(embs)} bans found on CCDB for **`{ckey}`**. Displaying page {min(page, maxpages)} of {maxpages}", embeds=(embs[(page-1)*10:page*10] if page <= maxpages else embs[(maxpages-1)*10:maxpages*10]), ephemeral=True if not public else False)
    else:
        await interaction.followup.send("This command isn't currently available in this server - check back later!", ephemeral=True)

@client.tree.command(description="Displays a list of commands and how to use the bot.")
async def help(interaction:discord.Interaction):
    if PROD or interaction.guild.id == 342787099407155202:
        if any(item in [r.id for r in interaction.user.roles] for item in [TESTING_ROLE_ID, HEAD_STAFF_ROLE_ID, STAFF_ROLE_ID]):
            await interaction.response.send_message(STAFF_HELP_MESSAGE, ephemeral=True)
        else:
            await interaction.response.send_message("⛔ Sorry, this bot is currently for staff use only!", ephemeral=True)
    else:
        await interaction.response.send_message("This command isn't currently available in this server - check back later!", ephemeral=True)

#@client.tree.command(description="Toggle an optional role.")
#@app_commands.choices(role=[
#    app_commands.Choice(name='server uptime', value=0),
#    app_commands.Choice(name='content update', value=1),
#    app_commands.Choice(name='event', value=2),
#    app_commands.Choice(name='warmonger', value=3)
#])
#async def toggleping(interaction:discord.Interaction, role: int):
#    role_id = [UPTIME_PING_ROLE_ID, DEV_PING_ROLE_ID, EVENT_PING_ROLE_ID, WAR_PING_ROLE_ID][role]
#    role_name = ["server uptime", "content update", "event", "warmonger"][role]
#    if role_id not in [r.id for r in interaction.user.roles]:
#        await interaction.user.add_roles(discord.Object(role_id))
#        await interaction.response.send_message(f"You will be pinged for {role_name} announcements! 🎺", ephemeral=True)
#    else:
#        await interaction.user.remove_roles(discord.Object(role_id))
#        await interaction.response.send_message(f"You will no longer be pinged for {role_name} announcements. 💤", ephemeral=True)

@client.tree.error
async def on_app_command_error(interaction, error):
    if isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
    else:
        #await interaction.response.send_message("⚠ An unknown error occurred! If this continues to happen, please contact <@188796089380503555>.", ephemeral=True)
        await client.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="[ERROR] Breaching the Arcanum"
            )
        )
        raise error

client.run(SETTINGS['TOKEN'])


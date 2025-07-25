import discord  # pycord\
from discord import Option
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions, has_role
from itertools import cycle
import threading
import time
from datetime import datetime, timedelta, date
import json
import sqlite3
import asyncio
import schedule
import traceback
#import ffmpeg (for music cmds)

bot = discord.Bot(intents=discord.Intents.all())

db = sqlite3.connect('modmail.db')
cursor = db.cursor()

try:
  print("Attempting to create database...")
  cursor.execute("""
      CREATE TABLE modmail (
        user_id int,
        channel_id int,
        last_msg text
      )
  """)
except:
  print("Database already made!")

# for adding timeout
# cursor.execute("""
#     ALTER TABLE modmail (
#       last_msg text
#     )
# """)
#
# CTRL + / to add/remove comment :O

def check(key):
  if key is None:
    return False
  else:
    return True

@bot.event
async def on_ready():
  print("Your bot is ready")
  testguild = bot.get_channel(964992479277514832)
  rntime = datetime.now().timestamp()
  await testguild.send(f"**Bot online** as of <t:{int(rntime)}>! :D")
  #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="DMs for help :D"))
  change_status.start()

statuslist = cycle(["DMs for help :D", "#AgainstShelley >:(", "over the squids"])

@tasks.loop(seconds=120)
async def change_status():
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=(next(statuslist))))

# -------------------- Commands --------------------


# -------------------- /help --------------------

@bot.command(description="Shows all the commands")
async def help(ctx):
  embed = discord.Embed(title="Commands", description="Hey there! Here are my commands.",
                        color=0x0400ff)
  embed.add_field(name="/mute [member] [reason] [duration]", value="Mutes someone for a certain amount of time.", inline=False)
  embed.add_field(name="/unmute [member] [reason]", value="Unmutes someone.", inline=False)
  embed.add_field(name="/kick [member] [reason]", value="Kicks someone.", inline=False)
  embed.add_field(name="/ban [member] [reason]", value="Bans someone.", inline=False)
  embed.add_field(name="/unban", value="Unbans someone.", inline=False)
  embed.add_field(name="/purge [amount]", value="Deletes a specified amount of messages.", inline=False)
  embed.add_field(name="/lockdown", value="Prevents members from talking in channel (All roles with SEND MESSAGES as / or X in the channel will not be able to talk.).", inline=False)
  embed.add_field(name="/unlock", value="Unlocks channel.", inline=False)
  embed.add_field(name="/setlogs", value="Set the logs channel.", inline=False)

  await ctx.send_response(embed=embed)

# -------------------- /mute --------------------

@bot.command(description="Mutes someone for a certain amount of time.", pass_context=True)
@has_permissions(moderate_members=True)
async def mute(ctx, member: Option(discord.Member, description="Who you want to mute", required=True), reason: Option(str, required=False), days: Option(int, required=False), hours: Option(int, required=False), minutes: Option(int, required=False)):
  if member.id == ctx.author.id:
    await ctx.send_response("You can't mute yourself!")
    return
  elif member.guild_permissions.manage_channels and not ctx.author.guild_permissions.manage_channels:
    await ctx.send_response("I think this is a staff member...")
    return  

  check=0
  if reason != None:
    r = f"`{reason}`"
  else:
    r = "`unspecified reason`"
    reason = "unspecified reason"

  if days != None:
    d = f" {days} days,"
  else:
    d = ""
    days = 0
    check = check+1

  if hours != None:
    h = f" {hours} hours"
  else:
    h = ""
    hours = 0
    check = check+1

  if minutes != None:
    m = f" {minutes} minutes"
  else:
    m = ""
    minutes = 0
    check=check+1
  
  if check == 3:
    await ctx.send_response("**Mute unsuccessful!** Did you put in a duration?")
    check=0
    return
  
  check=0
  duration = timedelta(days=days, hours=hours, minutes=minutes)
  try:
    await member.timeout_for(duration, reason=reason)
  except:
    await ctx.send_response("I could not mute this member!")
    return
  embed = discord.Embed(title="Member Muted", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Member", value=f"{member.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
  embed.add_field(name="Duration", value=f"{d}{h}{m}", inline=True)
  embed.add_field(name="Reason", value=f"{reason}", inline=True)

  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  print(logch)
  logs = bot.get_channel(logch)
  await logs.send(content=f"**Member muted** in <#{ctx.channel.id}> !", embed=embed)

  await ctx.send_response(f"{member.mention} has been timed out for**{d}{h}{m}** for **{r}.**")

# -------------------- /unmute --------------------

@bot.command(description="Unmutes someone.", pass_context=True)
@has_permissions(moderate_members=True)
async def unmute(ctx, member: Option(discord.Member, description="Who you want to unmute", required=True), reason: Option(str, required=False)):
  try:
    await member.remove_timeout(reason=reason)
  except:
    await ctx.send_response("I could not unmute this member!")
    return
  if reason == None:
    reason="unspecified reason"
  embed = discord.Embed(title="Member Unuted", color=discord.Color.green(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Member", value=f"{member.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
  embed.add_field(name="Reason", value=f"{reason}", inline=True)

  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  print(logch)
  logs = bot.get_channel(logch)
  await logs.send(content=f"**Member unmuted** in <#{ctx.channel.id}> !", embed=embed)

  await ctx.send_response(f"{member.mention} has been unmuted for **{reason}.**")

# -------------------- /kick --------------------

@bot.command(description="Kicks someone.", pass_context=True)
@has_permissions(kick_members=True)
async def kick(ctx, member: Option(discord.Member, description="Who you want to kick", required=True), reason: Option(str, required=False)):
  if member.id == ctx.author.id:
    await ctx.send_response("You can't kick yourself!")
    return
  if member.guild_permissions.manage_channels and not ctx.author.guild_permissions.manage_channels:
    await ctx.send_response("I think this is a staff member...")
    return
  if reason==None:
    reason="unspecified reason"

  try:
    await member.kick(reason=reason)
  except:
    await ctx.send_response("I could not kick this member!")  
    return

  embed = discord.Embed(title="Member Kicked", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Member", value=f"{member.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
  embed.add_field(name="Reason", value=f"{reason}", inline=True)


  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  logs = bot.get_channel(logch)
  await logs.send(content=f"**Member kicked** in <#{ctx.channel.id}> !", embed=embed)

  await ctx.send_response(f"{member.mention} has been **kicked** for `{reason}`!")
  
# -------------------- /ban --------------------

@bot.command(description="Bans someone.", pass_context=True)
@has_permissions(ban_members=True)
async def ban(ctx, member: Option(discord.Member, description="Who you want to ban", required=True)):
  if member.id == ctx.author.id:
    await ctx.send_response("You can't ban yourself!")
    return
  if member.guild_permissions.manage_channels and not ctx.author.guild_permissions.manage_channels:
    await ctx.send_response("I think this is a staff member...")
    return
  if reason==None:
    reason="unspecified reason"

  try:
    await member.ban(reason=reason)
  except:
    await ctx.send_response("I could not ban this member!")
    return  

  embed = discord.Embed(title="Member Banned", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Member", value=f"{member.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
  embed.add_field(name="Reason", value=f"{reason}", inline=True)


  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  logs = bot.get_channel(logch)
  await logs.send(content=f"**Member banned** in <#{ctx.channel.id}> !", embed=embed)

  await ctx.send_response(f"{member.mention} has been **banned** for `{reason}`!")

# -------------------- /unban --------------------

@bot.command(description="Unmutes someone.", pass_context=True)
@has_permissions(moderate_members=True)
async def unban(ctx, member: Option(discord.Member, description="Who you want to unmute", required=True), reason: Option(str, required=False)):
  try:
    await member.unban(reason=reason)
  except:
    await ctx.send_response("I could not unban this member!")
    return
  if reason == None:
    reason="unspecified reason"
  embed = discord.Embed(title="Member Unbanned", color=discord.Color.green(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Member", value=f"{member.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)
  embed.add_field(name="Reason", value=f"{reason}", inline=True)

  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  print(logch)
  logs = bot.get_channel(logch)
  await logs.send(content=f"**Member unbanned** in <#{ctx.channel.id}> !", embed=embed)

  await ctx.send_response(f"{member.mention} has been unbanned for **{reason}.**")

# -------------------- /purge --------------------

@bot.command(description="Clears a specific amount of messages. Needs MANAGE MESSAGES permission.", pass_context=True)
@has_permissions(manage_messages=True)
async def purge(ctx, limit: Option(int, description="How many messages you want to delete")):
  await ctx.channel.purge(limit=limit + 1)
  await ctx.send_response('Cleared by {}'.format(ctx.author.mention), delete_after=3)
  await ctx.message.delete()

# -------------------- /lockdown --------------------
@bot.command(description="Prevents members from talking in channel.")
@commands.has_permissions(manage_channels=True)
async def lockdown(ctx):
  await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

  embed = discord.Embed(title="Channel Locked", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.timezone.utc))
  embed.add_field(name="Channel", value=f"{ctx.channel.mention}", inline=True)
  embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)


  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(ctx.guild.id)])
  logs = bot.get_channel(logch)
  await logs.send(content=f"<#{ctx.channel.id}> was locked!", embed=embed)

  await ctx.send_response(
    ctx.channel.mention + " ***is now in lockdown.*** (Roles that have the [Send Messages] permission in this channel can still talk.)")

# -------------------- /unlock --------------------
@bot.command(description="Unlocks channel")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
  try:
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)

    embed = discord.Embed(title="Channel Unlocked", color=discord.Color.green(), timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.add_field(name="Channel", value=f"{ctx.channel.mention}", inline=True)
    embed.add_field(name="Moderator", value=f"{ctx.author.mention}", inline=True)

    with open("logs.json", 'r') as f:
      data = json.load(f)
    logch = int(data[str(ctx.guild.id)])
    logs = bot.get_channel(logch)
    await logs.send(content=f"<#{ctx.channel.id}> was unlocked!", embed=embed)
    await ctx.send_response(f"<#{ctx.channel.id}> ***has been unlocked.***")
  except:
    await ctx.send_response(ctx.channel.mention + "is not locked. Check the channel permissions.")

# -------------------- /setlogs --------------------

@bot.command(description="Set log channel.")
@commands.has_permissions(manage_channels=True)
async def setlogs(ctx):
  with open("logs.json", 'r') as f:
    data = json.load(f)

  data[f"{ctx.guild.id}"] = ctx.channel.id

  with open("logs.json", 'w') as f:
    json.dump(data, f)

  await ctx.send_response(f"**{ctx.guild.name}** log channel set to **{ctx.channel.mention}!**")


# -------------------- Modmail --------------------

async def tixtimeout():
  now = date.today()
  yesterday = now - timedelta(days = 1)
  guild = bot.get_guild(969391671982841936)
  admin_role = discord.utils.get(guild.roles, name='Modmail License Certified')

  cursor.execute("SELECT last_msg FROM modmail")
  result = cursor.fetchall

  for x in result:
    if x == yesterday:
      close_embed = discord.Embed(
        title="Ticket is Closed",
        timestamp=datetime.now(),
        color = discord.colour.Color.nitro_pink(),
        description=f"Ticket timed out."
      )
      close_embed.set_footer(text="By replying, you will open another ticket")

      cursor.execute("SELECT user_id FROM modmail WHERE last_msg = (?)", (x, ))
      uid = cursor.fetchone()
      user = bot.get_user(uid)

      cursor.execute("SELECT channel_id FROM modmail WHERE last_msg = (?)", (x, ))
      cid = cursor.fetchone()
      channel = bot.get_channel(cid)
      
      await user.send(embed=close_embed)
      await channel.send(f"***Ticket timed out!***")

      overwrite = discord.PermissionOverwrite()
      overwrite.send_messages = False
      overwrite.read_messages = True
      await channel.set_permissions(admin_role, overwrite=overwrite)
      await channel.edit(name=f"closed-{user.name}")
      
      cursor.execute("DELETE FROM modmail WHERE channel_id = (?)", (channel.id, ))
      db.commit()
      
      archive = discord.utils.get(guild.channels, name="archives")
      await channel.edit(category=archive)
      return
      
schedule.every().day.at("23:59").do(tixtimeout)

# https://youtu.be/R20ZOQUoKFo | https://github.com/PiggehJB/modmail-reworked
@bot.event
async def on_message(ctx):
    guild = bot.get_guild(969391671982841936)
    category = bot.get_channel(1073832558900547635)
    admin_role = discord.utils.get(guild.roles, name='Modmail License Certified')

    if ctx.author == bot.user:
        return
    
    if not ctx.guild:
        cursor.execute("SELECT user_id FROM modmail WHERE user_id = (?)", (ctx.author.id, ))
        if check(cursor.fetchone()) is True:
            try:
                print("RETURNING USER")
                cursor.execute("SELECT channel_id FROM modmail WHERE user_id = (?)", (ctx.author.id, ))
                channel_id = cursor.fetchone()
                for id in channel_id:
                    channel = bot.get_channel(id)
                    if channel == None:
                        cursor.execute("DELETE FROM modmail WHERE channel_id = (?)", (id, ))
                        db.commit()
                        print("Removed", id)
                    else:
                        cid = id
                        print(id)
                        break
                channel = bot.get_channel(cid)
                if channel is None:
                    print("CHANNEL NOT FOUND")
                    overwrites = {
                        guild.default_role : discord.PermissionOverwrite(read_messages=False),
                        admin_role : discord.PermissionOverwrite(read_messages=True)
                    }
                    new_channel = await guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites, category=category)

                    cursor.execute("UPDATE modmail SET channel_id = (?) WHERE user_id = (?)", (new_channel.id, ctx.author.id, ))
                    db.commit()
                    channel = new_channel
                
                embed = discord.Embed(title="New Message", color=discord.Color.purple(), timestamp=datetime.now(), description=ctx.content)
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

                await channel.send(embed=embed)
                if ctx.attachments:
                  for x in ctx.attachments:
                    await channel.send(content=x.url)
                  
                now = str(date.today())
                cursor.execute("UPDATE modmail SET last_msg = (?) WHERE channel_id = (?)", (now, channel.id, ))
                db.commit()

                await ctx.add_reaction(emoji='✅')

            except:
                print(traceback.format_exc())
                await ctx.add_reaction(emoji='❌')
                
        else:
            try:
                print("NEW USER")

                em = discord.Embed(title="Create a ticket?", description="If you want to create a ticket, react with ✅")
                em.set_footer(text="if you don't want to create a ticket, you can ignore this message.")
                msg = await ctx.channel.send(embed=em)

                for emoji in ('✅'): # https://stackoverflow.com/questions/62129427/check-if-a-specific-user-reacted-discord-py
                    await msg.add_reaction(emoji) 
                    try:

                        def reactcheck(rctn, user):
                            return user.id == ctx.author.id and str(rctn) == '✅'

                        rctn, user = await bot.wait_for("reaction_add", check=reactcheck, timeout=30)

                        await ctx.channel.send("Ticket created!")
                    except asyncio.TimeoutError:
                        await ctx.channel.send("Sorry, you didn't react in time!")
                        return
                
                overwrites = {
                    guild.default_role : discord.PermissionOverwrite(read_messages=False),
                    admin_role : discord.PermissionOverwrite(read_messages=True)
                }

                modmail_channel = await guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites, category=category)

                cursor.execute("INSERT INTO modmail VALUES (?, ?, ?)", (ctx.author.id, modmail_channel.id, str(date.today), ))
                db.commit()

                embed = discord.Embed(
                    title="New Modmail Ticket",
                    color = discord.colour.Color.brand_green(),
                    timestamp=datetime.now(),
                    description=ctx.content
                )
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

                await modmail_channel.send("<@&1066963647131308092>", embed=embed)
                if ctx.attachments:
                  for x in ctx.attachments:
                    await modmail_channel.send(content=x.url)

                await ctx.add_reaction(emoji='✅')

            except:
                print(traceback.format_exc())
                await ctx.add_reaction(emoji='❌')

    else:
        if ctx.channel.category == category and "ticket-" in ctx.channel.name:
            print("CATEGORY AND NAME VERIFIED")

            # cursor.execute("INSERT INTO modmail VALUES (?, ?)", (ctx.author.id, ctx.channel.id, ))
            # db.commit()
            # print("db.commit success")
            
            # cursor.execute("SELECT channel_id FROM modmail WHERE user_id = (?)", (ctx.author.id, ))
            # print("CURSOR.EXECUTE SUCCESS")
            
            # if check(cursor.fetchone()) is True:
            print("FOUND TICKET USER")
            try:
                cursor.execute("SELECT user_id FROM modmail WHERE channel_id = (?)", (ctx.channel.id, ))
                print(f"ctx.channel.id: {ctx.channel.id}")
                user_id = cursor.fetchone()

                for id in user_id:
                    user_id = id
                    break
                user = discord.utils.get(bot.get_all_members(), id=user_id) #vill.members
                if user is None:
                    await ctx.reply("I can't find that user ⚠")
                    await ctx.add_reaction(emoji='❌')
                    return
                else:
                    if ctx.content == '!close': # -------------------- !close --------------------
                        close_embed = discord.Embed(
                            title="Ticket is Closed",
                            timestamp=datetime.now(),
                            color = discord.colour.Color.nitro_pink(),
                            description=f"Closed by {ctx.author.mention}"
                        )
                        close_embed.set_footer(text="By replying, you will open another ticket")
                        await user.send(embed=close_embed)
                        channel = ctx.channel
                        await channel.send(f"***Ticket Closed by {ctx.author.mention}***")

                        overwrite = discord.PermissionOverwrite()
                        overwrite.send_messages = False
                        overwrite.read_messages = True
                        await channel.set_permissions(admin_role, overwrite=overwrite)
                        await channel.edit(name=f"closed-{user.name}")
                        
                        cursor.execute("DELETE FROM modmail WHERE channel_id = (?)", (channel.id, ))
                        db.commit()
                        
                        archive = discord.utils.get(ctx.guild.channels, name="archives")
                        await channel.edit(category=archive)
                        return
                    elif ctx.content.startswith("!noembed"): # -------------------- !noembed --------------------
                      msgcontent = ctx.content.replace("!noembed", f"**From {ctx.author.name}:**")
                      await user.send(msgcontent)
                    else:
                        embed = discord.Embed(
                            title="Message From {}".format(ctx.guild.name),
                            color = discord.colour.Color.og_blurple(),
                            timestamp=datetime.now(),
                            description=ctx.content
                        )

                        embed.set_author(
                        name=ctx.author.name,
                        icon_url = ctx.author.avatar.url
                        )
                        await user.send(embed=embed)

                        if ctx.attachments:
                          for x in ctx.attachments:
                            await user.send(content=x.url)
                      

                    await ctx.add_reaction(emoji='✅')

            except:
                print(traceback.format_exc())
                await ctx.add_reaction(emoji='❌')
            
# -------------------- /close --------------------

@bot.command(guild_ids=[969391671982841936], description="(Modmail) Closes a ticket")
@has_role(1066963647131308092)
async def close(ctx):
  category = bot.get_channel(1073832558900547635)
  guild = bot.get_guild(969391671982841936)
  admin_role = discord.utils.get(guild.roles, name='Modmail License Certified')
  if ctx.channel.category == category:
    try:
      cursor.execute("SELECT user_id FROM modmail WHERE channel_id = (?)", (ctx.channel.id, ))
      user_id = cursor.fetchone()
    
      for id in user_id:
        user_id = id
        break

      user = discord.utils.get(bot.get_all_members(), id=user_id)
      if user is None:
        await ctx.reply("I can't find that user ⚠")
        await ctx.add_reaction(emoji='❌')
        return
      
      close_embed = discord.Embed(
      title="Ticket is Closed",
      timestamp=datetime.now(),
      color = discord.colour.Color.nitro_pink(),
      description=f"Closed by {ctx.author.mention}"
      )
      close_embed.set_footer(text="By replying, you will open another ticket")
      await user.send(embed=close_embed)
      channel = ctx.channel
      await ctx.send_response(f"***Ticket Closed by {ctx.author.mention}***")

      overwrite = discord.PermissionOverwrite()
      overwrite.send_messages = False
      overwrite.read_messages = True
      await channel.set_permissions(admin_role, overwrite=overwrite)
      await channel.edit(name=f"closed-{user.name}")
      
      cursor.execute("DELETE FROM modmail WHERE channel_id = (?)", (channel.id, ))
      db.commit()

      archive = discord.utils.get(ctx.guild.channels, name="archives")
      await channel.edit(category=archive)
    except Exception as e:
      print(traceback.format_exc())
      error = str(e)
      if "permissions" in error.lower():
        await ctx.send_response("I'm missing permissions!")
      else:
        await ctx.send_response("Could not close ticket!")
  else:
    await ctx.send_response("This isn't a ticket!")

# -------------------- /noembed --------------------

@bot.command(guild_ids=[969391671982841936], description="(Modmail) Sends a message in plain text")
@has_role(1066963647131308092)
async def noembed(ctx, message: Option(str, description="The message you would like to send")):
  category = bot.get_channel(1073832558900547635)
  if ctx.channel.category == category:
    try:
      cursor.execute("SELECT user_id FROM modmail WHERE channel_id = (?)", (ctx.channel.id, ))
      user_id = cursor.fetchone()
        
      for id in user_id:
        user_id = id
        break

      user = discord.utils.get(bot.get_all_members(), id=user_id)
      await user.send(f"**From {ctx.author.name}:** {message}")
      await ctx.send_response(f"{message} \n\n*(sent with no embed)*")
    except:
      print(traceback.format_exc())
  else:
    await ctx.send_response("This isn't a ticket!")
      
  
# -------------------- Anti-raid --------------------


# -------------------- Detects mass channel deletion --------------------
channelsdel = 0


def channeltimer():
  time.sleep(10)
  global channelsdel
  channelsdel = 0


thread = threading.Thread(daemon=True, target=channeltimer)
thread.start()


@bot.event
async def on_guild_channel_delete(channel):
  inguild = channel.guild
  guild = bot.get_guild(channel.guild.id)
  entry = await inguild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1).get()
  pst_time = datetime.now().timestamp()

  embed = discord.Embed(title="Channel Deleted",
                        description="No punishment issued.",
                        color=discord.Color.red())
  embed.add_field(name="User", value=f"{entry.user.mention}", inline=True)
  embed.add_field(name="Action", value="Deleted a channel.", inline=True)
  embed.add_field(name="Channel", value=channel.name, inline=True)
  embed.add_field(name="Guild", value=inguild, inline=True)
  embed.add_field(name="Date", value=f"<t:{int(pst_time)}>", inline=True)

  with open("logs.json", 'r') as f:
    data = json.load(f)
  logch = int(data[str(channel.guild.id)])
  logs = bot.get_channel(logch)
  await logs.send(content=f"{entry.user} deleted {channel.name} in {channel.guild}!", embed=embed)

  global channelsdel
  if channelsdel == 5:
    member = entry.user
    membid = guild.get_member(entry.user.id)
    try:
      for i in membid.roles:
        try:
          await membid.remove_roles(i)
        except:
          print(f"[Antiraid | Channels] Can't remove the role {i}")
      await member.send(
        f"Your roles were taken away in {inguild} because a raid was detected!")
      punish = "quarantined"

    except:
      print(f"[Antiraid | Channels] Could not find {member}'s roles")
      await member.send(
        f"You were kicked from {inguild} because a raid was detected!")
      await guild.kick(member, reason="Deleted multiple channels (Anti-raid)")
      punish = "kicked"

    embed = discord.Embed(title="Raid Detected",
                          description=f"Member {punish}.",
                          color=discord.Color.red())
    embed.add_field(name="User", value=f"{entry.user.mention}", inline=True)
    embed.add_field(name="Action", value="Deleted a channel.", inline=True)
    embed.add_field(name="Channel", value=channel.name, inline=True)
    embed.add_field(name="Guild", value=inguild, inline=True)
    embed.add_field(name="Date", value=f"<t:{int(pst_time)}>", inline=True)

    with open("logs.json", 'r') as f:
      data = json.load(f)
    logch = int(data[str(channel.guild.id)])
    logs = bot.get_channel(logch)
    await logs.send(content=f"**Raid detected** in {channel.guild}!", embed=embed)
    channelsdel = 0

  else:
    channelsdel = channelsdel + 1
    print("[Antiraid | Channels] channelsdel:", channelsdel)


# -------------------- Detects @everyone spam --------------------
everyonepings = 0


def everyonetimer():
  global everyonepings
  while True:
    time.sleep(10)
    everyonepings = 0


thread = threading.Thread(daemon=True, target=everyonetimer)
thread.start()


@bot.listen('on_message')
async def everyoneraid(message):
  mention = f'@everyone'
  if mention in message.content:
    inguild = message.guild
    guild = bot.get_guild(message.guild.id)
    pst_time = datetime.now().timestamp()

    global everyonepings
    if everyonepings == 5:
      member = message.author
      membid = guild.get_member(member)

      try:
        for i in membid.roles:
          try:
            await membid.remove_roles(i)
          except:
            print(f"[Antiraid | @everyone] Can't remove the role {i}")
        await member.send(
          f"Your roles were taken away in {inguild} because a raid was detected!")
        punish = "quarantined"
      except:
        print(f"[Antiraid | @everyone] Could not find {member}'s roles")
        await member.send(
          f"You were kicked from {inguild} because a raid was detected!")
        await guild.kick(member, reason="Spammed @everyone")
        punish = "kicked"

      embed = discord.Embed(title="Raid Detected",
                            description=f"Member {punish}.",
                            color=discord.Color.red())
      embed.add_field(name="User", value=f"{member.mention}", inline=True)
      embed.add_field(name="Action", value="Spammed @everyone.", inline=True)
      embed.add_field(name="Guild", value=inguild, inline=True)
      embed.add_field(name="Date", value=f"<t:{int(pst_time)}>", inline=True)

      with open("logs.json", 'r') as f:
        data = json.load(f)
      logch = int(data[str(message.guild.id)])
      logs = bot.get_channel(logch)
      await logs.send(content=f"**Raid detected** in {inguild}!", embed=embed)
      everyonepings = 0

    else:
      everyonepings = everyonepings + 1
      print("[Antiraid | @everyone] everyonepings:", everyonepings)  

bot.run("insert token here")    # MUST INSERT TOKEN !!!

while True:
  schedule.run_pending()
  time.sleep(60)

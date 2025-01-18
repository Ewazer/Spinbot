import os
import random
import json
import discord
import asyncio
from datetime import datetime
from discord.ext import commands

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix="$",
                   intents=intents,
                   description='Hi',
                   help_command=None)


@bot.event
async def on_ready():
  print(f'Connecté en tant que {bot.user.name}')
  await bot.change_presence(activity=discord.Streaming(
      name="your business", url="https://www.twitch.tv/discord"))


def load_coins(guild_id):
  file_path = f"{guild_id}_coins.json"
  if os.path.exists(file_path):
    with open(file_path, "r") as f:
      return json.load(f)
  else:
    return {}


def save_coins(guild_id, coins):
  file_path = f"{guild_id}_coins.json"
  with open(file_path, "w") as f:
    json.dump(coins, f, indent=4)


def has_permissions(ctx):
  guild_id = str(ctx.guild.id)
  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])
  user_id = str(ctx.author.id)
  role_ids = [role.id for role in ctx.author.roles]
  if user_id in allowed_users or any(f"<@&{role_id}>" in allowed_users
                                     for role_id in role_ids):
    return True
  return False


@bot.command()
async def addcoins(ctx, user: discord.Member, amount: int):
  guild_id = str(ctx.guild.id)
  if not has_permissions(ctx) and not ctx.author.guild_permissions.administrator:
    await ctx.send("Vous n'avez pas la permission d'utiliser cette commande. Vous pouvez gérer les permissions en effectuant la commande `$setup`.")
    return

  coins = load_coins(guild_id)
  if str(user.id) in coins:
    coins[str(user.id)] += amount
  else:
    coins[str(user.id)] = amount
  save_coins(guild_id, coins)
  await ctx.send(f"{amount} pièces :coin: ont été ajoutées à {user.mention}")


@bot.command()
async def removecoins(ctx, user: discord.Member, amount: int):
  guild_id = str(ctx.guild.id)
  if not has_permissions(ctx) and not ctx.author.guild_permissions.administrator:
    await ctx.send("Vous n'avez pas la permission d'utiliser cette commande. Vous pouvez gérer les permissions en effectuant la commande `$setup`.")
    return

  coins = load_coins(guild_id)
  if str(user.id) in coins:
    coins[str(user.id)] -= amount
    if coins[str(user.id)] < 0:
      coins[str(user.id)] = 0
    save_coins(guild_id, coins)
    await ctx.send(f"{amount} pièces :coin: ont été retirées à {user.mention}")
  else:
    await ctx.send(f"{user.mention} n'a pas de pièces.")


@bot.command()
async def leaderboard(ctx):
  guild_id = str(ctx.guild.id)
  coins = load_coins(guild_id)
  if not coins:
    await ctx.send("Personne sur ce serveur n'a de pièces.")
    return

  filtered_coins = {k: v for k, v in coins.items() if isinstance(v, int)}

  if not filtered_coins:
    await ctx.send("Personne sur ce serveur n'a de pièces.")
    return

  sorted_coins = sorted(filtered_coins.items(),
                        key=lambda x: x[1],
                        reverse=True)
  leaderboard_embed = discord.Embed(title="Classement des utilisateurs",
                                    color=discord.Color.gold())
  for index, (user_id, coin) in enumerate(sorted_coins[:10]):
    user = bot.get_user(int(user_id))
    leaderboard_embed.add_field(name=f"{index+1}. {user.name}",
                                value=f"Pièces: {coin} :coin:",
                                inline=False)
  await ctx.send(embed=leaderboard_embed)


@bot.command()
async def setup(ctx):
  if not ctx.author.guild_permissions.administrator:
    await ctx.send("Vous devez être administrateur pour configurer le bot.")
    return

  overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
      ctx.author: discord.PermissionOverwrite(read_messages=True)
  }
  setup_channel = await ctx.guild.create_text_channel('setup SpinBot',
                                                      overwrites=overwrites)

  embed = discord.Embed(
      title=
      "Les commandes suivantes seront disponibles pour configurer le bot pendant 3 minutes :",
      url=
      "https://discord.com/oauth2/authorize?client_id=1227716254949707796&permissions=8&scope=bot+applications.commands",
      description=
      "```\n$adduser @utilisateur - Les membres mentionnés pourront gérer les pièces \n$removeser @utilisateur - Les membres mentionnés ne pourront plus gérer les coins \n$addrole @role - Les rôles mentionnés pourront gérer les coins \n$removerole @role - Les rôles mentionnés ne pourront plus gérer les coins \n$setup_reward <montant/off> - Configure la récompense quotidienne. Utilisez <off> pour désactiver la récompense. ```",
      colour=discord.Color.gold())

  embed.set_author(
      name="SpinBot",
      url=
      "https://discord.com/oauth2/authorize?client_id=1227716254949707796&permissions=8&scope=bot+applications.commands",
      icon_url=
      "https://cdn.discordapp.com/avatars/1227716254949707796/10d0d73af97dba509e61310b24958a79.webp?size=240"
  )

  embed.set_footer(
      text="@ewazer https://ewazer.com",
      icon_url=
      "https://cdn.discordapp.com/attachments/1228985803867426908/1229083563220013218/0_03.png?ex=662e6444&is=661bef44&hm=698d047885d27cd86315a9d924e02e99ca4a1f41481cf359412ad88bb127d4c0&"
  )

  await setup_channel.send(embed=embed)

  def check(m):
    return m.channel == setup_channel and m.author == ctx.author

  try:
    await bot.wait_for('message', timeout=180.0, check=check)
  except asyncio.TimeoutError:
    pass
  await asyncio.sleep(180)
  await setup_channel.delete()


@bot.command()
async def adduser(ctx, user: discord.Member):
  guild_id = str(ctx.guild.id)
  if not ctx.author.guild_permissions.administrator:
    await ctx.send(
        "Vous devez être administrateur pour utiliser cette commande.")
    return

  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])
  if str(user.id) not in allowed_users:
    allowed_users.append(str(user.id))
    coins["allowed_users"] = allowed_users
    save_coins(guild_id, coins)
    await ctx.send(
        f"{user.mention} a été ajouté à la liste des utilisateurs autorisés.")
  else:
    await ctx.send(
        f"{user.mention} est déjà dans la liste des utilisateurs autorisés.")


@bot.command()
async def removeuser(ctx, user: discord.Member):
  guild_id = str(ctx.guild.id)
  if not ctx.author.guild_permissions.administrator:
    await ctx.send(
        "Vous devez être administrateur pour utiliser cette commande.")
    return

  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])
  if str(user.id) in allowed_users:
    allowed_users.remove(str(user.id))
    coins["allowed_users"] = allowed_users
    save_coins(guild_id, coins)
    await ctx.send(
        f"{user.mention} a été retiré de la liste des utilisateurs autorisés.")
  else:
    await ctx.send(
        f"{user.mention} n'est pas dans la liste des utilisateurs autorisés.")


@bot.command()
async def addrole(ctx, role: discord.Role):
  guild_id = str(ctx.guild.id)
  if not ctx.author.guild_permissions.administrator:
    await ctx.send(
        "Vous devez être administrateur pour utiliser cette commande.")
    return

  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])
  if f"<@&{role.id}>" not in allowed_users:
    allowed_users.append(f"<@&{role.id}>")
    coins["allowed_users"] = allowed_users
    save_coins(guild_id, coins)
    await ctx.send(
        f"Le rôle {role.name} a été ajouté à la liste des utilisateurs autorisés."
    )
  else:
    await ctx.send(
        f"Le rôle {role.name} est déjà dans la liste des utilisateurs autorisés."
    )


@bot.command()
async def removerole(ctx, role: discord.Role):
  guild_id = str(ctx.guild.id)
  if not ctx.author.guild_permissions.administrator:
    await ctx.send(
        "Vous devez être administrateur pour utiliser cette commande.")
    return

  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])
  if f"<@&{role.id}>" in allowed_users:
    allowed_users.remove(f"<@&{role.id}>")
    coins["allowed_users"] = allowed_users
    save_coins(guild_id, coins)
    await ctx.send(
        f"Le rôle {role.name} a été retiré de la liste des utilisateurs autorisés."
    )
  else:
    await ctx.send(
        f"Le rôle {role.name} n'est pas dans la liste des utilisateurs autorisés."
    )


@bot.command()
async def allowed(ctx):
  guild_id = str(ctx.guild.id)
  coins = load_coins(guild_id)
  allowed_users = coins.get("allowed_users", [])

  users_mention = "\n".join([
      f"<@{user_id}>" for user_id in allowed_users
      if not user_id.startswith('<@&')
  ])
  roles_mention = "\n".join(
      [f"{role_id}" for role_id in allowed_users if role_id.startswith('<@&')])

  if not allowed_users:
    await ctx.send(
        "Aucun utilisateur ni rôle n'est autorisé à gérer les coins pour ce serveur."
    )
  else:
    description = ""
    if users_mention:
      description += f"Utilisateurs :\n{users_mention}\n\n"
    if roles_mention:
      description += f"Rôles :\n{roles_mention}\n\n"

    embed = discord.Embed(title="Personnes autorisées à gérer les coins :",
                          description=f"{description}",
                          colour=discord.Color.gold())

    embed.set_author(
        name="SpinBot",
        url=
        "https://discord.com/oauth2/authorize?client_id=1227716254949707796&permissions=8&scope=bot+applications.commands",
        icon_url=
        "https://cdn.discordapp.com/attachments/1228985803867426908/1229083890589892789/logo-rond-colore-vintage-jeu-hasard_153969-559.jpg?ex=662e6492&is=661bef92&hm=1969dfde91376a868ef2cfd49b9cbf79d7409f3221adcc373413fcb7e4fc66e6&"
    )

    embed.set_footer(
        text="@ewazer ewazer.com",
        icon_url=
        "https://cdn.discordapp.com/attachments/1228985803867426908/1229083563220013218/0_03.png?ex=662e6444&is=661bef44&hm=698d047885d27cd86315a9d924e02e99ca4a1f41481cf359412ad88bb127d4c0&"
    )

    await ctx.send(embed=embed)


@bot.command()
async def money(ctx, user: discord.Member = None):
  if user is None:
    user = ctx.author

  guild_id = str(ctx.guild.id)
  coins = load_coins(guild_id)
  user_id = str(user.id)

  if user_id in coins:
    await ctx.send(f"{user.mention} a {coins[user_id]} pièces :coin:")
  else:
    await ctx.send(f"{user.mention} n'a pas encore de pièces.")


roulette_running = {}
roulette_bets = {}


@bot.command()
async def roulette(ctx):
  global roulette_running

  guild_id = ctx.guild.id

  if guild_id in roulette_running and roulette_running[guild_id]:
    await ctx.send(
        "Une partie de la roulette est déjà en cours sur un serveur.")
    return

  roulette_running[guild_id] = True
  emojis = ["🟥", "⚫", "🟩"]
  number = random.randint(0, 34)

  if number == 0:
    color = "🟩"
  elif number % 2 == 0:
    color = "⚫"
  else:
    color = "🟥"
  embed = discord.Embed(
      title="🎰 Ouverture des paris pour la roulette 🎰",
      description=
      "Les paris sont maintenant ouverts pour la roulette ! Faites vos mises en utilisant la commande `$bet`. Exemple : `$bet color 100 red`",
      color=discord.Color.gold())
  await ctx.send(embed=embed)
  await ctx.send("** **")
  message = await ctx.send("🔄 Tourne la roulette...")
  for _ in range(30):
    random.shuffle(emojis)
    await message.edit(content="🔄 Tourne la roulette... " + "".join(emojis))
    await asyncio.sleep(0.5)
  await message.edit(content=f"La roulette s'arrête sur... {color} {number}")

  if color == "🟩":
    color = "green"
  elif color == "⚫":
    color = "black"
  else:
    color = "red"

  await resolve_bets(ctx, guild_id, number, color)
  roulette_running[guild_id] = False


async def resolve_bets(ctx, guild_id, number, color):
  global roulette_bets

  if guild_id not in roulette_bets:
    await ctx.send(
        "Aucun pari n'a été placé lors de cette session de roulette.")
    return

  bets = roulette_bets.pop(guild_id)
  winnings = {}

  guild = bot.get_guild(guild_id)
  if guild is None:
    print("Le serveur n'a pas été trouvé.")
    return

  for user_id, bet_data in bets.items():
    user = guild.get_member(int(user_id))
    if user is None:
      await ctx.send(
          f"Impossible de trouver l'utilisateur avec l'ID {user_id}.")
      continue

    user_winnings = 0
    for bet_type, bet_amount, bet_value in bet_data:
      if bet_type == "number":
        if int(bet_value) == number:
          user_winnings += bet_amount * 36
        else:
          user_winnings -= bet_amount
      elif bet_type == "color":
        if bet_value.lower() == color.lower():
          if color.lower() == "green":
            user_winnings += bet_amount * 17
          else:
            user_winnings += bet_amount
        else:
          user_winnings -= bet_amount

    winnings[user_id] = user_winnings

    current_coins = get_coins(guild_id, user_id)
    new_coins = current_coins + user_winnings
    add_coins(guild_id, user_id, user_winnings)

  if color == "green":
    color = "🟩"
  elif color == "black":
    color = "⚫"
  else:
    color = "🟥"

  embed = discord.Embed(title="Résultats de la roulette",
                        color=discord.Color.gold())
  embed.add_field(name="Numéro", value=number, inline=True)
  embed.add_field(name="Couleur", value=color, inline=True)

  winners = [
      f"<@{user_id}>: {winnings[user_id]} pièces :coin:"
      for user_id in winnings if winnings[user_id] > 0
  ]
  losers = [
      f"<@{user_id}>: {-winnings[user_id]} pièces :coin:"
      for user_id in winnings if winnings[user_id] < 0
  ]

  if winners:
    embed.add_field(name="Gagnants", value="\n".join(winners), inline=False)

  if losers:
    embed.add_field(name="Perdants", value="\n".join(losers), inline=False)

  await ctx.send(embed=embed)


@bot.command()
async def bet(ctx, bet_type: str, amount: int, *args):
  global roulette_running
  guild_id = ctx.guild.id
  user_id = str(ctx.author.id)

  if guild_id not in roulette_running or not roulette_running[guild_id]:
    await ctx.send("Il n'y a pas de roulette en cours pour le moment.")
    return

  user_coins = get_coins(guild_id, user_id)
  if user_coins < amount:
    await ctx.send("Vous n'avez pas assez de pièces pour ce pari.")
    return

  if bet_type == "number":
    if len(args) != 1:
      await ctx.send("Vous devez spécifier un seul numéro sur lequel parier.")
      return

    chosen_number = args[0]
    if not chosen_number.isdigit() or int(chosen_number) < 0 or int(
        chosen_number) > 34:
      await ctx.send(
          "Numéro de pari invalide. Le numéro doit être compris entre 0 et 34."
      )
      return

    roulette_bets.setdefault(guild_id, {}).setdefault(user_id, []).append(
        (bet_type, amount, chosen_number))
    await ctx.send(
        f"Vous avez misé {amount} pièces sur le numéro {chosen_number}.")
  elif bet_type == "color":
    if amount <= 0 or amount > user_coins // 2:
      await ctx.send("Montant de pari invalide.")
      return

    if len(args) != 1:
      await ctx.send(
          "Vous devez spécifier une seule couleur sur laquelle parier.")
      return

    chosen_color = args[0].lower()
    if chosen_color not in ["red", "black", "green"]:
      await ctx.send(
          "Couleur de pari invalide. Les couleurs valides sont 'red', 'black' et 'green'."
      )
      return

    roulette_bets.setdefault(guild_id, {}).setdefault(user_id, []).append(
        (bet_type, amount, chosen_color))
    await ctx.send(
        f"Vous avez misé {amount} pièces sur la couleur {chosen_color}.")
  else:
    await ctx.send(
        "Type de pari invalide. Les types valides sont 'number' et 'color'.")


def add_coins(guild_id, user_id, amount):
  coins = load_coins(guild_id)
  if user_id in coins:
    coins[user_id] += amount
  else:
    coins[user_id] = amount
  save_coins(guild_id, coins)


def get_coins(guild_id, user_id):
  coins = load_coins(guild_id)
  return coins.get(user_id, 0)


@bot.command(name='coinflip')
async def coinflip(ctx):

  result = random.choice(['Pile', 'Face'])
  embed = discord.Embed(title='Lancer de pièce',
                        description=f'La pièce est tombée sur **{result}**!',
                        color=discord.Color.gold())
  coin_emoji = '🟡' if result == 'Pile' else '🪙'
  embed.add_field(name='Résultat',
                  value=f'{coin_emoji} {result}',
                  inline=False)
  await ctx.send(embed=embed)


@bot.command(name='dice')
async def roll_dice(ctx, faces: int = 6):

  if faces < 2:
    await ctx.send('Un dé doit avoir au moins 2 faces!')
    return

  result = random.randint(1, faces)
  embed = discord.Embed(title='Lancer de dé',
                        description=f'Le dé est tombé sur **{result}**!',
                        color=discord.Color.gold())
  embed.add_field(name='Résultat', value=f'🎲 {result}', inline=False)
  await ctx.send(embed=embed)


@bot.command()
async def machine(ctx, amount: int):
  guild_id = ctx.guild.id
  user_id = str(ctx.author.id)

  user_coins = get_coins(guild_id, user_id)
  if user_coins < amount:
    await ctx.send("Vous n'avez pas assez de pièces pour ce pari.")
    return

  if amount <= 0:
    await ctx.send("Le montant du pari doit être supérieur à zéro.")
    return

  emojis = ["🍒", "🍋", "🍊", "🍇", "🍉", "🍌", "🍎", "🍓", "🍏"]
  result = [random.choice(emojis) for _ in range(3)]

  embed = discord.Embed(title="Machine à sous", color=discord.Color.gold())
  embed.add_field(name="Résultat", value=' '.join(result), inline=False)

  winnings = 0

  if len(set(result)) == 1:
    winnings = amount * 8
    embed.add_field(name="Résultat",
                    value=f"Bravo! Vous avez gagné {winnings} pièces :coin:")
  elif len(set(result)) == 2:
    winnings = amount * 2
    embed.add_field(
        name="Résultat",
        value=f"Bien joué! Vous avez gagné {winnings} pièces :coin:")
  else:
    embed.add_field(name="Résultat",
                    value="Désolé, vous n'avez pas gagné cette fois.")

  add_coins(guild_id, user_id, winnings - amount)

  await ctx.send(embed=embed)


@bot.command()
async def battle(ctx, player_choice: str, amount: int):
  choices = ['rock', 'paper', 'scissors']
  emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
  computer_choice = random.choice(choices)

  user_id = str(ctx.author.id)
  user_coins = get_coins(ctx.guild.id, user_id)

  if amount < 100 or amount > 20000:
    await ctx.send("Le montant misé doit être compris entre 100 et 20000.")
    return

  if user_coins < amount:
    await ctx.send("Vous n'avez pas assez de pièces pour ce pari.")
    return

  result = ""
  if player_choice == computer_choice:
    result = "C'est une égalité !"
    winnings = 0
  elif (player_choice == 'rock' and computer_choice == 'scissors') or \
       (player_choice == 'paper' and computer_choice == 'rock') or \
       (player_choice == 'scissors' and computer_choice == 'paper'):
    result = "Vous avez gagné !"
    winnings = amount
  else:
    result = "Vous avez perdu !"
    winnings = -amount

  add_coins(ctx.guild.id, user_id, winnings)

  embed = discord.Embed(title="Résultat de la bataille",
                        color=discord.Color.gold())
  embed.add_field(name="Votre choix", value=emojis[player_choice], inline=True)
  embed.add_field(name="Choix de l'ordinateur",
                  value=emojis[computer_choice],
                  inline=True)
  embed.add_field(name="Résultat", value=result, inline=False)
  embed.add_field(name="Gains/Pertes",
                  value=f"{winnings} pièces :coin:",
                  inline=False)

  await ctx.send(embed=embed)


@bot.command()
async def help(ctx):

  embed = discord.Embed(
      title="Liste commande de SpinBot",
      url=
      "https://discord.com/oauth2/authorize?client_id=1227716254949707796&permissions=8&scope=bot+applications.commands",
      description=
      "```\n$setup - Setup le bot \n$money [user] - Affiche le nombre de pièces d'un user \n$roulette - Lance une partie de roulette \n$bet <color/number> <montant> <red;green;black/number> - Permet de parier sur une couleu ou un numéro dans une partie de roulette \n$coinflip - Lance une pièce virtuelle \n$dice [number] - Lance un dé avec un nombre spécifié de faces \n$machine <montant> - Joue à la machine à sous avec un montant spécifié \n$battle <rock/paper/scissors> <montant> - Joue à pierre-papier-ciseaux avec un montant spécifié \n$leaderboard - Affiche un classement des utilisateurs en fonction du nombre de pièces \n$addcoins <membre> <montant> - Ajoute un montant spécifié de pièces à un membre \n$removecoins <membre> <montant> - Retire un montant spécifié de pièces à un membre ```",
      colour=discord.Color.gold())

  embed.set_author(
      name="SpinBot",
      url=
      "https://discord.com/oauth2/authorize?client_id=1227716254949707796&permissions=8&scope=bot+applications.commands",
      icon_url=
      "https://cdn.discordapp.com/avatars/1227716254949707796/10d0d73af97dba509e61310b24958a79.webp?size=240"
  )

  embed.set_footer(
      text="@ewazer https://ewazer.com",
      icon_url=
      "https://cdn.discordapp.com/attachments/1228985803867426908/1229083563220013218/0_03.png?ex=662e6444&is=661bef44&hm=698d047885d27cd86315a9d924e02e99ca4a1f41481cf359412ad88bb127d4c0&"
  )

  await ctx.send(embed=embed)

@bot.command()
async def claim(ctx):
  guild_id = str(ctx.guild.id)
  user_id = str(ctx.author.id)

  daily_reward_data = load_daily_reward(guild_id)

  if not daily_reward_data["enabled"]:
    await ctx.send("La récompense quotidienne est désactivée sur ce serveur.")
    return
  
  last_claim_date = daily_reward_data.get(user_id)
  current_date = datetime.utcnow().strftime("%Y-%m-%d")
  if last_claim_date == current_date:
    await ctx.send(
        "Vous avez déjà réclamé votre récompense quotidienne pour aujourd'hui."
    )
    return

  reward_amount = daily_reward_data["reward_amount"]
  add_coins(guild_id, user_id, reward_amount)

  daily_reward_data[user_id] = current_date
  save_daily_reward(guild_id, daily_reward_data)

  await ctx.send(
      f"Félicitations ! Vous avez réclamé votre récompense quotidienne de {reward_amount} pièces :coin:"
  )


def load_daily_reward(guild_id):
  file_path = f"{guild_id}_daily_reward.json"
  if os.path.exists(file_path):
    with open(file_path, "r") as f:
      return json.load(f)
  else:

    default_data = {
        "reward_amount": 100,
    }
    return default_data

@bot.command()
async def setup_reward(ctx, amount_or_off):
    if not has_permissions(ctx) and not ctx.author.guild_permissions.administrator:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande. Vous pouvez gérer les permissions en effectuant la commande `$setup`.")
        return

    guild_id = str(ctx.guild.id)

    daily_reward_data = load_daily_reward(guild_id)

    if amount_or_off.lower() == "off":
        daily_reward_data["enabled"] = False
        save_daily_reward(guild_id, daily_reward_data)
        await ctx.send("La récompense quotidienne a été désactivée avec succès.")
    else:
        amount = int(amount_or_off)
        daily_reward_data["enabled"] = True
        daily_reward_data["reward_amount"] = amount
        save_daily_reward(guild_id, daily_reward_data)
        await ctx.send(f"La récompense quotidienne a été mise à jour avec succès à {amount} pièces :coin:")



def save_daily_reward(guild_id, data):
  file_path = f"{guild_id}_daily_reward.json"
  with open(file_path, "w") as f:
    json.dump(data, f, indent=4)

@battle.error
async def battle_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send(
        "Utilisation : $battle <rock> or <paper> or <scissors> <bet>.")
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        "Argument invalide. Utilisation : $battle <rock> or <paper> or <scissors> <bet>."
    )
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@machine.error
async def machine_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $machine <montant>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $machine <montant>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@roll_dice.error
async def roll_dice_command_error(ctx, error):
  if isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $dice <number>.")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@bet.error
async def bet_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send(
        "Utilisation : $bet <color/number> <montant> <red;green;black/number>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        "Argument invalide. Utilisation : $addcoins <membre> <montant>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@addcoins.error
async def addcoins_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $addcoins <membre> <montant>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        "Argument invalide. Utilisation : $addcoins <membre> <montant>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@removecoins.error
async def removecoins_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $removecoins <membre> <montant>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send(
        "Argument invalide. Utilisation : $removecoins <membre> <montant>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@adduser.error
async def adduser_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $adduser <membre>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $adduser <membre>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@addrole.error
async def addrole_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $addrole <role>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $addrole <role>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@removeuser.error
async def removeuser_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $removeuser <membre>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $removeuser <membre>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@removerole.error
async def removerole_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Utilisation : $removerole <role>")
  elif isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $removerole <role>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@money.error
async def money_command_error(ctx, error):
  if isinstance(error, commands.BadArgument):
    await ctx.send("Argument invalide. Utilisation : $money <user>")
  else:
    await ctx.send(
        "Une erreur est survenue lors de l'exécution de la commande.")


@coinflip.error
@roulette.error
@allowed.error
@setup.error
@help.error
@claim.error
@setup_reward.error
async def leaderboard_command_error(ctx, error):
  await ctx.send("Une erreur est survenue lors de l'exécution de la commande.")

bot.run(os.environ['TOKEN'])

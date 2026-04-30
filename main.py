import os
import discord
import functools
import random
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=1495300890821791824)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild.")
    except Exception as e:
        print(f"Failed to sync: {e}")
    print("Bot Ready")
# How to get the bot to give a user a role on button click
ROLE_ID = 123456789012345678  # replace with your role ID

class RoleView(discord.ui.View):

    @discord.ui.button(label="Get Role", style=discord.ButtonStyle.success)
    async def get_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(ROLE_ID)
        user = interaction.user

        if role in user.roles:
            await interaction.response.send_message("You already have this role!", ephemeral=True)
        else:
            await user.add_roles(role)
            await interaction.response.send_message("Role added!", ephemeral=True)

@bot.command()
async def rolebutton(ctx):
    await ctx.send("Click to get the role:", view=RoleView())
# --- SCRIM SYSTEM ---

def generate_scrim_code():
    return f"SCRIM{random.randint(100, 999)}"

def build_scrim_embed(team_size: int, team1: list, team2: list, ref, code, winner) -> discord.Embed:
    embed = discord.Embed(
        title="⚔️ Scrim Lobby",
        description=f"Join a team below! Teams are **{team_size}v{team_size}**.",
        color=discord.Color.red() if winner else discord.Color.blue()
    )

    def team_value(team, size):
        lines = [f"• {m.display_name}" for m in team]
        spots = size - len(team)
        if spots > 0:
            lines.append(f"_{spots} spot(s) remaining_")
        return "\n".join(lines) if lines else "_Empty_"

    embed.add_field(name=f"🔵 Team 1 ({len(team1)}/{team_size})", value=team_value(team1, team_size), inline=True)
    embed.add_field(name=f"🔴 Team 2 ({len(team2)}/{team_size})", value=team_value(team2, team_size), inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    ref_val = ref.display_name if ref else "_No ref yet_"
    embed.add_field(name="🟡 Referee", value=ref_val, inline=False)

    if winner:
        embed.add_field(name="🏆 Result", value=f"**{winner}** wins!", inline=False)
        embed.set_footer(text="Scrim over!")
    elif code:
        embed.add_field(name="🔑 Scrim Code", value=f"||`{code}`||", inline=False)
        embed.set_footer(text="Teams are full! Code DMed to all players. Good luck!")
    else:
        embed.set_footer(text="Waiting for players...")

    return embed


class ScrimView(discord.ui.View):
    def __init__(self, team_size: int, creator_id: int):
        super().__init__(timeout=None)
        self.team_size = team_size
        self.team1: list[discord.Member] = []
        self.team2: list[discord.Member] = []
        self.ref: discord.Member | None = None
        self.code: str | None = None
        self.winner: str | None = None
        self.creator_id = creator_id
        self.locked = False

    def all_players(self):
        return self.team1 + self.team2 + ([self.ref] if self.ref else [])

    def is_full(self):
        return len(self.team1) == self.team_size and len(self.team2) == self.team_size

    def assign_team(self, member: discord.Member) -> str:
        if len(self.team1) < self.team_size and len(self.team2) < self.team_size:
            chosen = random.choice(["team1", "team2"])
        elif len(self.team1) < self.team_size:
            chosen = "team1"
        else:
            chosen = "team2"

        if chosen == "team1":
            self.team1.append(member)
        else:
            self.team2.append(member)
        return chosen

    async def refresh(self, interaction: discord.Interaction):
        """Always edits the original scrim message regardless of which button was clicked."""
        embed = build_scrim_embed(self.team_size, self.team1, self.team2, self.ref, self.code, self.winner)
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Join Scrim", style=discord.ButtonStyle.green, emoji="⚔️", custom_id="scrim_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if self.locked:
            await interaction.response.send_message("❌ The scrim is already full!", ephemeral=True)
            return

        if member in self.all_players():
            await interaction.response.send_message("❌ You've already joined this scrim!", ephemeral=True)
            return

        team = self.assign_team(member)
        team_name = "🔵 Team 1" if team == "team1" else "🔴 Team 2"

        if self.is_full():
            self.locked = True
            self.code = generate_scrim_code()
            self.join.disabled = True
            for p in self.team1 + self.team2:
                try:
                    await p.send(f"🔑 Your scrim code is: `{self.code}`\nGood luck!")
                except discord.Forbidden:
                    pass

        # Defer first, then edit the original message, then send ephemeral follow-up
        await interaction.response.defer()
        await self.refresh(interaction)
        await interaction.followup.send(f"✅ You've been assigned to **{team_name}**!", ephemeral=True)

    @discord.ui.button(label="Leave Scrim", style=discord.ButtonStyle.red, emoji="🚪", custom_id="scrim_leave")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if member in self.team1:
            self.team1.remove(member)
        elif member in self.team2:
            self.team2.remove(member)
        elif member == self.ref:
            self.ref = None
            await interaction.response.defer()
            await self.refresh(interaction)
            await interaction.followup.send("✅ You've stepped down as referee.", ephemeral=True)
            return
        else:
            await interaction.response.send_message("❌ You're not in this scrim.", ephemeral=True)
            return

        if self.locked:
            self.locked = False
            self.code = None
            self.join.disabled = False

        await interaction.response.defer()
        await self.refresh(interaction)
        await interaction.followup.send("✅ You've left the scrim.", ephemeral=True)

    @discord.ui.button(label="Be a Ref", style=discord.ButtonStyle.blurple, emoji="🟡", custom_id="scrim_ref")
    async def become_ref(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user

        if member in self.team1 or member in self.team2:
            await interaction.response.send_message("❌ You can't be a ref while on a team. Leave your team first.", ephemeral=True)
            return
        if self.ref is not None and self.ref != member:
            await interaction.response.send_message(f"❌ {self.ref.display_name} is already the ref.", ephemeral=True)
            return
        if self.ref == member:
            await interaction.response.send_message("❌ You're already the ref!", ephemeral=True)
            return

        self.ref = member
        await interaction.response.defer()
        await self.refresh(interaction)
        await interaction.followup.send("✅ You're now the referee!", ephemeral=True)

    @discord.ui.button(label="Team 1 Wins", style=discord.ButtonStyle.grey, emoji="🏆", custom_id="scrim_win1")
    async def team1_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ref:
            await interaction.response.send_message("❌ Only the referee can log the winner.", ephemeral=True)
            return
        if not self.locked:
            await interaction.response.send_message("❌ The scrim hasn't started yet (teams aren't full).", ephemeral=True)
            return

        self.winner = "🔵 Team 1"
        for child in self.children:
            child.disabled = True

        await interaction.response.defer()
        await self.refresh(interaction)
        await interaction.followup.send("✅ Result logged: **🔵 Team 1** wins!", ephemeral=True)

    @discord.ui.button(label="Team 2 Wins", style=discord.ButtonStyle.grey, emoji="🏆", custom_id="scrim_win2")
    async def team2_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ref:
            await interaction.response.send_message("❌ Only the referee can log the winner.", ephemeral=True)
            return
        if not self.locked:
            await interaction.response.send_message("❌ The scrim hasn't started yet (teams aren't full).", ephemeral=True)
            return

        self.winner = "🔴 Team 2"
        for child in self.children:
            child.disabled = True

        await interaction.response.defer()
        await self.refresh(interaction)
        await interaction.followup.send("✅ Result logged: **🔴 Team 2** wins!", ephemeral=True)

@bot.command(name="scrim")
async def scrim(ctx, team_size: int):
    if team_size not in (3, 4):
        await ctx.send("❌ Invalid team size. Use `3` for 3v3 or `4` for 4v4.")
        return

    view = ScrimView(team_size=team_size, creator_id=ctx.author.id)
    embed = build_scrim_embed(team_size, [], [], None, None, None)
    await ctx.send(
        content="@here 🎮 A scrim is starting! Click below to join.",
        embed=embed,
        view=view
    )

bot.run(os.getenv("DISCORD_TOKEN"))

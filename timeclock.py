import discord
from discord import ui, app_commands
from discord.ext import commands, tasks
import json
import os
import datetime

DATA_FILE = "/home/container/data/activity_data.json"
LOGO_URL = "https://media.discordapp.net/attachments/1342569230339670086/1400853213539729428/cc2356a6-f64e-4178-8c07-7df0d5f0f930-removebg-preview.png"
IMAGE_URL = "https://media.discordapp.net/attachments/1342569230339670086/1428466536783544413/Gemini_Generated_Image_nqb14wnqb14wnqb1_2.png"
LOG_CHANNEL_ID = 1428471793496358942
NOTIFICATION_COOLDOWN_HOURS = 6
AFK_CHECK_HOURS = 3
AFK_RESPONSE_MINUTES = 10
AFK_LOG_PING_ROLE_ID = 1342569119869829123
ROLE_GOALS = {
    1342569124554866801: {"name": "Helper", "seconds": 30 * 60},
    1342569120981454868: {"name": "Admin", "seconds": 90 * 60},
    1342569121736294505: {"name": "Moderator", "seconds": 60 * 60},
    1401918325235388497: {"name": "Trainee", "seconds": 25 * 60}
}

def get_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def format_duration(total_seconds: float, simple: bool = False) -> str:
    if total_seconds < 0: total_seconds = 0
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if simple:
        return f"{total_seconds // 60}"
    if hours > 0: return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0: return f"{minutes}m {seconds}s"
    else: return f"{seconds}s"

def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "currently_clocked_in": {},
                "time_logs": {},
                "last_quota_notification": {},
                "afk_check_sent": {}
            }, f, indent=4)

class AFKCheckView(ui.View):
    def __init__(self, member: discord.Member, bot_instance):
        super().__init__(timeout=AFK_RESPONSE_MINUTES * 60)
        self.member = member
        self.bot = bot_instance
        self.responded = False

    @ui.button(label="Yes, I'm active!", style=discord.ButtonStyle.green, custom_id="afk_confirm_yes")
    async def confirm_active(self, interaction: discord.Interaction, button: ui.Button):
        self.responded = True
        await interaction.response.send_message("Thanks for confirming! Your activity log continues.", ephemeral=True)
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(view=self)
        self.stop()

    async def on_timeout(self):
        if self.responded:
            return

        data = get_data()
        user_id = str(self.member.id)

        if user_id not in data.get("currently_clocked_in", {}):
            return

        start_time_iso = data["currently_clocked_in"].pop(user_id)
        start_time = datetime.datetime.fromisoformat(start_time_iso)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = end_time - start_time

        if user_id not in data["time_logs"]:
            data["time_logs"][user_id] = []
        
        log_entry = {"start": start_time.isoformat(), "end": end_time.isoformat(), "duration_seconds": duration.total_seconds()}
        data["time_logs"][user_id].append(log_entry)
        
        if user_id in data.get("afk_check_sent", {}):
            del data["afk_check_sent"][user_id]
        save_data(data)

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="🚨 Activity Stopped Due to Inactivity (AFK)",
                description=f"The activity of {self.member.mention} was automatically stopped due to no response to the check.\n\n"
                            f"**Possible AFK.** <@&{AFK_LOG_PING_ROLE_ID}>",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            await log_channel.send(embed=log_embed)

class ActivityPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Clock In", style=discord.ButtonStyle.green, custom_id="clock_in_button")
    async def clock_in(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        data = get_data()
        if user_id in data["currently_clocked_in"]:
            await interaction.response.send_message("❌ You have already clocked in!", ephemeral=True)
            return
        start_time = datetime.datetime.now(datetime.timezone.utc)
        data["currently_clocked_in"][user_id] = start_time.isoformat()
        save_data(data)
        embed = discord.Embed(title="✅ Activity Started", description="Your activity session has begun. Thank you for your dedication!", color=discord.Color.green())
        embed.add_field(name="Start Time", value=f"<t:{int(start_time.timestamp())}:F>")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="Clock Out", style=discord.ButtonStyle.red, custom_id="clock_out_button")
    async def clock_out(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        data = get_data()
        if user_id not in data["currently_clocked_in"]:
            await interaction.response.send_message("❌ You need to clock in first!", ephemeral=True)
            return
        start_time_iso = data["currently_clocked_in"].pop(user_id)
        start_time = datetime.datetime.fromisoformat(start_time_iso)
        end_time = datetime.datetime.now(datetime.timezone.utc)
        duration = end_time - start_time
        if user_id not in data["time_logs"]:
            data["time_logs"][user_id] = []
        log_entry = {"start": start_time.isoformat(), "end": end_time.isoformat(), "duration_seconds": duration.total_seconds()}
        data["time_logs"][user_id].append(log_entry)
        save_data(data)
        embed = discord.Embed(title="✅ Activity Finished", description="Your activity session has ended. We appreciate your time!", color=discord.Color.red())
        embed.add_field(name="Session Duration", value=format_duration(duration.total_seconds()))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="My Info", style=discord.ButtonStyle.secondary, custom_id="my_info_button")
    async def my_info(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        member = interaction.user
        data = get_data()
        user_logs = data["time_logs"].get(user_id, [])
        if not user_logs:
            await interaction.response.send_message("You don't have any activity records yet.", ephemeral=True)
            return
        total_seconds_worked = sum(log["duration_seconds"] for log in user_logs)
        
        embed = discord.Embed(title="Your Activity Time", color=discord.Color.blue())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Total Dedicated Time", value=f"**{format_duration(total_seconds_worked)}**", inline=False)
        
        goals_text = ""
        user_role_ids = [role.id for role in member.roles]
        for role_id, info in ROLE_GOALS.items():
            if role_id in user_role_ids:
                goal_seconds = info["seconds"]
                progress_percent = (total_seconds_worked / goal_seconds) * 100 if goal_seconds > 0 else 100
                time_worked_str = format_duration(total_seconds_worked)
                goal_time_str = format_duration(goal_seconds)
                goals_text += f"<@&{role_id}>: `{time_worked_str} / {goal_time_str}` **({progress_percent:.1f}%)**\n"
        
        if not goals_text:
            goals_text = "You do not have a role with an activity goal."
        embed.add_field(name="Activity Goals", value=goals_text, inline=False)
        
        recent_sessions_text = ""
        for log in reversed(user_logs[-5:]):
            start_ts = int(datetime.datetime.fromisoformat(log["start"]).timestamp())
            duration_str = format_duration(log["duration_seconds"])
            recent_sessions_text += f"• <t:{start_ts}:d> - Duration: `{duration_str}`\n"
        if recent_sessions_text:
            embed.add_field(name="Recent Sessions", value=recent_sessions_text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="Top Staff", style=discord.ButtonStyle.secondary, custom_id="top_staff_button")
    async def top_3_staff(self, interaction: discord.Interaction, button: ui.Button):
        data = get_data()
        time_logs = data.get("time_logs", {})
        if not time_logs:
            await interaction.response.send_message("There are no activity records yet to generate a ranking.", ephemeral=True)
            return
        staff_totals = {user_id: sum(log["duration_seconds"] for log in logs) for user_id, logs in time_logs.items()}
        sorted_staff = sorted(staff_totals.items(), key=lambda item: item[1], reverse=True)
        embed = discord.Embed(title="Top 3 Staff", description="Ranking based on total recorded activity time.", color=discord.Color.gold())
        description_text = ""
        rank_emojis = ["🥇", "🥈", "🥉"]
        for i, (user_id, total_seconds) in enumerate(sorted_staff[:3]):
            rank_emoji = rank_emojis[i]
            duration_str = format_duration(total_seconds)
            description_text += f"{rank_emoji} <@{user_id}> - `{duration_str}`\n"
        if not description_text:
            description_text = "No staff members with enough time for the ranking."
        embed.description = description_text
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ActivityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        ensure_data_file()
        self.bot.add_view(ActivityPanelView())
        self.check_staff_quotas.start()
        self.check_afk_staff.start()

    def cog_unload(self):
        self.check_staff_quotas.cancel()
        self.check_afk_staff.cancel()

    @tasks.loop(hours=1)
    async def check_staff_quotas(self):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel: return

        guild = log_channel.guild
        data = get_data()
        if "last_quota_notification" not in data:
            data["last_quota_notification"] = {}

        clocked_in_users = data.get("currently_clocked_in", {}).keys()
        time_logs = data.get("time_logs", {})
        last_notifications = data.get("last_quota_notification", {})
        
        target_role_ids = set(ROLE_GOALS.keys())
        members_to_notify = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for member in guild.members:
            if member.bot or str(member.id) in clocked_in_users: continue

            member_role_ids = {role.id for role in member.roles}
            if not target_role_ids.intersection(member_role_ids): continue
            
            last_notif_iso = last_notifications.get(str(member.id))
            if last_notif_iso:
                last_notif_time = datetime.datetime.fromisoformat(last_notif_iso)
                if (now - last_notif_time).total_seconds() < NOTIFICATION_COOLDOWN_HOURS * 3600: continue
            
            total_seconds_worked = sum(log["duration_seconds"] for log in time_logs.get(str(member.id), []))
            
            unmet_quotas = []
            for role_id, info in ROLE_GOALS.items():
                if role_id in member_role_ids and total_seconds_worked < info["seconds"]:
                    unmet_quotas.append(info)
            
            if unmet_quotas:
                members_to_notify.append((member, total_seconds_worked, unmet_quotas))

        if not members_to_notify: return

        log_embed = discord.Embed(title="📢 Activity Goal Reminder", description="The following team members have been notified:", color=discord.Color.orange(), timestamp=now)
        notified_list_log = []

        for member, worked_seconds, quotas in members_to_notify:
            dm_desc = "Hello! This is a friendly reminder about your voluntary activity goals:\n\n"
            for quota_info in quotas:
                worked_min = format_duration(worked_seconds, simple=True)
                goal_min = format_duration(quota_info["seconds"], simple=True)
                dm_desc += f"• **{quota_info['name']}**: `{worked_min} / {goal_min}` minutes\n"
            dm_desc += "\nUse the panel to **clock in** and continue contributing to the community."

            dm_embed = discord.Embed(title="👋 Activity Reminder", description=dm_desc, color=discord.Color.orange())
            dm_embed.set_footer(text=f"Server: {guild.name}")
            
            try:
                await member.send(embed=dm_embed)
                notified_list_log.append(f"✅ {member.mention} (DM sent)")
                data["last_quota_notification"][str(member.id)] = now.isoformat()
            except discord.Forbidden:
                notified_list_log.append(f"❌ {member.mention} (DMs blocked)")

        if notified_list_log:
            log_embed.add_field(name="Notified Members", value="\n".join(notified_list_log), inline=False)
            await log_channel.send(embed=log_embed)
            save_data(data)

    @check_staff_quotas.before_loop
    async def before_check_quotas(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def check_afk_staff(self):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel: return
        
        guild = log_channel.guild
        data = get_data()
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for user_id, start_iso in data.get("currently_clocked_in", {}).copy().items():
            if user_id in data.get("afk_check_sent", {}): continue

            start_time = datetime.datetime.fromisoformat(start_iso)
            duration = now - start_time
            
            if duration.total_seconds() > AFK_CHECK_HOURS * 3600:
                member = guild.get_member(int(user_id))
                if not member: continue

                dm_embed = discord.Embed(
                    title="🤔 Activity Check",
                    description="Hello! Your activity log has been active for over 3 hours. Are you still there?",
                    color=discord.Color.yellow()
                )
                try:
                    view = AFKCheckView(member, self.bot)
                    await member.send(embed=dm_embed, view=view)
                    
                    data["afk_check_sent"][user_id] = True
                    save_data(data)
                except discord.Forbidden:
                    print(f"Could not send AFK check to {member.name} (DMs are closed).")

    @check_afk_staff.before_loop
    async def before_check_afk(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="viewactivity", description="Views the activity information of a staff member.")
    @app_commands.describe(member="The member you want to check.")
    @app.commands.checks.has_permissions(manage_guild=True)
    async def view_activity(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(member.id)
        data = get_data()
        user_logs = data["time_logs"].get(user_id, [])

        if not user_logs:
            await interaction.followup.send(f"{member.mention} does not have any activity records yet.")
            return

        total_seconds_worked = sum(log["duration_seconds"] for log in user_logs)

        embed = discord.Embed(title=f"Activity Time for {member.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Total Dedicated Time", value=f"**{format_duration(total_seconds_worked)}**", inline=False)

        goals_text = ""
        user_role_ids = [role.id for role in member.roles]
        for role_id, info in ROLE_GOALS.items():
            if role_id in user_role_ids:
                goal_seconds = info["seconds"]
                progress_percent = (total_seconds_worked / goal_seconds) * 100 if goal_seconds > 0 else 100
                time_worked_str = format_duration(total_seconds_worked)
                goal_time_str = format_duration(goal_seconds)
                goals_text += f"<@&{role_id}>: `{time_worked_str} / {goal_time_str}` **({progress_percent:.1f}%)**\n"

        if not goals_text:
            goals_text = "This member does not have a role with an activity goal."
        embed.add_field(name="Activity Goals", value=goals_text, inline=False)

        recent_sessions_text = ""
        for log in reversed(user_logs[-5:]):
            start_ts = int(datetime.datetime.fromisoformat(log["start"]).timestamp())
            duration_str = format_duration(log["duration_seconds"])
            recent_sessions_text += f"• <t:{start_ts}:d> - Duration: `{duration_str}`\n"
        if recent_sessions_text:
            embed.add_field(name="Recent Sessions", value=recent_sessions_text, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="activitypanel", description="Creates the team activity panel in the current channel.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def create_activity_panel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = discord.Embed(
            title="Team Activity Hub",
            description="Use the buttons below to log your volunteer activity in the community.\n\n"
                        "We appreciate your collaboration and patience!",
            color=0x2b2d31
        )
        embed.set_thumbnail(url=LOGO_URL)
        embed.add_field(
            name="How does it work?",
            value="• **Clock In:** Click when you start your activity.\n"
                  "• **Clock Out:** Click when you finish your activity.\n"
                  "• **My Info:** View your total time and recent sessions.\n"
                  "• **Top Staff:** Shows the ranking of the most active members.",
            inline=False
        )
        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text="© Your Server Name. All rights reserved.")
        await interaction.channel.send(embed=embed, view=ActivityPanelView())
        await interaction.followup.send("✅ Activity panel created successfully!", ephemeral=True)


async def setup(bot: commands.eBot):
    await bot.add_cog(ActivityCog(bot))

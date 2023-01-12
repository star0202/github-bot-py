from logging import getLogger

from discord import ApplicationContext, Embed, Interaction  # noqa
from discord.ext import commands  # noqa
from discord.ui import Modal, InputText  # noqa
from github import Github

from config import COLOR, BAD
from utils.bot import Bot
from utils.commands import slash_command

logger = getLogger(__name__)


class RegisterModal(Modal):
    def __init__(self, bot: Bot):
        super().__init__(title="Github 계정 등록")
        self.bot = bot
        self.add_item(InputText(label="Github 토큰", placeholder="Personal Access Token"))

    async def callback(self, interaction: Interaction):
        token = await self.bot.crypt.encrypt(self.children[0].value)
        await self.bot.db.insert("User", (interaction.user.id, str(token)))
        embed = Embed(title="성공", description="Github 계정이 연동되었습니다!", color=COLOR)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class GithubCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @slash_command(name="연동", description="토큰을 사용해 깃허브 계정을 연동합니다.")
    async def register(self, ctx: ApplicationContext):
        if await self.bot.db.select("User", ctx.user.id):
            embed = Embed(title="오류", description="이미 연동된 계정이 있습니다. 연동을 해제하려면 `/연동해제`를 입력해주세요.", color=BAD)
            await ctx.respond(embed=embed)
            return
        await ctx.send_modal(RegisterModal(self.bot))

    @slash_command(name="연동해제", description="깃허브 계정 연동을 해제합니다.")
    async def unregister(self, ctx: ApplicationContext):
        if not await self.bot.db.select("User", ctx.user.id):
            embed = Embed(title="오류", description="연동된 계정이 없습니다. 연동을 하려면 `/연동`을 입력해주세요.", color=BAD)
            await ctx.respond(embed=embed)
            return
        await self.bot.db.delete("User", ctx.user.id)
        embed = Embed(title="성공", description="Github 계정 연동이 해제되었습니다.", color=COLOR)
        await ctx.respond(embed=embed, ephemeral=True)

    @slash_command(name="연동정보", description="깃허브 계정 연동 정보를 확인합니다.")
    async def info(self, ctx: ApplicationContext):
        data = await self.bot.db.select("User", ctx.user.id)
        if data:
            token = await self.bot.crypt.decrypt(data[1])
            github = Github(token)
            user = github.get_user()
            embed = Embed(
                title="연동된 계정",
                description=f"**{user.name}([{user.login}](https://github.com/{user.login}))**",
                color=COLOR
            )
        else:
            embed = Embed(title="오류", description="연동된 계정이 없습니다. 연동을 하려면 `/연동`을 입력해주세요.", color=BAD)
        await ctx.respond(embed=embed)


def setup(bot):
    logger.info("Loaded")
    bot.add_cog(GithubCog(bot))


def teardown():
    logger.info("Unloaded")

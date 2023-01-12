from logging import getLogger

from discord import ApplicationContext, Embed, Interaction, Option, ButtonStyle  # noqa
from discord.ext import commands  # noqa
from discord.ui import Modal, InputText, button, Button, View  # noqa
from github import Github
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser

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


class RegisterRecommend(View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.id = self.bot.get_application_command('연동').id

    @button(label="계정 연동하기", style=ButtonStyle.primary)
    async def register(self, _, interaction: Interaction):
        await interaction.response.edit_message(content=f"</연동:{self.id}>", embed=None)


class UserControl(View):
    def __init__(self, me: AuthenticatedUser, user: NamedUser):
        super().__init__(timeout=60)
        self.me = me
        self.user = user
        self.add_item(Button(label="🔗", url=user.html_url, style=ButtonStyle.url))

    @button(label="💜", style=ButtonStyle.red)
    async def follow(self, _, interaction: Interaction):
        if self.user in self.me.get_following():
            self.me.remove_from_following(self.user)
            await interaction.response.send_message("팔로우 취소됨", ephemeral=True)
        else:
            self.me.add_to_following(self.user)
            await interaction.response.send_message("팔로우됨", ephemeral=True)


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
                description=f"{user.name}([{user.login}]({user.html_url}))",
                color=COLOR
            )
        else:
            embed = Embed(title="오류", description="연동된 계정이 없습니다. 연동을 하려면 `/연동`을 입력해주세요.", color=BAD)
        await ctx.respond(embed=embed)

    @slash_command(name="유저", description="깃허브 유저 정보를 확인합니다.")
    async def user_info(
            self, ctx: ApplicationContext, user_id: Option(
                str, name="아이디", description="확인할 유저의 아이디를 입력해주세요.")
    ):
        data = await self.bot.db.select("User", ctx.user.id)
        if data:
            token = await self.bot.crypt.decrypt(data[1])
            github = Github(token)
            view = UserControl(github.get_user(), github.get_user(user_id))
        else:
            github = Github()
            view = RegisterRecommend(self.bot)
        user = github.get_user_by_id(github.get_user(user_id).id)
        embed = Embed(title="유저 정보", color=COLOR)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="이름", value=f"{user.name}([{user.login}]({user.html_url}))")
        embed.add_field(name="팔로워 / 팔로잉", value=f"{user.followers} / {user.following}(명)")
        embed.add_field(name="공개 레포지토리", value=f"{user.public_repos}개")
        embed.add_field(name="소개", value=user.bio)
        await ctx.respond(embed=embed, view=view)

    @slash_command(name="레포", description="깃허브 레포 정보를 확인합니다.")
    async def repo_info(
            self, ctx: ApplicationContext,
            repo_owner: Option(
                str, name="소속", description="확인할 레포의 소속을 입력해주세요."),
            repo_name: Option(
                str, name="이름", description="확인할 레포의 이름을 입력해주세요.")
    ):
        data = await self.bot.db.select("User", ctx.user.id)
        if data:
            token = await self.bot.crypt.decrypt(data[1])
            github = Github(token)
        else:
            github = Github()
            view = RegisterRecommend(self.bot)
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        embed = Embed(title="레포 정보", color=COLOR)
        embed.add_field(name="이름", value=f"{repo.name}([{repo.owner.login}]({repo.html_url}))")
        embed.add_field(name="언어", value=repo.language)
        embed.add_field(name="설명", value=repo.description)
        embed.add_field(name="스타", value=f"{repo.stargazers_count}개")
        await ctx.respond(embed=embed)


def setup(bot):
    logger.info("Loaded")
    bot.add_cog(GithubCog(bot))

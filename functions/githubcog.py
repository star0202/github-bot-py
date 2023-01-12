from logging import getLogger

from discord import ApplicationContext, Option
from discord.ext import commands
from github import Github
from github.GithubException import UnknownObjectException

from config import BAD
from utils.commands import slash_command
from views.githubview import *

logger = getLogger(__name__)


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
        embed.add_field(name="팔로워 / 팔로잉", value=f"{user.followers} / {user.following} (명)")
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
            view = RepoControl(github.get_user(), github.get_repo(f"{repo_owner}/{repo_name}"))
        else:
            github = Github()
            view = RegisterRecommend(self.bot)
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        embed = Embed(title="레포 정보", color=COLOR)
        embed.add_field(name="이름", value=f"{repo.name}([{repo.owner.login}]({repo.html_url}))")
        embed.add_field(name="언어", value=repo.language
                        ) if repo.language else embed.add_field(name="언어", value="알 수 없음")
        embed.add_field(name="설명", value=repo.description)
        embed.add_field(name="스타", value=f"{repo.stargazers_count}개")
        embed.add_field(name="포크", value=f"{repo.forks_count}개")
        embed.add_field(name="PR", value=f"{len(list(repo.get_pulls()))}개")
        embed.add_field(name="이슈", value=f"{repo.open_issues_count}개")
        try:
            license_name = repo.get_license().license.name
        except UnknownObjectException:
            license_name = "없음"
        embed.add_field(name="라이선스", value=license_name)
        await ctx.respond(embed=embed, view=view)


def setup(bot):
    logger.info("Loaded")
    bot.add_cog(GithubCog(bot))

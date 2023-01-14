from logging import getLogger

from discord import ApplicationContext, Embed, Option
from discord.ext import commands
from github import Github
from github.GithubException import UnknownObjectException
from github.Repository import Repository
from github.NamedUser import NamedUser

from config import BAD, COLOR
from utils.bot import Bot
from utils.commands import slash_command
from views.githubview import RegisterModal, RepoControl, UserControl
from utils.utils import if_none_return
from utils.githubutils import is_user

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
        else:
            github = Github()
        user = github.get_user_by_id(github.get_user(user_id).id)
        view = UserControl(self.bot, github.get_user(), user)
        embed = Embed(title="유저 정보", color=COLOR)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="이름", value=f"{user.name}([{user.login}]({user.html_url}))")
        embed.add_field(name="팔로워 / 팔로잉", value=f"{user.followers} / {user.following} (명)")
        embed.add_field(name="공개 레포지토리", value=f"{user.public_repos}개")
        embed.add_field(name="소개", value=if_none_return(user.bio, "없음"))
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
        view = RepoControl(self.bot, github.get_user(), github.get_repo(f"{repo_owner}/{repo_name}"))
        repo = github.get_repo(f"{repo_owner}/{repo_name}")
        embed = Embed(title="레포 정보", color=COLOR)
        embed.add_field(name="이름", value=f"{repo.owner.login}/[{repo.name}]({repo.html_url})")
        embed.add_field(name="언어", value=if_none_return(repo.language, "없음"))
        embed.add_field(name="설명", value=if_none_return(repo.description, "없음"))
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

    @slash_command(name="검색", description="깃허브 유저 또는 레포를 검색합니다.")
    async def search(self, ctx: ApplicationContext, query: Option(str, name="검색어", description="검색할 내용을 입력해주세요.")):
        data = await self.bot.db.select("User", ctx.user.id)
        if data:
            token = await self.bot.crypt.decrypt(data[1])
            github = Github(token)
        else:
            github = Github()
        embed = Embed(title="검색 결과", color=COLOR)
        user = ""
        repo = ""
        user_searched = github.search_users(query)
        repo_searched = github.search_repositories(query)
        for i in range(3):
            try:
                u: NamedUser = user_searched[i]
                r: Repository = repo_searched[i]
                user += f"\n{if_none_return(u.name, u.login)}([{u.login}]({u.html_url}))"
                repo += f"\n{r.owner.login}/[{r.name}]({r.html_url})"
            except IndexError:
                pass
        embed.add_field(name="유저", value=user)
        embed.add_field(name="레포", value=repo)
        await ctx.respond(embed=embed)


def setup(bot: Bot):
    logger.info("Loaded")
    bot.add_cog(GithubCog(bot))

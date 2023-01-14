from discord import ButtonStyle, Embed, Interaction, PartialEmoji
from discord.ui import button, Button, InputText, Modal, View
from github import Github
from github.AuthenticatedUser import AuthenticatedUser
from github.GithubException import BadCredentialsException, GithubException
from github.NamedUser import NamedUser
from github.Organization import Organization
from github.Repository import Repository

from config import COLOR
from utils.bot import Bot
from utils.githubutils import is_user


class RegisterModal(Modal):
    def __init__(self, bot: Bot):
        super().__init__(title="Github 계정 등록")
        self.bot = bot
        self.add_item(InputText(label="Github 토큰", placeholder="Personal Access Token"))

    async def callback(self, interaction: Interaction):
        token = self.children[0].value
        try:
            github = Github(token)
            me = github.get_user()
            embed = Embed(title="성공", description=f"Github 계정이 연동되었습니다!\n연동된 계정: {me.login}", color=COLOR)
            token_encrypted = await self.bot.crypt.encrypt(self.children[0].value)
            await self.bot.db.insert("User", (interaction.user.id, str(token_encrypted)))
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except BadCredentialsException:
            await interaction.response.send_message("잘못된 토큰입니다.", ephemeral=True)


class RequireRegisterView(View):
    def __init__(self, bot: Bot, me: AuthenticatedUser):
        super().__init__(timeout=60)
        self.bot = bot
        self.me = me
        try:
            self.login = bool(me.login)
        except GithubException:
            self.login = False
        self.register = self.bot.get_application_command('연동').id

    @button(style=ButtonStyle.primary, label="연동", custom_id="register")
    async def register(self, _, interaction: Interaction):
        if self.login:
            return await interaction.response.send_message("이미 연동되어 있습니다.", ephemeral=True)
        await interaction.response.send_message(f"</연동:{self.register}>", ephemeral=True)


class UserControl(RequireRegisterView):
    def __init__(self, bot: Bot, me: AuthenticatedUser, user: NamedUser | Organization):
        super().__init__(bot, me)
        self.user = user
        self.add_item(Button(label="🔗", url=user.html_url, style=ButtonStyle.url))

    @button(style=ButtonStyle.blurple, label="💜", custom_id="follow")
    async def follow(self, _, interaction: Interaction):
        if not self.login:
            return await interaction.response.send_message("계정을 연동해 주세요.", ephemeral=True)
        if self.me.id == self.user.id and is_user(self.user):
            return await interaction.response.send_message("자기 자신을 팔로우할 수 없습니다.", ephemeral=True)
        if self.user in self.me.get_following():
            self.me.remove_from_following(self.user)
            await interaction.response.send_message("팔로우 취소!", ephemeral=True)
        else:
            self.me.add_to_following(self.user)
            await interaction.response.send_message("팔로우!", ephemeral=True)


class RepoControl(RequireRegisterView):
    def __init__(self, bot: Bot, me: AuthenticatedUser, repo: Repository):
        super().__init__(bot, me)
        self.repo = repo
        self.add_item(Button(label="🔗", url=repo.html_url, style=ButtonStyle.url))

    @button(style=ButtonStyle.blurple, custom_id="fork", emoji=PartialEmoji(name="fork", id=1063066537075953684))
    async def fork(self, _, interaction: Interaction):
        if not self.login:
            return await interaction.response.send_message("계정을 연동해 주세요.", ephemeral=True)
        if self.me.id == self.repo.owner.id:
            return await interaction.response.send_message("자기 자신의 레포를 포크할 수 없습니다.", ephemeral=True)
        url = self.me.create_fork(self.repo).html_url
        await interaction.response.send_message(f"포크 완료!\n<{url}>", ephemeral=True)

    @button(style=ButtonStyle.green, label="⭐", custom_id="star")
    async def star(self, _, interaction: Interaction):
        if not self.login:
            return await interaction.response.send_message("계정을 연동해 주세요.", ephemeral=True)
        if self.repo in self.me.get_starred():
            self.me.remove_from_starred(self.repo)
            await interaction.response.send_message("스타 취소!", ephemeral=True)
        else:
            self.me.add_to_starred(self.repo)
            await interaction.response.send_message("스타!", ephemeral=True)

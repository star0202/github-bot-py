from discord import ButtonStyle, Embed, Interaction, PartialEmoji
from discord.ui import button, Button, InputText, Modal, View
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from github.Repository import Repository

from config import COLOR
from utils.bot import Bot


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
            await interaction.response.send_message("팔로우 취소!", ephemeral=True)
        else:
            self.me.add_to_following(self.user)
            await interaction.response.send_message("팔로우!", ephemeral=True)


class RepoControl(View):
    def __init__(self, me: AuthenticatedUser, repo: Repository):
        super().__init__(timeout=60)
        self.me = me
        self.repo = repo
        self.add_item(Button(label="🔗", url=repo.html_url, style=ButtonStyle.url))

    @button(emoji=PartialEmoji(name="fork", id=1063066537075953684), style=ButtonStyle.blurple)
    async def fork(self, _, interaction: Interaction):
        url = self.me.create_fork(self.repo).html_url
        await interaction.response.send_message(f"포크 완료!\n<{url}>", ephemeral=True)

    @button(label="⭐", style=ButtonStyle.green)
    async def star(self, _, interaction: Interaction):
        if self.repo in self.me.get_starred():
            self.me.remove_from_starred(self.repo)
            await interaction.response.send_message("스타 취소!", ephemeral=True)
        else:
            self.me.add_to_starred(self.repo)
            await interaction.response.send_message("스타!", ephemeral=True)

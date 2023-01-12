from aiosqlite import Error
from logging import getLogger
from traceback import format_exc

from discord import ApplicationContext, Option, Embed  # noqa
from discord.ext import commands  # noqa

from config import COLOR, BAD
from utils.commands import slash_command

logger = getLogger(__name__)


class Dev(commands.Cog, command_attrs={"hidden": True}):
    def __init__(self, bot):
        self.bot = bot

    @slash_command()
    @commands.is_owner()
    async def stop(self, ctx: ApplicationContext):
        await ctx.respond("stopping..")
        await self.bot.close()

    @slash_command()
    @commands.is_owner()
    async def load_ext(self, ctx: ApplicationContext, ext_name: Option(str)):
        self.bot.load_extension(f"functions.{ext_name}")
        await ctx.respond(f"{ext_name}.py loaded")

    @slash_command()
    @commands.is_owner()
    async def unload_ext(self, ctx: ApplicationContext, ext_name: Option(str)):
        self.bot.unload_extension(f"functions.{ext_name}")
        await ctx.respond(f"{ext_name}.py loaded")

    @slash_command()
    @commands.is_owner()
    async def reload_ext(self, ctx: ApplicationContext, ext_name: Option(str)):
        self.bot.unload_extension(f"functions.{ext_name}")
        self.bot.load_extension(f"functions.{ext_name}")
        await ctx.respond(f"{ext_name}.py reloaded")

    @slash_command()
    @commands.is_owner()
    async def send_here(self, ctx: ApplicationContext, content: Option(str)):
        await ctx.send(content)
        delete_this = await ctx.respond("random respond")
        await delete_this.delete_original_response()

    @slash_command()
    @commands.is_owner()
    async def sql(self, ctx: ApplicationContext, sql: Option(str)):
        try:
            result = await self.bot.db.execute(sql)
            embed = Embed(title="Executed!", color=COLOR)
            embed.add_field(name="Script", value=f"```sql\n{sql}```")
            embed.add_field(name="Result", value=f"```py\n{result}```")
        except Error:
            embed = Embed(title="SQL Error", color=BAD)
            embed.add_field(name="Script", value=f"```sql\n{sql}```")
            embed.add_field(name="Error", value=f"```py\n{format_exc().splitlines()[-1]}```")
        await ctx.respond(embed=embed)


def setup(bot):
    logger.info("Loaded")
    bot.add_cog(Dev(bot))


def teardown():
    logger.info("Unloaded")

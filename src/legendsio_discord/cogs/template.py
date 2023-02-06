from discord.ext import commands
from discord.ext.commands import Context

from legendsio_discord.helpers import checks


class Template(commands.Cog, name="template"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="test",
        description="A command that does nothing but confirm cogs are working."
    )
    @checks.not_blacklisted()
    async def test(self, context: Context):
        """
        This is a test command that does nothing

        :param context: The command's context
        :return:
        """
        await context.send("Yay, cogs and application commands are working.")


async def setup(bot):
    await bot.add_cog(Template(bot))
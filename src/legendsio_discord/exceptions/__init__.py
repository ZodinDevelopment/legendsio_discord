import discord
from discord.ext import commands


class UserBlackListed(commands.CheckFailure):
    def __init__(self, message="User is blacklisted"):
        self.message = message
        super().__init__(self.message)


class UserNotOwner(commands.CheckFailure):
    def __init__(self, message="User is not owner"):
        self.message = message
        super().__init__(self.message)


class UserNotAgent(commands.CheckFailure):
    def __init__(self, message="User does not have free agent role"):
        self.message = message
        super().__init__(self.message)


class UserNotCoach(commands.CheckFailure):
    def __init__(self, message="User does not have coach role."):
        self.message = message
        super().__init__(self.message)
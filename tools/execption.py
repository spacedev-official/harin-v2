from discord.ext import commands
class PermError:
    class BlacklistedUser(commands.CheckFailure):
        def __str__(self):
            return "BlackListed User"

    class NotOwnerUser(commands.CheckFailure):
        def __str__(self):
            return "This user is not owner"

    class NotRegisterUser(commands.CheckFailure):
        def __str__(self):
            return "Not Register User"

    class AlreadyRegisterUser(commands.CheckFailure):
        def __str__(self):
            return "Already Register User"

    class NotEnoughItem(commands.CheckFailure):
        def __str__(self):
            return "Has Not Enough Item"

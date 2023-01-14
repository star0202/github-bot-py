from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser


def is_user(user: NamedUser) -> bool:
    if user.type == "User":
        return True
    return False


def get_user_name(user: AuthenticatedUser | NamedUser) -> str:
    return user.name if user.name else user.login

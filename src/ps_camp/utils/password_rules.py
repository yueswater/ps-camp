import re


def is_strong_password(password: str) -> bool:
    """
    Passwords must meet the following conditions:
    -At least 8 characters
    -At least one capital letter
    -At least one lowercase letter
    -At least one number
    -At least one special symbol (such as !@#$%^&*)
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

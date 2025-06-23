from flask_bcrypt import Bcrypt


class PasswordHasher:
    def __init__(self, bcrypt: Bcrypt = None):
        if bcrypt is None:
            from flask import current_app

            self.bcrypt = Bcrypt(current_app)
        else:
            self.bcrypt = bcrypt

    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("密碼不得為空！")
        hashed = self.bcrypt.generate_password_hash(password)
        return hashed.decode("utf-8")

    def verify_password(self, raw: str, hashed: str) -> bool:
        return bool(raw and hashed and self.bcrypt.check_password_hash(hashed, raw))

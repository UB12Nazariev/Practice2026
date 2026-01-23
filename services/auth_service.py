import bcrypt
import asyncpg


class AuthService:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, hash_: str) -> bool:
        return bcrypt.checkpw(password.encode(), hash_.encode())

    async def create_user(self, username: str, password: str):
        pwd_hash = self.hash_password(password)
        await self.conn.execute(
            "INSERT INTO users (username, password_hash) VALUES ($1, $2)",
            username,
            pwd_hash
        )

    async def authenticate(self, username: str, password: str):
        row = await self.conn.fetchrow(
            "SELECT * FROM users WHERE username=$1 AND is_active=true",
            username
        )
        if not row:
            return None

        if not self.verify_password(password, row["password_hash"]):
            return None

        return dict(row)

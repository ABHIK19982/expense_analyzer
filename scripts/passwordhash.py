import bcrypt
import secrets
import base64


class PasswordHasher:
    def __init__(self):
        self.rounds = 12  # Number of rounds for bcrypt

    def generate_hash(self, password: str) -> tuple:
        """
        Generate a secure password hash using bcrypt
        Returns tuple of (hash, salt)
        """
        if not isinstance(password, str):
            raise ValueError("Password must be a string")

        if not password:
            raise ValueError("Password cannot be empty")

        # Generate a random salt
        salt = bcrypt.gensalt(rounds=self.rounds)

        # Convert password to bytes if it's not already
        password_bytes = password.encode('utf-8')

        # Generate the hash
        password_hash = bcrypt.hashpw(password_bytes, salt)

        return password_hash.decode('utf-8'), salt.decode('utf-8')

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify a password against a stored hash
        """
        try:
            password_bytes = password.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, stored_hash_bytes)
        except Exception as e:
            print(f"Error verifying password: {e}")
            return False

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a secure random token
        """
        return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8')


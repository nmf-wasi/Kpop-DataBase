from passlib.context import CryptContext

# instantiate the CryptoContext obj
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """returns the hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Takes plain input password and hashed password from db and compares them"""
    return pwd_context.verify(plain_password, hashed_password)

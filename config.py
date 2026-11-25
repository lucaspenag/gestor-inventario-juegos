import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalizar_url_base(url):
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "passkey-de-desarrollo")

    SQLALCHEMY_DATABASE_URI = _normalizar_url_base(
        os.getenv("DATABASE_URL")
    ) or "sqlite:///" + os.path.join(BASE_DIR, "instance", "inventario.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tiendadejuegos.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

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

    # Busqueda por nombre en Wikidata y detalle desde el JSON de la web de BGG
    # (la XML API2 oficial de BGG exige un token registrado).
    WIKIDATA_SPARQL_URL = os.getenv(
        "WIKIDATA_SPARQL_URL", "https://query.wikidata.org/sparql"
    )
    WIKIDATA_TIMEOUT = int(os.getenv("WIKIDATA_TIMEOUT", "20"))
    GEEKDO_API_URL = os.getenv("GEEKDO_API_URL", "https://api.geekdo.com/api")
    BGG_TIMEOUT = int(os.getenv("BGG_TIMEOUT", "10"))

    # Credenciales de Google OAuth (se obtienen en Google Cloud Console).
    # Si falta alguna de las dos, el login con Google queda deshabilitado.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_DISCOVERY_URL = os.getenv(
        "GOOGLE_DISCOVERY_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    )

    # Si esta en "True", una cuenta de Google nueva se registra sola como
    # empleado. Si esta en "False", solo entran los usuarios ya cargados.
    PERMITIR_ALTA_CON_GOOGLE = os.getenv("PERMITIR_ALTA_CON_GOOGLE", "True") == "True"

    ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@tiendadejuegos.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

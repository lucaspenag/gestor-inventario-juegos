from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


def ahora():
    """Fecha y hora actual."""
    return datetime.now(timezone.utc)


class Usuario(UserMixin, db.Model):

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default="empleado")
    origen = db.Column(db.String(20), nullable=False, default="local")
    foto_url = db.Column(db.String(300), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_alta = db.Column(db.DateTime, default=ahora)


    def definir_password(self, password):
        """Guarda la contrasena cifrada."""
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):
        """Compara la contrasena ingresada contra el hash guardado."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == "admin"

    def __repr__(self):
        return f"<Usuario {self.email} ({self.rol})>"


@login_manager.user_loader
def cargar_usuario(user_id):
    try:
        return db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager


def ahora():
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

    movimientos = db.relationship("Movimiento", back_populates="usuario")

    def definir_password(self, password):

        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):

        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == "admin"

    def __repr__(self):
        return f"<Usuario {self.email} ({self.rol})>"


class Proveedor(db.Model):


    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), unique=True, nullable=False)
    contacto = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    juegos = db.relationship("Juego", back_populates="proveedor")

    def __repr__(self):
        return f"<Proveedor {self.nombre}>"


class Juego(db.Model):


    __tablename__ = "juegos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    editorial = db.Column(db.String(150), nullable=True)
    categoria = db.Column(db.String(100), nullable=True)
    min_jugadores = db.Column(db.Integer, nullable=True)
    max_jugadores = db.Column(db.Integer, nullable=True)
    edad_minima = db.Column(db.Integer, nullable=True)
    duracion_minutos = db.Column(db.Integer, nullable=True)
    precio = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=1)

    bgg_id = db.Column(db.Integer, nullable=True)
    imagen_url = db.Column(db.String(400), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)

    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"), nullable=True)
    proveedor = db.relationship("Proveedor", back_populates="juegos")

    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_alta = db.Column(db.DateTime, default=ahora)

    movimientos = db.relationship(
        "Movimiento", back_populates="juego", cascade="all, delete-orphan"
    )

    @property
    def necesita_reposicion(self):

        return self.stock <= self.stock_minimo

    @property
    def jugadores_texto(self):
        if self.min_jugadores and self.max_jugadores:
            if self.min_jugadores == self.max_jugadores:
                return f"{self.min_jugadores} jugadores"
            return f"{self.min_jugadores} a {self.max_jugadores} jugadores"
        return "Sin datos"

    def __repr__(self):
        return f"<Juego {self.nombre} (stock={self.stock})>"


class Movimiento(db.Model):


    __tablename__ = "movimientos"

    TIPOS = ("ingreso", "venta", "baja")

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(250), nullable=True)
    stock_resultante = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=ahora, index=True)

    juego_id = db.Column(db.Integer, db.ForeignKey("juegos.id"), nullable=False)
    juego = db.relationship("Juego", back_populates="movimientos")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuario", back_populates="movimientos")

    @property
    def signo(self):

        return 1 if self.tipo == "ingreso" else -1

    def __repr__(self):
        return f"<Movimiento {self.tipo} x{self.cantidad} juego={self.juego_id}>"


@login_manager.user_loader
def cargar_usuario(user_id):

    try:
        return db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None

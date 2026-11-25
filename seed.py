from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Juego, Proveedor, Usuario

JUEGOS_DEMO = [
    {
        "nombre": "Catan",
        "editorial": "Devir",
        "categoria": "Estrategia",
        "min_jugadores": 3,
        "max_jugadores": 4,
        "edad_minima": 10,
        "duracion_minutos": 75,
        "precio": 52000.0,
        "stock": 8,
        "stock_minimo": 3,
    },
    {
        "nombre": "Dixit",
        "editorial": "Libellud",
        "categoria": "Party",
        "min_jugadores": 3,
        "max_jugadores": 6,
        "edad_minima": 8,
        "duracion_minutos": 30,
        "precio": 61000.0,
        "stock": 4,
        "stock_minimo": 2,
    },
    {
        "nombre": "Carcassonne",
        "editorial": "Devir",
        "categoria": "Familiar",
        "min_jugadores": 2,
        "max_jugadores": 5,
        "edad_minima": 7,
        "duracion_minutos": 45,
        "precio": 48000.0,
        "stock": 2,
        "stock_minimo": 3,
    },
    {
        "nombre": "Virus",
        "editorial": "Tranjis Games",
        "categoria": "Cartas",
        "min_jugadores": 2,
        "max_jugadores": 6,
        "edad_minima": 8,
        "duracion_minutos": 20,
        "precio": 22000.0,
        "stock": 12,
        "stock_minimo": 5,
    },
    {
        "nombre": "Aventureros al Tren",
        "editorial": "Days of Wonder",
        "categoria": "Familiar",
        "min_jugadores": 2,
        "max_jugadores": 5,
        "edad_minima": 8,
        "duracion_minutos": 60,
        "precio": 78000.0,
        "stock": 0,
        "stock_minimo": 2,
    },
]


def crear_datos_iniciales():
    try:
        email_admin = current_app.config["ADMIN_EMAIL"].lower()
        admin = Usuario.query.filter_by(email=email_admin).first()

        if admin is None:
            admin = Usuario(
                nombre=current_app.config["ADMIN_NOMBRE"],
                email=email_admin,
                rol="admin",
                origen="local",
            )
            admin.definir_password(current_app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            current_app.logger.info("Se creo el usuario administrador %s", email_admin)

        if Proveedor.query.count() == 0:
            db.session.add_all(
                [
                    Proveedor(
                        nombre="Devir Argentina",
                        contacto="Ventas mayoristas",
                        email="ventas@devir.example",
                        telefono="011-4000-0001",
                    ),
                    Proveedor(
                        nombre="Maldito Games",
                        contacto="Distribucion",
                        email="pedidos@maldito.example",
                        telefono="011-4000-0002",
                    ),
                ]
            )

        if Juego.query.count() == 0:
            db.session.add_all(Juego(**datos) for datos in JUEGOS_DEMO)
            current_app.logger.info("Se cargaron los juegos de ejemplo")

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error("Error al cargar los datos iniciales: %s", e)

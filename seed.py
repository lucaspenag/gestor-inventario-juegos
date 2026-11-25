from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Usuario


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

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error("Error al cargar los datos iniciales: %s", e)

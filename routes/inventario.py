from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from decoradores import admin_requerido
from extensions import db
from models import Juego, Proveedor

inventario_bp = Blueprint("inventario", __name__)


@inventario_bp.route("/")
@login_required
def tablero():
    try:
        juegos_activos = Juego.query.filter_by(activo=True).all()
        total_juegos = len(juegos_activos)
        unidades = sum(j.stock for j in juegos_activos)
        valorizado = sum(j.stock * j.precio for j in juegos_activos)
        a_reponer = [j for j in juegos_activos if j.necesita_reposicion]
        sin_stock = [j for j in juegos_activos if j.stock == 0]
    except SQLAlchemyError as e:
        current_app.logger.error("Error al armar el tablero: %s", e)
        flash("No se pudo cargar el resumen del inventario.", "danger")
        total_juegos = unidades = valorizado = 0
        a_reponer = sin_stock = []

    return render_template(
        "tablero.html",
        total_juegos=total_juegos,
        unidades=unidades,
        valorizado=valorizado,
        a_reponer=a_reponer,
        sin_stock=sin_stock,
    )

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

from extensions import db
from models import Juego, Movimiento

movimientos_bp = Blueprint("movimientos", __name__, url_prefix="/movimientos")

ETIQUETAS = {
    "ingreso": "Ingreso de mercaderia",
}


@movimientos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    try:
        juegos = Juego.query.filter_by(activo=True).order_by(Juego.nombre).all()
    except SQLAlchemyError as e:
        current_app.logger.error("Error al cargar los juegos: %s", e)
        flash("No se pudo cargar el listado de juegos.", "danger")
        juegos = []


    preseleccionado = request.args.get("juego_id", "")

    if request.method == "POST":
        tipo = (request.form.get("tipo") or "").strip()
        motivo = (request.form.get("motivo") or "").strip()
        errores = []

        if tipo not in ETIQUETAS:
            errores.append("Elegi un tipo de movimiento valido.")

        try:
            juego_id = int(request.form.get("juego_id") or 0)
        except ValueError:
            juego_id = 0
        if juego_id <= 0:
            errores.append("Elegi el juego sobre el que se hace el movimiento.")

        try:
            cantidad = int(request.form.get("cantidad") or 0)
            if cantidad <= 0:
                errores.append("La cantidad tiene que ser mayor que cero.")
        except ValueError:
            cantidad = 0
            errores.append("La cantidad tiene que ser un numero entero.")

        juego = db.session.get(Juego, juego_id) if juego_id > 0 else None
        if juego_id > 0 and juego is None:
            errores.append("El juego seleccionado no existe.")

        if errores:
            for error in errores:
                flash(error, "warning")
            return render_template(
                "movimientos/formulario.html",
                juegos=juegos,
                etiquetas=ETIQUETAS,
                valores=request.form,
                preseleccionado=preseleccionado,
            )

        try:
            juego.stock += cantidad

            movimiento = Movimiento(
                tipo=tipo,
                cantidad=cantidad,
                motivo=motivo or None,
                stock_resultante=juego.stock,
                juego_id=juego.id,
                usuario_id=current_user.id,
            )
            db.session.add(movimiento)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error("Error al registrar el movimiento: %s", e)
            flash("No se pudo registrar el movimiento.", "danger")
            return render_template(
                "movimientos/formulario.html",
                juegos=juegos,
                etiquetas=ETIQUETAS,
                valores=request.form,
                preseleccionado=preseleccionado,
            )

        flash(
            f"{ETIQUETAS[tipo]} registrado. {juego.nombre} queda con {juego.stock} unidades.",
            "success",
        )

        return redirect(url_for("inventario.listar_juegos"))

    return render_template(
        "movimientos/formulario.html",
        juegos=juegos,
        etiquetas=ETIQUETAS,
        valores=None,
        preseleccionado=preseleccionado,
    )
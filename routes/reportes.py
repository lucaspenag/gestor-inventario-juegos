from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, render_template, request
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from decoradores import admin_requerido
from models import Juego, Movimiento

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _leer_fecha(nombre, por_defecto):
    crudo = (request.args.get(nombre) or "").strip()
    if not crudo:
        return por_defecto, None
    try:
        return datetime.strptime(crudo, "%Y-%m-%d"), None
    except ValueError:
        return por_defecto, f"La fecha {nombre} no tiene un formato valido."


@reportes_bp.route("/")
@login_required
@admin_requerido
def periodo():
    hoy = datetime.now()
    desde_defecto = hoy - timedelta(days=30)

    desde, error_desde = _leer_fecha("desde", desde_defecto)
    hasta, error_hasta = _leer_fecha("hasta", hoy)

    for error in (error_desde, error_hasta):
        if error:
            flash(error, "warning")

    if desde > hasta:
        flash("La fecha desde no puede ser posterior a la fecha hasta.", "warning")
        desde, hasta = hasta, desde

    hasta_completo = hasta.replace(hour=23, minute=59, second=59)

    filas = []
    totales = {"ingreso": 0, "venta": 0, "baja": 0}

    try:
        movimientos = (
            Movimiento.query.filter(
                Movimiento.fecha >= desde, Movimiento.fecha <= hasta_completo
            )
            .order_by(Movimiento.fecha)
            .all()
        )

        acumulado = {}
        for m in movimientos:
            clave = m.juego_id
            if clave not in acumulado:
                acumulado[clave] = {
                    "juego": m.juego,
                    "ingreso": 0,
                    "venta": 0,
                    "baja": 0,
                }
            acumulado[clave][m.tipo] += m.cantidad
            totales[m.tipo] += m.cantidad

        filas = sorted(
            acumulado.values(), key=lambda f: f["venta"], reverse=True
        )

        a_reponer = [
            j
            for j in Juego.query.filter_by(activo=True).order_by(Juego.nombre).all()
            if j.necesita_reposicion
        ]
    except SQLAlchemyError as e:
        current_app.logger.error("Error al generar el reporte: %s", e)
        flash("No se pudo generar el reporte.", "danger")
        a_reponer = []

    return render_template(
        "reportes.html",
        filas=filas,
        totales=totales,
        a_reponer=a_reponer,
        desde=desde.strftime("%Y-%m-%d"),
        hasta=hasta.strftime("%Y-%m-%d"),
    )

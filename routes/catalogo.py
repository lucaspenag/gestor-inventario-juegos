from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from decoradores import admin_requerido
from services.bgg import ErrorAPIExterna, buscar_juegos, obtener_detalle

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/catalogo/buscar")
@login_required
@admin_requerido
def buscar():
    consulta = (request.args.get("q") or "").strip()
    resultados = []

    if consulta:
        try:
            resultados = buscar_juegos(consulta)
            if not resultados:
                flash(f"BoardGameGeek no encontro juegos para '{consulta}'.", "info")
        except ErrorAPIExterna as e:
            flash(str(e), "danger")
        except Exception as e:
            current_app.logger.error("Error inesperado al buscar en BGG: %s", e)
            flash("Ocurrio un error inesperado al consultar BoardGameGeek.", "danger")

    return render_template("catalogo.html", consulta=consulta, resultados=resultados)


@catalogo_bp.route("/catalogo/importar/<int:bgg_id>")
@login_required
@admin_requerido
def importar(bgg_id):
    try:
        datos = obtener_detalle(bgg_id)
    except ErrorAPIExterna as e:
        flash(str(e), "danger")
        return redirect(url_for("catalogo.buscar"))
    except Exception as e:
        current_app.logger.error("Error inesperado al importar de BGG: %s", e)
        flash("No se pudo importar el juego desde BoardGameGeek.", "danger")
        return redirect(url_for("catalogo.buscar"))

    parametros = {clave: valor for clave, valor in datos.items() if valor is not None}
    flash(
        f"Datos de {datos['nombre']} traidos desde BoardGameGeek. "
        "Completa el precio y el stock para terminar el alta.",
        "info",
    )
    return redirect(url_for("inventario.nuevo_juego", **parametros))

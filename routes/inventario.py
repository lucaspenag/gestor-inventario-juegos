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
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from decoradores import admin_requerido
from extensions import db
from models import Juego, Proveedor

inventario_bp = Blueprint("inventario", __name__)


def _leer_entero(nombre, obligatorio=False, minimo=None, etiqueta=None):
    etiqueta = etiqueta or nombre
    crudo = (request.form.get(nombre) or "").strip()

    if not crudo:
        if obligatorio:
            return None, f"El campo {etiqueta} es obligatorio."
        return None, None

    try:
        valor = int(crudo)
    except ValueError:
        return None, f"El campo {etiqueta} tiene que ser un numero entero."

    if minimo is not None and valor < minimo:
        return None, f"El campo {etiqueta} no puede ser menor que {minimo}."

    return valor, None


def _leer_decimal(nombre, obligatorio=False, minimo=None, etiqueta=None):
    etiqueta = etiqueta or nombre
    crudo = (request.form.get(nombre) or "").strip().replace(",", ".")

    if not crudo:
        if obligatorio:
            return None, f"El campo {etiqueta} es obligatorio."
        return None, None

    try:
        valor = float(crudo)
    except ValueError:
        return None, f"El campo {etiqueta} tiene que ser un numero."

    if minimo is not None and valor < minimo:
        return None, f"El campo {etiqueta} no puede ser menor que {minimo}."

    return valor, None


def _datos_del_formulario():
    errores = []
    datos = {}

    datos["nombre"] = (request.form.get("nombre") or "").strip()
    if not datos["nombre"]:
        errores.append("El nombre del juego es obligatorio.")

    datos["editorial"] = (request.form.get("editorial") or "").strip() or None
    datos["categoria"] = (request.form.get("categoria") or "").strip() or None
    datos["descripcion"] = (request.form.get("descripcion") or "").strip() or None
    datos["imagen_url"] = (request.form.get("imagen_url") or "").strip() or None

    for campo, obligatorio, minimo, etiqueta in [
        ("min_jugadores", False, 1, "cantidad minima de jugadores"),
        ("max_jugadores", False, 1, "cantidad maxima de jugadores"),
        ("edad_minima", False, 0, "edad minima"),
        ("duracion_minutos", False, 1, "duracion"),
        ("stock", True, 0, "stock"),
        ("stock_minimo", True, 0, "stock minimo"),
        ("bgg_id", False, 1, "id de BoardGameGeek"),
    ]:
        valor, error = _leer_entero(campo, obligatorio, minimo, etiqueta)
        if error:
            errores.append(error)
        datos[campo] = valor

    precio, error = _leer_decimal("precio", obligatorio=True, minimo=0.01, etiqueta="precio")
    if error:
        errores.append(error)
    datos["precio"] = precio

    if datos["min_jugadores"] and datos["max_jugadores"]:
        if datos["min_jugadores"] > datos["max_jugadores"]:
            errores.append(
                "La cantidad minima de jugadores no puede superar a la maxima."
            )

    proveedor_id, error = _leer_entero("proveedor_id", etiqueta="proveedor")
    if error:
        errores.append(error)
    datos["proveedor_id"] = proveedor_id

    return datos, errores


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


@inventario_bp.route("/juegos")
@login_required
def listar_juegos():
    texto = (request.args.get("q") or "").strip()
    jugadores = (request.args.get("jugadores") or "").strip()
    ver_inactivos = request.args.get("inactivos") == "1"
    solo_reponer = request.args.get("reponer") == "1"

    try:
        consulta = Juego.query
        if not ver_inactivos:
            consulta = consulta.filter_by(activo=True)

        if texto:
            patron = f"%{texto}%"
            consulta = consulta.filter(
                or_(
                    Juego.nombre.ilike(patron),
                    Juego.categoria.ilike(patron),
                    Juego.editorial.ilike(patron),
                )
            )

        if jugadores:
            try:
                cantidad = int(jugadores)
                consulta = consulta.filter(
                    Juego.min_jugadores <= cantidad,
                    Juego.max_jugadores >= cantidad,
                )
            except ValueError:
                flash("La cantidad de jugadores tiene que ser un numero.", "warning")

        juegos = consulta.order_by(Juego.nombre).all()

        if solo_reponer:
            juegos = [j for j in juegos if j.necesita_reposicion]
    except SQLAlchemyError as e:
        current_app.logger.error("Error al listar los juegos: %s", e)
        flash("No se pudo cargar el catalogo.", "danger")
        juegos = []

    return render_template(
        "juegos/lista.html",
        juegos=juegos,
        texto=texto,
        jugadores=jugadores,
        ver_inactivos=ver_inactivos,
        solo_reponer=solo_reponer,
    )


@inventario_bp.route("/juegos/nuevo", methods=["GET", "POST"])
@login_required
@admin_requerido
def nuevo_juego():
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()

    if request.method == "POST":
        datos, errores = _datos_del_formulario()

        if errores:
            for error in errores:
                flash(error, "warning")
            return render_template(
                "juegos/formulario.html",
                juego=None,
                proveedores=proveedores,
                valores=request.form,
            )

        try:
            duplicado = Juego.query.filter(
                db.func.lower(Juego.nombre) == datos["nombre"].lower()
            ).first()
            if duplicado:
                flash(
                    f"Ya existe un juego registrado con el nombre {datos['nombre']}.",
                    "warning",
                )
                return render_template(
                    "juegos/formulario.html",
                    juego=None,
                    proveedores=proveedores,
                    valores=request.form,
                )

            juego = Juego(**datos)
            db.session.add(juego)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo guardar el juego por un conflicto de datos.", "danger")
            return render_template(
                "juegos/formulario.html",
                juego=None,
                proveedores=proveedores,
                valores=request.form,
            )
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error("Error al dar de alta un juego: %s", e)
            flash("No se pudo guardar el juego.", "danger")
            return render_template(
                "juegos/formulario.html",
                juego=None,
                proveedores=proveedores,
                valores=request.form,
            )

        flash(f"Se agrego {juego.nombre} al inventario.", "success")
        return redirect(url_for("inventario.listar_juegos"))

    return render_template(
        "juegos/formulario.html",
        juego=None,
        proveedores=proveedores,
        valores=request.args,
    )


@inventario_bp.route("/juegos/<int:juego_id>/editar", methods=["GET", "POST"])
@login_required
@admin_requerido
def editar_juego(juego_id):
    """Modificacion de los datos de un juego. HU02."""
    juego = db.session.get(Juego, juego_id)
    if juego is None:
        flash("El juego que buscas no existe.", "warning")
        return redirect(url_for("inventario.listar_juegos"))

    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()

    if request.method == "POST":
        datos, errores = _datos_del_formulario()

        if errores:
            for error in errores:
                flash(error, "warning")
            return render_template(
                "juegos/formulario.html",
                juego=juego,
                proveedores=proveedores,
                valores=request.form,
            )

        try:
            for campo, valor in datos.items():
                setattr(juego, campo, valor)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error("Error al editar el juego %s: %s", juego_id, e)
            flash("No se pudieron guardar los cambios.", "danger")
            return render_template(
                "juegos/formulario.html",
                juego=juego,
                proveedores=proveedores,
                valores=request.form,
            )

        flash(f"Se actualizaron los datos de {juego.nombre}.", "success")
        return redirect(url_for("inventario.listar_juegos"))

    return render_template(
        "juegos/formulario.html", juego=juego, proveedores=proveedores, valores=None
    )

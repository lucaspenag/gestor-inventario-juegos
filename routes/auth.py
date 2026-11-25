from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import Usuario

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("inventario.tablero"))

    google_activo = bool(current_app.config.get("GOOGLE_CLIENT_ID"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Completa el email y la contrasena.", "warning")
            return render_template("login.html", google_activo=google_activo)

        try:
            usuario = Usuario.query.filter_by(email=email).first()
        except SQLAlchemyError as e:
            current_app.logger.error("Error al consultar el usuario: %s", e)
            flash("No se pudo validar el usuario. Intentalo de nuevo.", "danger")
            return render_template("login.html", google_activo=google_activo)

        if usuario is None or not usuario.verificar_password(password):
            flash("El email o la contrasena no son correctos.", "danger")
            return render_template("login.html", google_activo=google_activo)

        if not usuario.activo:
            flash("Tu usuario esta dado de baja. Hablalo con el administrador.", "danger")
            return render_template("login.html", google_activo=google_activo)

        login_user(usuario)
        flash(f"Hola {usuario.nombre}, iniciaste sesion correctamente.", "success")
        return redirect(url_for("inventario.tablero"))

    return render_template("login.html", google_activo=google_activo)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste la sesion.", "info")
    return redirect(url_for("auth.login"))

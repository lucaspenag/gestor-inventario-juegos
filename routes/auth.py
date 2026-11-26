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

from extensions import db, oauth
from models import Usuario

auth_bp = Blueprint("auth", __name__)


def _google_configurado():
    return bool(
        current_app.config.get("GOOGLE_CLIENT_ID")
        and current_app.config.get("GOOGLE_CLIENT_SECRET")
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("inventario.tablero"))

    google_activo = _google_configurado()

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

@auth_bp.route("/login/google")
def login_google():
    if not _google_configurado():
        flash(
            "El inicio de sesion con Google no esta configurado en este entorno.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    try:
        redirect_uri = url_for("auth.callback_google", _external=True)
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error("Error al iniciar el flujo de Google: %s", e)
        flash("No se pudo conectar con Google. Intentalo de nuevo.", "danger")
        return redirect(url_for("auth.login"))


@auth_bp.route("/auth/callback")
def callback_google():
    if not _google_configurado():
        return redirect(url_for("auth.login"))

    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        current_app.logger.warning("No se completo el login con Google: %s", e)
        flash("Cancelaste el inicio de sesion con Google o no se pudo completar.", "warning")
        return redirect(url_for("auth.login"))

    datos = token.get("userinfo") or {}
    email = (datos.get("email") or "").strip().lower()

    if not email or not datos.get("email_verified", False):
        flash("Google no devolvio un email verificado.", "danger")
        return redirect(url_for("auth.login"))

    try:
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario is None:
            if not current_app.config.get("PERMITIR_ALTA_CON_GOOGLE"):
                flash(
                    "Esa cuenta de Google no esta habilitada. Pedile el alta al administrador.",
                    "warning",
                )
                return redirect(url_for("auth.login"))

            usuario = Usuario(
                nombre=datos.get("name") or email.split("@")[0],
                email=email,
                rol="empleado",
                origen="google",
                foto_url=datos.get("picture"),
            )
            db.session.add(usuario)
        else:
            usuario.foto_url = datos.get("picture") or usuario.foto_url

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error("Error al guardar el usuario de Google: %s", e)
        flash("No se pudo registrar tu cuenta. Intentalo de nuevo.", "danger")
        return redirect(url_for("auth.login"))

    if not usuario.activo:
        flash("Tu usuario esta dado de baja. Hablalo con el administrador.", "danger")
        return redirect(url_for("auth.login"))

    login_user(usuario)
    flash(f"Hola {usuario.nombre}, entraste con tu cuenta de Google.", "success")
    return redirect(url_for("inventario.tablero"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste la sesion.", "info")
    return redirect(url_for("auth.login"))

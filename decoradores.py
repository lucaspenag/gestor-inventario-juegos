from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_requerido(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.es_admin:
            flash("Esa seccion es exclusiva del administrador.", "danger")
            return redirect(url_for("inventario.tablero"))
        return f(*args, **kwargs)

    return envoltura


def solo_activos(f):

    @wraps(f)
    def envoltura(*args, **kwargs):
        if current_user.is_authenticated and not current_user.activo:
            abort(403)
        return f(*args, **kwargs)

    return envoltura

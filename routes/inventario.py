from flask import Blueprint, render_template
from flask_login import login_required

inventario_bp = Blueprint("inventario", __name__)


@inventario_bp.route("/")
@login_required
def tablero():
    return render_template("tablero.html")

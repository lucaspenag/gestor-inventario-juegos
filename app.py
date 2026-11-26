import os

from flask import Flask



from config import Config
from extensions import db, login_manager, oauth
from routes.auth import auth_bp
from routes.catalogo import catalogo_bp
from routes.inventario import inventario_bp
from routes.movimientos import movimientos_bp
from routes.reportes import reportes_bp
from seed import crear_datos_iniciales

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
oauth.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(movimientos_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(catalogo_bp)


@app.context_processor
def variables_globales():
    return {"nombre_sistema": "Mesa Chica - Gestor de Inventario"}


@app.template_filter("pesos")
def formato_pesos(valor):
    try:
        return "$ " + f"{float(valor):,.2f}".replace(",", "X").replace(
            ".", ","
        ).replace("X", ".")
    except (TypeError, ValueError):
        return "$ 0,00"


@app.template_filter("fecha")
def formato_fecha(valor):
    try:
        return valor.strftime("%d/%m/%Y %H:%M")
    except AttributeError:
        return "-"



with app.app_context():
    db.create_all()
    crear_datos_iniciales()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "True") == "True"
    app.run(debug=debug, port=int(os.getenv("PORT", "5000")))

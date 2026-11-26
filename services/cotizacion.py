import requests
from flask import current_app

URL_COTIZACION = "https://dolarapi.com/v1/dolares/oficial"


def obtener_cotizacion():
    try:
        respuesta = requests.get(URL_COTIZACION, timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except requests.exceptions.Timeout:
        return {"ok": False, "mensaje": "La API de cotizacion tardo demasiado."}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "mensaje": "No hay conexion con la API de cotizacion."}
    except requests.exceptions.HTTPError as e:
        return {"ok": False, "mensaje": f"La API de cotizacion respondio mal: {e}"}
    except ValueError:
        return {"ok": False, "mensaje": "La API de cotizacion devolvio datos invalidos."}
    except Exception as e:  
        current_app.logger.error("Error inesperado en la cotizacion: %s", e)
        return {"ok": False, "mensaje": "No se pudo obtener la cotizacion."}

    return {
        "ok": True,
        "nombre": datos.get("nombre", "Oficial"),
        "compra": datos.get("compra"),
        "venta": datos.get("venta"),
        "actualizado": datos.get("fechaActualizacion"),
    }

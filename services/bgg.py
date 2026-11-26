"""Consulta de datos de juegos de mesa.

La XML API2 oficial de BoardGameGeek ahora exige un token registrado, asi que
mientras tanto se usan dos fuentes sin clave:

- Wikidata (SPARQL publico) para buscar por nombre. Cada juego trae su ID de
  BoardGameGeek (propiedad P2339), asi que los IDs siguen siendo los de BGG.
- El JSON que usa la propia web de BGG (api.geekdo.com) para traer el detalle.
  No es una API oficial y puede cambiar sin aviso: si falla, el detalle se
  arma con los datos de Wikidata.
"""

import html
import re

import requests
from flask import current_app


class ErrorAPIExterna(Exception):
    """La API externa no respondio bien."""


_HEADERS = {"User-Agent": "gestor-inventario/1.0 (python-requests)"}


def _get(url, parametros, timeout, nombre_fuente, headers=None):
    try:
        respuesta = requests.get(
            url,
            params=parametros,
            headers={**_HEADERS, **(headers or {})},
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise ErrorAPIExterna(
            f"{nombre_fuente} tardo demasiado en responder. Intentalo de nuevo."
        )
    except requests.exceptions.ConnectionError:
        raise ErrorAPIExterna(
            f"No se pudo conectar con {nombre_fuente}. Revisa tu conexion a internet."
        )
    except requests.exceptions.RequestException as e:
        raise ErrorAPIExterna(f"Error al consultar {nombre_fuente}: {e}")

    if respuesta.status_code == 404:
        raise ErrorAPIExterna("El juego buscado no existe en BoardGameGeek.")
    if respuesta.status_code != 200:
        raise ErrorAPIExterna(
            f"{nombre_fuente} respondio con el codigo {respuesta.status_code}."
        )

    try:
        return respuesta.json()
    except ValueError:
        raise ErrorAPIExterna(f"La respuesta de {nombre_fuente} no se pudo interpretar.")


def _entero(texto, por_defecto=None):
    try:
        valor = int(float(texto))
        return valor if valor > 0 else por_defecto
    except (TypeError, ValueError):
        return por_defecto


def _texto_plano(contenido, limite=600):
    texto = re.sub(r"<[^>]+>", " ", contenido or "")
    texto = re.sub(r"\s+", " ", html.unescape(texto)).strip()
    if len(texto) > limite:
        texto = texto[:limite].rsplit(" ", 1)[0] + "..."
    return texto


# Wikidata


def _sparql(consulta):
    datos = _get(
        current_app.config["WIKIDATA_SPARQL_URL"],
        {"query": consulta},
        current_app.config["WIKIDATA_TIMEOUT"],
        "Wikidata",
        headers={"Accept": "application/sparql-results+json"},
    )
    return datos.get("results", {}).get("bindings", [])


def _escapar_sparql(texto):
    return texto.replace("\\", "\\\\").replace('"', '\\"')


def _campo(fila, clave):
    return fila.get(clave, {}).get("value")


def buscar_juegos(consulta, limite=10):
    consulta = (consulta or "").strip()
    if not consulta:
        raise ErrorAPIExterna("Escribi el nombre de un juego para buscar.")

    termino = _escapar_sparql(consulta.lower())
    filas = _sparql(
        f"""
        SELECT ?bgg (SAMPLE(?l) AS ?nombre) (MIN(YEAR(?fecha)) AS ?anio) WHERE {{
          ?juego wdt:P2339 ?bgg ; rdfs:label ?l .
          FILTER(LANG(?l) IN ("es", "en"))
          FILTER(CONTAINS(LCASE(?l), "{termino}"))
          OPTIONAL {{ ?juego wdt:P577 ?fecha }}
        }}
        GROUP BY ?bgg
        LIMIT 100
        """
    )

    resultados = []
    for fila in filas:
        bgg_id = _entero(_campo(fila, "bgg"))
        if bgg_id is None:
            continue
        resultados.append(
            {
                "bgg_id": bgg_id,
                "nombre": _campo(fila, "nombre") or "Sin nombre",
                "anio": _campo(fila, "anio") or "s/d",
            }
        )

    buscado = consulta.lower()
    resultados.sort(
        key=lambda r: (
            r["nombre"].lower() != buscado,
            not r["nombre"].lower().startswith(buscado),
            len(r["nombre"]),
            r["nombre"].lower(),
        )
    )
    return resultados[:limite]


def _detalle_wikidata(bgg_id):
    filas = _sparql(
        f"""
        SELECT ?nombre ?min ?max ?edad ?duracion ?editorialLabel ?generoLabel ?imagen
        WHERE {{
          ?juego wdt:P2339 "{int(bgg_id)}" .
          OPTIONAL {{ ?juego rdfs:label ?nombre . FILTER(LANG(?nombre) = "en") }}
          OPTIONAL {{ ?juego wdt:P1872 ?min }}
          OPTIONAL {{ ?juego wdt:P1873 ?max }}
          OPTIONAL {{ ?juego wdt:P2899 ?edad }}
          OPTIONAL {{ ?juego wdt:P2047 ?duracion }}
          OPTIONAL {{ ?juego wdt:P123 ?editorial }}
          OPTIONAL {{ ?juego wdt:P136 ?genero }}
          OPTIONAL {{ ?juego wdt:P18 ?imagen }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
        }}
        LIMIT 20
        """
    )
    if not filas:
        raise ErrorAPIExterna("No se encontraron datos para ese juego.")

    def primero(clave):
        for fila in filas:
            valor = _campo(fila, clave)
            if valor:
                return valor
        return None

    minimos = [_entero(_campo(f, "min")) for f in filas]
    maximos = [_entero(_campo(f, "max")) for f in filas]
    minimos = [v for v in minimos if v]
    maximos = [v for v in maximos if v]

    return {
        "bgg_id": int(bgg_id),
        "nombre": primero("nombre") or "Sin nombre",
        "editorial": primero("editorialLabel"),
        "categoria": primero("generoLabel"),
        "min_jugadores": min(minimos) if minimos else None,
        "max_jugadores": max(maximos) if maximos else None,
        "edad_minima": _entero(primero("edad")),
        "duracion_minutos": _entero(primero("duracion")),
        "imagen_url": primero("imagen"),
        "descripcion": "",
    }


# JSON de la web de BoardGameGeek 


def _detalle_geekdo(bgg_id):
    datos = _get(
        current_app.config["GEEKDO_API_URL"] + "/geekitems",
        {"objecttype": "thing", "objectid": int(bgg_id)},
        current_app.config["BGG_TIMEOUT"],
        "BoardGameGeek",
    )
    item = datos.get("item")
    if not item:
        raise ErrorAPIExterna("BoardGameGeek no devolvio datos para ese juego.")

    enlaces = item.get("links") or {}

    def primer_enlace(tipo):
        lista = enlaces.get(tipo) or []
        return lista[0].get("name") if lista else None

    imagenes = item.get("images") or {}
    return {
        "bgg_id": _entero(item.get("objectid")) or int(bgg_id),
        "nombre": item.get("name") or "Sin nombre",
        "editorial": primer_enlace("boardgamepublisher"),
        "categoria": primer_enlace("boardgamecategory"),
        "min_jugadores": _entero(item.get("minplayers")),
        "max_jugadores": _entero(item.get("maxplayers")),
        "edad_minima": _entero(item.get("minage")),
        "duracion_minutos": _entero(item.get("maxplaytime"))
        or _entero(item.get("minplaytime")),
        "imagen_url": imagenes.get("original") or item.get("imageurl"),
        "descripcion": _texto_plano(item.get("description")),
    }


def obtener_detalle(bgg_id):
    try:
        return _detalle_geekdo(bgg_id)
    except ErrorAPIExterna as e:
        current_app.logger.warning(
            "Fallo el detalle de BGG para %s (%s); se usa Wikidata.", bgg_id, e
        )
    except Exception as e:
        current_app.logger.warning(
            "Respuesta inesperada de BGG para %s (%s); se usa Wikidata.", bgg_id, e
        )
    return _detalle_wikidata(bgg_id)

# Mesa Chica - Gestor de Inventario

Sistema de gestion de inventario para una tienda de juegos de mesa.

Trabajo practico integrador de **Analisis y Metodologias de Sistemas**
(Analista de Sistemas, DA VINCI). Profesor: Florencio Elias Contrera.

## Objetivo del sistema

Administrar el catalogo de juegos de mesa de la tienda y controlar el stock
disponible, registrando las altas, bajas y modificaciones de productos junto
con los ingresos de mercaderia, las ventas y las bajas por rotura o perdida.
Busca que el personal conozca en todo momento que productos hay y en que
cantidad, evitando vender unidades inexistentes, y que la administracion
detecte a tiempo los productos que necesitan reposicion.

## Tecnologias

| Requisito del parcial | Donde esta implementado |
|---|---|
| Desarrollo web con Flask | `app.py` y la carpeta `routes/` (blueprints) |
| SQLAlchemy como ORM | `models.py` |
| Base de datos SQLite | `instance/inventario.db`, configurable por `DATABASE_URL` |
| Consumo de APIs | `services/bgg.py` (Wikidata y BoardGameGeek, JSON) y `services/cotizacion.py` (dolar, JSON) |
| Inicio de sesion con Flask | `routes/auth.py` con Flask-Login |
| Inicio de sesion con Google | `routes/auth.py` con Authlib (OAuth 2.0) |
| Manejo de excepciones | Bloques `try/except` en rutas y servicios, y paginas de error 404, 403 y 500 |
| Variables de entorno | `config.py` + `.env` (ver `.env.example`) |
| Hosting en Render | `gunicorn app:app`, `requirements.txt`, `.python-version` y `ProxyFix` |

## Estructura del proyecto

```
gestor_inventario/
├── app.py                  # Aplicacion principal (gunicorn app:app)
├── config.py               # Configuracion leida de variables de entorno
├── extensions.py           # db, login_manager y oauth
├── models.py               # Modelos del ORM: Usuario, Juego, Proveedor, Movimiento
├── decoradores.py          # Control de autorizacion por rol
├── seed.py                 # Datos iniciales
├── requirements.txt
├── .python-version         # Version de Python que usa Render
├── .env.example            # Plantilla de variables (sin credenciales reales)
├── .gitignore
├── routes/
│   ├── auth.py             # Login local y login con Google
│   ├── inventario.py       # Tablero, CRUD de juegos, proveedores, usuarios
│   ├── movimientos.py      # Ingresos, ventas y bajas de stock
│   ├── reportes.py         # Reportes por periodo y alertas
│   └── catalogo.py         # Consumo de las APIs externas
├── services/
│   ├── bgg.py              # Busqueda e importacion de juegos
│   └── cotizacion.py       # Cliente de la API de cotizacion del dolar
├── templates/              # Plantillas Jinja2
│   └── errores/            # Paginas 404, 403 y 500
└── static/css/estilos.css  # Identidad visual propia
```

## Como levantarlo en local

1. Crear y activar el entorno virtual:

   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac o Linux
   ```

2. Instalar las dependencias:

   ```
   pip install -r requirements.txt
   ```

3. Crear el archivo `.env` a partir de la plantilla:

   ```
   copy .env.example .env       # Windows
   cp .env.example .env         # Mac o Linux
   ```

   Completar `SECRET_KEY`, `ADMIN_PASSWORD` y, si se quiere probar el login
   con Google, `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`. Sin las
   credenciales de Google el boton no se muestra y se usa el login normal.

4. Levantar el servidor:

   ```
   python app.py
   ```

5. Entrar a `http://127.0.0.1:5000` (no `localhost`: Google compara la URL
   de retorno de forma literal).

La primera vez el sistema crea la base de datos, el usuario administrador
definido en el `.env` y algunos juegos de ejemplo.

En Mac, el Receptor AirPlay usa el puerto 5000. Si con la app apagada
`http://127.0.0.1:5000` responde 403, es AirPlay: se desactiva en
Configuracion del Sistema > General > AirDrop y Handoff.

## Despliegue en Render

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app` (el archivo `app.py` y la variable
  `app` que esta adentro).
- **Variables de entorno:** `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`,
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `FLASK_DEBUG=False`. Las demas
  tienen valor por defecto en `config.py`.
- **ProxyFix:** Render atiende el https en un proxy delante de la aplicacion.
  `app.py` envuelve la app con `ProxyFix` para que las URLs se armen con
  https; sin eso Google rechaza el callback del login.
- **Google Cloud Console:** agregar `https://<servicio>.onrender.com` como
  origen autorizado y `https://<servicio>.onrender.com/auth/callback` como URI
  de redireccionamiento, sin borrar las de desarrollo.
- **Persistencia:** en el plan gratuito el disco es efimero. Cada reinicio
  borra el SQLite y `seed.py` vuelve a crear el administrador y los juegos de
  ejemplo. Para conservar los datos haria falta una base PostgreSQL externa,
  que `config.py` ya admite mediante `DATABASE_URL`.

## Roles

- **Administrador**: gestiona el catalogo de juegos, los proveedores y los
  usuarios, importa datos desde BoardGameGeek y accede a los reportes.
- **Empleado**: consulta el stock y registra movimientos (ingresos, ventas y
  bajas). No puede modificar el catalogo ni ver los reportes. Las cuentas de
  Google nuevas se registran como empleado si `PERMITIR_ALTA_CON_GOOGLE=True`.

## APIs externas que consume

- **Wikidata** (`https://query.wikidata.org/sparql`): busca juegos por nombre
  con una consulta SPARQL. Cada juego trae su ID de BoardGameGeek.
- **BoardGameGeek** (`https://api.geekdo.com/api/geekitems`): con ese ID trae
  editorial, categoria, cantidad de jugadores, edad minima, duracion, imagen
  y descripcion para precargar el formulario de alta. Es el JSON que usa la
  web de BGG; si no responde, los datos se completan desde Wikidata.

  La XML API2 oficial de BoardGameGeek (`/xmlapi2`) ahora exige registrar la
  aplicacion y enviar un token, por eso se reemplazo por estas dos fuentes,
  que no necesitan clave.
- **DolarAPI** (`https://dolarapi.com/v1/dolares/oficial`): cotizacion del
  dolar oficial, util porque buena parte de los juegos son importados. Se
  consume desde la ruta `/api/cotizacion`, que devuelve JSON con `jsonify`.

Si cualquiera de las APIs falla, el sistema muestra un mensaje claro y sigue
funcionando.

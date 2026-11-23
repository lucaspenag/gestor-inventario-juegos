# Mesa Chica - Gestor de inventario

Sistema de gestion de inventario para una tienda de juegos de mesa.

Trabajo practico integrador de Analisis y Metodologias de sistemas.

## Objetivo del sistema

Administrar el catalogo de juegos de mesa de la tienda y controlar el stock disponible, registrando las altas, bajas y modificaciones de productos junto con los ingresos de mercaderia, las ventas y las bajas por rotura o perdida.

## Como levantarlo

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
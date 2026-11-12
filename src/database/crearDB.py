"""Crea la base de datos de nekonometrics con las tres tablas requeridas.

Uso:
    python -m src.database.crearDB

Seguro de re-ejecutar: no borra ni modifica datos existentes.
"""
import sqlite3
import sys
from pathlib import Path

from src.utils.paths import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache_indicadores (
    indicador   TEXT PRIMARY KEY,
    valor       REAL,
    last_update TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cache_macro_precios (
    variable TEXT NOT NULL,
    -- Ej: 'AVGC.L', 'FTAW.AS', 'USD', 'UF'
    fecha    DATE NOT NULL
             CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    valor    REAL,
    PRIMARY KEY (variable, fecha)
);

CREATE TABLE IF NOT EXISTS transacciones (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    tipo   TEXT NOT NULL CHECK (tipo = 'compra'),   -- este sistema no vende
    fecha  DATE NOT NULL
           CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),

    -- cantidad = número de ACCIONES (no euros, no dólares)
    cantidad REAL NOT NULL,

    -- Bloque USD: el monto original de la operación
    precio_ejecucion_usd REAL NOT NULL,
    comision_usd         REAL NOT NULL,
    total_usd            REAL NOT NULL,

    -- Bloque CLP: valor_usd es el TIPO DE CAMBIO (CLP por 1 USD) -> se MULTIPLICA
    valor_usd            REAL NOT NULL,
    precio_ejecucion_clp REAL NOT NULL,
    comision_clp         REAL NOT NULL,
    total_clp            REAL NOT NULL,

    -- Bloque UF: valor_uf es el TIPO DE CAMBIO (CLP por 1 UF) -> se DIVIDE
    valor_uf             REAL NOT NULL,
    precio_ejecucion_uf  REAL NOT NULL,
    comision_uf          REAL NOT NULL,
    total_uf             REAL NOT NULL,

    -- Espejo FTAW: valor_ftaw es el PRECIO de 1 acción (USD) -> se DIVIDE
    valor_ftaw    REAL NOT NULL,
    cantidad_ftaw REAL NOT NULL
);
"""

TABLAS = ("cache_indicadores", "cache_macro_precios", "transacciones")


def _tablas(conn: sqlite3.Connection) -> set[str]:
    return {
        fila[0]
        for fila in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }


def inicializar_db() -> int:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        antes = _tablas(conn)
        conn.executescript(SCHEMA)
        conn.commit()
        despues = _tablas(conn)

        # Detector de drift: si la tabla ya existía sin las restricciones nuevas
        sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'transacciones'"
        ).fetchone()
    finally:
        conn.close()

    for tabla in TABLAS:
        print(f"  {tabla:<22} {'ya existía' if tabla in antes else 'creada'}")

    if sql and "GLOB" not in sql[0]:
        print(
            "\nAVISO: 'transacciones' ya existía sin las restricciones nuevas "
            "de fecha y tipo.\n"
            "       Este script no altera tablas existentes: los CHECK sólo "
            "aplican a bases nuevas.",
            file=sys.stderr,
        )

    faltan = [t for t in TABLAS if t not in despues]
    if faltan:
        print(f"ERROR: faltan tablas: {', '.join(faltan)}", file=sys.stderr)
        return 1

    print(f"\nBase lista en: {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(inicializar_db())
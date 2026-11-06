import sqlite3
from src.utils.paths import DB_PATH

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE transacciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('compra', 'venta')) NOT NULL,
        fecha DATE NOT NULL,        

        -- Valores en USD
        cantidad REAL NOT NULL,   
        precio_ejecucion_usd REAL NOT NULL,
        comision_usd REAL NOT NULL,
        total_usd REAL NOT NULL,
                    
        -- Equivalentes en CLP
        valor_eur REAL NOT NULL,
        precio_ejecucion_clp REAL NOT NULL,
        comision_clp REAL NOT NULL,
        total_clp REAL NOT NULL,               
               
        -- Equivalentes en UF        
        valor_uf REAL NOT NULL,
        precio_ejecucion_uf REAL NOT NULL,
        comision_uf REAL NOT NULL,
        total_uf REAL NOT NULL,

        -- Equivalentes en FTAW (iShares FTSE All-World UCITS ETF)
        valor_ftaw REAL NOT NULL,
        cantidad_ftaw REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()


inicializar_db()
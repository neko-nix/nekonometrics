import os
import sqlite3
import sys
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from src.utils.paths import DB_PATH
from src.visualizacion import rendimiento_historico


try:
    rendimiento_historico.inicializar_db_long()
except Exception as e:
    print(f"Error crítico al inicializar la base de datos: {e}")
    sys.exit(1) 


try:
    conn = sqlite3.connect(DB_PATH)
    df_tx_inicial = pd.read_sql_query("SELECT * FROM transacciones", conn)
except Exception as e:
    print(f"Error crítico al leer la base de datos (¿está bloqueada?): {e}")
    sys.exit(1) 
finally:
    conn.close()


if df_tx_inicial.empty:
    print("Operación abortada: La tabla de transacciones está vacía o no existe.")

    sys.exit(1) 


try:
    df_tx_inicial['fecha'] = pd.to_datetime(df_tx_inicial['fecha'])
    fecha_desde_donde_actualizar = df_tx_inicial['fecha'].min()
    
    tickers_usuario = [t + ".L" if not t.endswith(".L") else t for t in df_tx_inicial['ticker'].unique()]
    lista_descarga_completa = list(set(tickers_usuario + ['FTAW.AS']))
    
    print("\nIniciando sincronización de mercado...")
    
    
    rendimiento_historico.actualizar_cache_long(
        variables_tickers=lista_descarga_completa, 
        fecha_inicio=fecha_desde_donde_actualizar
    )
    
    print("Sincronización de mercado completada con éxito.")

except Exception as e:
    print(f"Error crítico durante la descarga de datos de mercado: {e}")    
    sys.exit(1) 
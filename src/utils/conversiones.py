import sys
import sqlite3
import requests
import yfinance as yf
from datetime import datetime, timedelta
from src.utils.paths import DB_PATH

def execute_query(query, params=(), fetch=False, commit=False):
    """Helper genérico para interactuar con la base de datos de forma segura."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetch:
            return cursor.fetchone()

def init_db():
    """Inicializa la tabla de caché si no existe."""
    execute_query("""
        CREATE TABLE IF NOT EXISTS cache_indicadores (
            indicador TEXT PRIMARY KEY,
            valor REAL,
            last_update REAL
        )
    """, commit=True)

def get_cached_indicator(indicador, ttl_seconds):
    """
    Intenta obtener un indicador del caché. 
    Retorna (valor, es_valido). Soporta migración de tipos str -> float.
    """
    res = execute_query(
        "SELECT valor, last_update FROM cache_indicadores WHERE indicador = ?", 
        (indicador,), 
        fetch=True
    )
    if not res:
        return None, False
    
    valor, last_update = res
    
    if isinstance(last_update, str):
        try:
            last_update = datetime.fromisoformat(last_update).timestamp()
        except ValueError:

            return valor, False
    
    es_valido = (datetime.now().timestamp() - last_update) < ttl_seconds
    return valor, es_valido

def save_indicator(indicador, valor):
    """Guarda o actualiza un indicador en el caché con el timestamp actual."""
    execute_query("""
        INSERT OR REPLACE INTO cache_indicadores (indicador, valor, last_update) 
        VALUES (?, ?, ?)
    """, (indicador, valor, datetime.now().timestamp()), commit=True)


def fetch_from_yfinance(ticker):
    """Llamada segura a yfinance con manejo de excepciones."""
    try:
        return yf.Ticker(ticker).fast_info['last_price']
    except Exception as e:
        print(f"Error al obtener {ticker} desde Yahoo Finance: {e}")
        return None


def get_indicator(indicador, ticker, ttl_minutes=15):
    """
    Función unificada para monedas y ETFs.
    Usa caché y hace el fallback a yfinance si el caché expiró.
    """
    ttl_seconds = ttl_minutes * 60
    valor, es_valido = get_cached_indicator(indicador, ttl_seconds)
    
    if es_valido:
        return valor
    

    print(f"Obteniendo valor de {indicador} desde el mercado...")
    nuevo_valor = fetch_from_yfinance(ticker)
    
    if nuevo_valor is not None:
        save_indicator(indicador, nuevo_valor)
        return nuevo_valor
    

    if valor is not None:
        print(f"Alerta: Falló la actualización de {indicador}. Usando valor expirado en caché.")
        return valor
    
    raise RuntimeError(f"No se pudo obtener el valor de {indicador} y no hay caché disponible.")



def get_usd():
    return get_indicator('USD', 'CLP=X', ttl_minutes=15)

def get_eur():
    return get_indicator('EUR', 'EURCLP=X', ttl_minutes=15)

def get_vt():
    return get_indicator('VT', 'VT', ttl_minutes=60)

def get_vwce():
    return get_indicator('FTAW', 'FTAW.AS', ttl_minutes=60)


def get_uf():

    valor, es_valido = get_cached_indicator('UF', ttl_seconds=12 * 3600)
    if es_valido:
        return valor
    
    print("Obteniendo el valor de la UF de hoy desde mindicador.cl...")
    url = "https://mindicador.cl/api/uf"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        nuevo_valor = float(response.json()['serie'][0]['valor'])
        save_indicator('UF', nuevo_valor)
        return nuevo_valor
        
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"\nError al obtener la UF automáticamente: {e}")
        

        if valor is not None:
            print("Usando el último valor de UF registrado en el caché local como plan de contingencia.")
            return valor
        

        if sys.stdin.isatty():
            while True:
                try:
                    entrada = input("Introduce el valor de la UF manualmente: ").strip()
                    nuevo_valor = float(entrada.replace(',', '.'))
                    save_indicator('UF', nuevo_valor)
                    return nuevo_valor
                except ValueError:
                    print("Entrada inválida. Por favor, ingresa un número válido.")
        else:
            raise RuntimeError("La API de la UF falló, no hay caché previo y el entorno no es interactivo para solicitar entrada manual.")


if __name__ == "__main__":
    init_db()
    print(f"Dólar:  ${get_usd():,.2f} CLP")
    print(f"Euro:   ${get_eur():,.2f} CLP")
    print(f"VT:     ${get_vt():,.2f} USD")
    print(f"FTAW:   ${get_vwce():,.2f} USD")
    print(f"UF:     ${get_uf():,.2f} CLP")
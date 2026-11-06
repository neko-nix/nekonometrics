import sqlite3
import yfinance as yf
from src.utils.paths import DB_PATH, DATA_DIR
import pandas as pd
from tabulate import tabulate
from src.utils import conversiones

def valoresActuales(precios):

    #tickers_validos = ("AVWC.DE", "AVWS.DE", "AVEM.DE", "AVUS.DE", "AVEU.DE", "AVPE.DE")
    tickers_validos = ("AVGC.L", "AVGS.L", "AVEM.L")
    conn = sqlite3.connect(DB_PATH)
    query = f"""
            SELECT
              ticker,
                SUM(cantidad)  as cantidad,
                SUM(cantidad_ftaw) as cantidadVT,
                SUM(total_usd) as total_usd_inicial,
                SUM(total_clp) as total_clp_inicial,
                SUM(total_uf)  as total_uf_inicial
              FROM transacciones
              WHERE ticker IN {tickers_validos}
              GROUP BY ticker
            """
    df = pd.read_sql_query(query, conn)
    conn.close()


    df['unitarioUSD'] = df['ticker'].map(precios)
    df['totalUSD'] = df['cantidad'] * df['unitarioUSD']
    

    valorDolar = conversiones.get_usd()
    valorUF = conversiones.get_uf()
    valorVT = conversiones.get_vwce()

    df["totalCLP"] = df['totalUSD'] * valorDolar
    df["totalUF"]  = df['totalCLP'] / valorUF
    df["totalVT"] = df["cantidadVT"] * valorVT

    df["gananciaUSD"] = df["totalUSD"] - df["total_usd_inicial"]
    df["gananciaCLP"] = df["totalCLP"] - df["total_clp_inicial"]
    df["gananciaUF"]  = df["totalUF"] -  df["total_uf_inicial"]
    df["gananciaVT"] = df["totalVT"] - df["total_usd_inicial"]

    df["variaciónUSD"] = df["gananciaUSD"] / df["total_usd_inicial"]
    df["variaciónCLP"] = df["gananciaCLP"] / df["total_clp_inicial"]
    df["variaciónUF"] = df["gananciaUF"] / df["total_uf_inicial"]
    df["variaciónVT"] = df["gananciaVT"] / df["total_uf_inicial"]

    df["proporcionActual"] = df["totalUSD"] / df["totalUSD"].sum()



    
    print("\n" + "="*31 + " VALORES DE REFERENCIA " + "="*31)
    print(f" Dólar Mercado:  $    {valorDolar:,.2f}")
    print(f" Valor UF:       $ {valorUF:,.2f}")
    print(f" Valor FTAW:     $      {valorVT:,.2f}")

    df_print = pd.DataFrame()
    df_print['Ticker'] = df['ticker']
    df_print['Cantidad'] = df['cantidad']
    df_print['Precio USD'] = df['unitarioUSD'].map(lambda x: f"$ {x:,.2f}")
    df_print['Inicial USD'] = df['total_usd_inicial'].map(lambda x: f"$ {x:,.2f}")
    df_print['Actual USD'] = df['totalUSD'].map(lambda x: f"$ {x:,.2f}")
    df_print['Ganancia USD'] = df['gananciaUSD'].map(lambda x: f"$ {x:+,.2f}")
    df_print['Var %'] = df['variaciónUSD'].map(lambda x: f"{x:+.2%}")
    df_print['Prop %'] = df['proporcionActual'].map(lambda x: f"{x:.1%}")

    print("\n" + "="*31 + " DESGLOSE POR ACTIVO (USD) " + "="*31)
    print(tabulate(df_print, headers="keys", tablefmt="rounded_grid", numalign='right', stralign='right', showindex=False))


    tot_ini_usd = df['total_usd_inicial'].sum()
    tot_act_usd = df['totalUSD'].sum()
    gan_usd = df['gananciaUSD'].sum()
    var_usd = (gan_usd / tot_ini_usd) if tot_ini_usd else 0


    tot_ini_clp = df['total_clp_inicial'].sum()
    tot_act_clp = df['totalCLP'].sum()
    gan_clp = df['gananciaCLP'].sum()
    var_clp = (gan_clp / tot_ini_clp) if tot_ini_clp else 0


    tot_ini_uf = df['total_uf_inicial'].sum()
    tot_act_uf = df['totalUF'].sum()
    gan_uf = df['gananciaUF'].sum()
    var_uf = (gan_uf / tot_ini_uf) if tot_ini_uf else 0

    resumen_data = [
        [
            "USD", 
            f"$ {tot_ini_usd:,.0f}",
            f"$ {tot_act_usd:,.0f}",
            f"$ {gan_usd:+,.0f}",
            f"{var_usd:+.2%}"
        ],
        [
            "CLP", 
            f"$ {tot_ini_clp:,.0f}",
            f"$ {tot_act_clp:,.0f}",
            f"$ {gan_clp:+,.0f}",
            f"{var_clp:+.2%}"
        ],
        [
            "UF", 
            f"UF {tot_ini_uf:,.0f}",
            f"UF {tot_act_uf:,.0f}",
            f"UF {gan_uf:+,.0f}",
            f"{var_uf:+.2%}"
        ]
    ]

    print("\n" + "="*28 + " RESUMEN GLOBAL DEL PORTAFOLIO " + "="*28)
    print(tabulate(resumen_data, 
                   headers=["Moneda", "Valor Inicial", "Valor Actual", "Ganancia / Pérdida", "Variación Total"], 
                   tablefmt="rounded_grid", 
                   numalign='right', 
                   stralign='right'))
    print("="*87 + "\n")

    return df
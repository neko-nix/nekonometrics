import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
from tabulate import tabulate


from src.utils import conversiones, pesoEmergentes
from src.utils.paths import DATA_DIR
from src.utils.portafolio import valoresActuales

pd.set_option('future.no_silent_downcasting', True)

#tickers_list = ["AVWC.DE", "AVWS.DE", "AVEM.DE"]
tickers_list = ["AVGC.L", "AVGS.L", "AVEM.L"]

print("Descargando datos de mercado desde Yahoo Finance...")
try:
    df_precios = yf.download(tickers_list, period="5d", group_by='ticker', progress=True, timeout=30)
except Exception as e:
    print(f"Error crítico al conectar con Yahoo Finance: {e}")
    sys.exit(1)

if df_precios.empty:
    print("Error: No se obtuvieron datos de mercado.")
    sys.exit(1)


precios = {}
for t in tickers_list:
    try:
        series_close = df_precios[t]['Close']
        series_validas = series_close.dropna()
        if not series_validas.empty:
            precios[t] = series_validas.iloc[-1]
        else:
            print(f"Error: No hay datos de precio recientes para {t}")
            sys.exit(1)
    except KeyError:
        print(f"Error: Ticker {t} no encontrado en el DataFrame.")
        sys.exit(1)


ruta_ftaw = Path("data/ftaw_holdings.csv")
if not ruta_ftaw.exists():
    print(f"Error: No se encontró {ruta_ftaw}. Ejecuta la descarga de FTAW primero.")
    sys.exit(1)

pesoEmergentesVal = pesoEmergentes.obtener_peso_emergentes_msci(str(ruta_ftaw))
pesoDesarrollados = 1 - pesoEmergentesVal

print(f"Asignación Dinámica MSCI -> Desarrollados: {pesoDesarrollados:.2%} | Emergentes: {pesoEmergentesVal:.2%}")


proporcionesTickers = [
    ["AVGC.L", pesoDesarrollados / 2],  # Core Large Cap
    ["AVGS.L", pesoDesarrollados / 2],  # Small Cap Value
    ["AVEM.L", pesoEmergentesVal],      # Emerging Markets
]
targetTotal = pd.DataFrame(proporcionesTickers, columns=["ticker", "proporción_ideal"])


etf_prices = {t: precios[t] for t in tickers_list}
activos_raw = valoresActuales(etf_prices)
activos = valoresActuales(etf_prices)


#activos = activos_raw.rename(columns={
#    'totalUSD': 'totalUSD',
#    'unitarioUSD': 'unitarioEUR'
#})
activos = activos.sort_values('ticker')

totalActualUSD = activos["totalUSD"].sum()


activos = pd.merge(activos, targetTotal, on="ticker", how="outer").fillna(0)


dolarObservado = conversiones.get_usd() 
valorUF = conversiones.get_uf()


activos["totalUF"] = (activos["totalUSD"] * dolarObservado) / valorUF


comisionWiseProporcional = 0.55 / 100  

while True:
    print("\n" + "="*60)
    print(" INYECCIÓN DE NUEVO CAPITAL ")
    print("="*60)
    
    montoInvertirUSD = input("Ingrese monto NETO a invertir que ya está en el Broker (USD): ").strip()
    try:
        montoInvertirUSD = float(montoInvertirUSD)
        if montoInvertirUSD < 0:
            print("El monto no puede ser negativo.")
            continue
        break
    except ValueError:
        print(f"'{montoInvertirUSD}' no es un número válido.")


montoInvertirCLP_inicial = (montoInvertirUSD * dolarObservado) / (1 - comisionWiseProporcional)
comisionWisePagadaCLP = (montoInvertirCLP_inicial * comisionWiseProporcional) + (1.17*dolarObservado)

print(f"\nFlujo de Origen (Wise):")
print(f" -> Tuviste que transferir desde Chile: ${montoInvertirCLP_inicial:,.0f} CLP")
print(f" -> Comisión de Wise descontada:       ${comisionWisePagadaCLP:,.0f} CLP (~ ${comisionWisePagadaCLP/dolarObservado:.2f} USD)")
print(f" -> Efectivo limpio en Broker:        ${montoInvertirUSD:,.2f} USD")


activos['variacionProporcion'] = (activos["proporcionActual"] - activos['proporción_ideal']) / activos['proporción_ideal']


activos['inversion_ideal'] = (totalActualUSD + montoInvertirUSD) * activos['proporción_ideal']
activos['monto_comprar_crudo'] = np.where(activos['inversion_ideal'] - activos['totalUSD'] > 0, activos['inversion_ideal'] - activos['totalUSD'], 0.0)

totalComprarFiltrado = activos['monto_comprar_crudo'].sum()


if totalComprarFiltrado > 0:
    activos['proporcionCompras'] = activos['monto_comprar_crudo'] / totalComprarFiltrado
    activos['monto_comprar_bruto'] = montoInvertirUSD * activos['proporcionCompras']
else:
    activos['proporcionCompras'] = 0.0
    activos['monto_comprar_bruto'] = 0.0


def obtener_neto_y_comision(monto_bruto):
    if monto_bruto <= 0:
        return 0.0, 0.0
    
    if monto_bruto <= 2501.25:
        if monto_bruto <= 1.7:
            return 0.0, monto_bruto
        return monto_bruto - 1.7, 1.7
    else:
        neto = monto_bruto / 1.0005
        comision = monto_bruto - neto
        return neto, comision


netos_y_comisiones = activos['monto_comprar_bruto'].apply(obtener_neto_y_comision)
activos['monto_invertir'] = [x[0] for x in netos_y_comisiones]
activos['comisión_pagada'] = [x[1] for x in netos_y_comisiones]


activos["cantidadComprar"] = activos['monto_invertir'] / activos['unitarioUSD']


activos['inversión_nueva'] = activos['totalUSD'] + activos['monto_invertir']
activos['proporción_nueva'] = activos['inversión_nueva'] / activos['inversión_nueva'].sum()
activos["totalUF_nuevo_float"] = (activos["inversión_nueva"] * dolarObservado) / valorUF


ruta_salida_csv = Path(DATA_DIR) / "ultimosDatos.csv"
ruta_salida_csv.parent.mkdir(parents=True, exist_ok=True)
activos.to_csv(ruta_salida_csv, index=False)


totales = [
    'totalUSD', 'proporcionActual', 'proporción_ideal', 'monto_invertir', 
    'cantidadComprar', 'comisión_pagada', 'inversión_nueva', 'proporción_nueva', 
    'totalUF', 'totalUF_nuevo_float'
]
activos.loc['TOTAL', totales] = activos[totales].sum()


activos.loc['TOTAL', 'ticker'] = 'TOTAL'
activos.loc['TOTAL'] = activos.loc['TOTAL'].fillna(0)
activos.loc['TOTAL', 'variacionProporcion'] = np.nan
activos.loc['TOTAL', 'Status'] = ''


orden_visual = ["AVGC.L", "AVGS.L", "AVEM.L", "TOTAL"]
activos['ticker'] = pd.Categorical(activos['ticker'], categories=orden_visual, ordered=True)
activos = activos.sort_values('ticker')


activos['totalUSD'] = activos['totalUSD'].map("$ {:,.2f}".format)
activos['inversión_nueva'] = activos['inversión_nueva'].map("$ {:,.2f}".format)
activos['variacionProporcion'] = activos['variacionProporcion'].map(lambda x: f"{x:.2%}" if pd.notna(x) else "")
activos['proporcionActual'] = activos['proporcionActual'].map("{:,.2%}".format)
activos['proporción_nueva'] = activos['proporción_nueva'].map("{:,.2%}".format)
activos['proporción_ideal'] = activos['proporción_ideal'].map("{:,.2%}".format)
activos['monto_invertir'] = activos['monto_invertir'].map("$ {:,.2f}".format)
activos['cantidadComprar'] = activos['cantidadComprar'].map("{:,.2f}".format)
activos['comisión_pagada'] = activos['comisión_pagada'].map("$ {:,.2f}".format)
activos['totalUF_nuevo_formatted'] = activos['totalUF_nuevo_float'].map("{:,.2f} UF".format)

print("\n" + "="*95)
print(" PROPUESTA DE RECOMPRA MAESTRA (AJUSTADA A COMISIONES REALES DE IBKR)")
print("="*95)

print(tabulate(
    activos[[
        'ticker',
        'totalUSD',
        'proporcionActual',
        'proporción_ideal',
        'variacionProporcion',
        'monto_invertir',
        'cantidadComprar',
        'comisión_pagada',
        'inversión_nueva',
        'proporción_nueva',
        'totalUF_nuevo_formatted'
    ]],
    headers=[
        'Ticker',
        'Total (USD)',
        'Act. %',
        'Ideal %',
        'Desviación',
        'Monto Neto',
        'Acciones a Comp.',
        'Comisión Broker',
        'Post Operación',
        'Nueva %',
        'Proyección UF'
    ], 
    tablefmt='rounded_grid',
    numalign='right',
    stralign='right',
    showindex=False
))
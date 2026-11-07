import os
import sqlite3
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
from src.utils.paths import DB_PATH
import random

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def inicializar_db_long():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cache_macro_precios (
        variable TEXT,      -- Ej: 'AVGC.L' 'FTAW.AS' 'USD' 'UF'
        fecha DATE,         -- Formato: YYYY-MM-DD
        valor REAL,         
        PRIMARY KEY (variable, fecha)
    )
    """)
    conn.commit()
    conn.close()



def actualizar_cache_long(variables_tickers, fecha_inicio):
    inicializar_db_long()
    conn = sqlite3.connect(DB_PATH)
    fecha_hoy = pd.to_datetime('today').strftime('%Y-%m-%d')
    
    for var in variables_tickers:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(fecha) FROM cache_macro_precios WHERE variable = ?", (var,))
        ultima_fecha = cursor.fetchone()[0]
        
        descargar_desde = fecha_inicio.strftime('%Y-%m-%d')
        if ultima_fecha and ultima_fecha >= fecha_hoy:
            print(f"[{var}] ya está actualizado en caché hasta {ultima_fecha}.")
            continue
        elif ultima_fecha:
            descargar_desde = (pd.to_datetime(ultima_fecha) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        print(f"⏳ Descargando {var} desde {descargar_desde}...")
        try:
            df_yf = yf.download(var, start=descargar_desde, end=fecha_hoy, progress=False)
            if not df_yf.empty:
                df_yf = df_yf['Close'].reset_index()
                df_yf.columns = ['fecha', 'valor']
                df_yf['variable'] = var
                df_yf['fecha'] = df_yf['fecha'].dt.strftime('%Y-%m-%d')
                
                df_yf[['variable', 'fecha', 'valor']].to_sql(
                    'cache_macro_precios', conn, if_exists='append', index=False
                )
        except Exception as e:
            print(f"Error con yfinance para {var}: {e}")

    for indicador_cl in ['UF', 'USD']:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(fecha) FROM cache_macro_precios WHERE variable = ?", (indicador_cl,))
        ultima_fecha_macro = cursor.fetchone()[0]
        
        descargar_desde_macro = fecha_inicio.strftime('%Y-%m-%d')
        necesita_actualizar = True
        
        if ultima_fecha_macro:
            if ultima_fecha_macro >= fecha_hoy:
                print(f"[{indicador_cl}] ya está actualizado en caché hasta el día de hoy.")
                necesita_actualizar = False
            else:
                descargar_desde_macro = (pd.to_datetime(ultima_fecha_macro) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        if necesita_actualizar:
            anio_inicio = pd.to_datetime(descargar_desde_macro).year
            anio_fin = pd.to_datetime(fecha_hoy).year
            macro_historica_lista = []
            api_endpoint = 'dolar' if indicador_cl == 'USD' else 'uf'
            
            for anio in range(anio_inicio, anio_fin + 1):
                print(f"Consultando {indicador_cl} del año {anio} en mindicador.cl...")
                url = f"https://mindicador.cl/api/{api_endpoint}/{anio}"
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        serie = data.get('serie', [])
                        for dia in serie:
                            fecha_clean = dia['fecha'][:10]
                            macro_historica_lista.append({
                                'variable': indicador_cl,
                                'fecha': fecha_clean,
                                'valor': float(dia['valor'])
                            })
                    else:
                        print(f"Error HTTP {response.status_code} en {indicador_cl} (Año {anio})")
                except Exception as e:
                    print(f"Error de conexión con mindicador.cl para {indicador_cl} ({anio}): {e}")
            
            if macro_historica_lista:
                df_macro = pd.DataFrame(macro_historica_lista)
                df_macro = df_macro[(df_macro['fecha'] >= descargar_desde_macro) & (df_macro['fecha'] <= fecha_hoy)]
                
                if not df_macro.empty:
                    df_macro = df_macro.sort_values('fecha').drop_duplicates(subset=['fecha'])
                    df_macro.to_sql('cache_macro_precios', conn, if_exists='append', index=False)
                    print(f"Guardados {len(df_macro)} días limpios para {indicador_cl} en la base de datos.")
    conn.close()



def calcular_metricas_avanzadas(serie_rentabilidad):
    idx = 1 + (serie_rentabilidad / 100)
    retornos_diarios = idx.pct_change().dropna()
    
    max_acumulado = idx.cummax()
    drawdowns = (idx - max_acumulado) / max_acumulado
    max_dd = drawdowns.min() * 100
    
    dias_totales = (idx.index[-1] - idx.index[0]).days
    rentabilidad_final_pct = serie_rentabilidad.iloc[-1]
    
    cagr = (1 + rentabilidad_final_pct / 100) ** (365.25 / dias_totales) - 1 if dias_totales > 0 else 0
    sharpe = (retornos_diarios.mean() / retornos_diarios.std()) * np.sqrt(252) if retornos_diarios.std() > 0 else 0
    
    retornos_negativos = retornos_diarios[retornos_diarios < 0]
    downside_std = retornos_negativos.std()
    sortino = (retornos_diarios.mean() / downside_std) * np.sqrt(252) if downside_std > 0 else 0
    calmar = cagr / abs(max_dd / 100) if max_dd != 0 else 0
    
    return {
        'CAGR': cagr * 100, 'MaxDD': max_dd, 'Sharpe': sharpe, 'Sortino': sortino, 'Calmar': calmar
    }



def generar_dashboard_premium():
    conn = sqlite3.connect(DB_PATH)
    df_tx = pd.read_sql_query("SELECT * FROM transacciones ORDER BY fecha ASC", conn)
    
    if df_tx.empty:
        print("No hay transacciones en la base de datos.")
        conn.close()
        return

    df_tx['fecha'] = pd.to_datetime(df_tx['fecha'])
    fecha_inicio = df_tx['fecha'].min()
    fecha_fin = pd.to_datetime('today')
    
    df_cache_long = pd.read_sql_query("SELECT * FROM cache_macro_precios WHERE fecha >= ?", conn, params=[fecha_inicio.strftime('%Y-%m-%d')])
    conn.close()
    
    df_cache_long['fecha'] = pd.to_datetime(df_cache_long['fecha'])
    data_precios = df_cache_long.pivot(index='fecha', columns='variable', values='valor')
    
    calendario = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    data_precios = data_precios.reindex(calendario).ffill()

    df_saldos_yo = pd.DataFrame(0.0, index=calendario, columns=df_tx['ticker'].unique())
    df_saldo_bench = pd.Series(0.0, index=calendario, name='BENCHMARK')
    
    cap_invertido_usd = pd.Series(0.0, index=calendario)
    cap_invertido_clp = pd.Series(0.0, index=calendario)
    cap_invertido_uf = pd.Series(0.0, index=calendario)

    for _, tx in df_tx.iterrows():
        fecha = tx['fecha']
        factor = 1 if tx['tipo'] == 'compra' else -1
        
        df_saldos_yo.loc[fecha:, tx['ticker']] += tx['cantidad'] * factor
        df_saldo_bench.loc[fecha:] += tx['cantidad_ftaw'] * factor

        cap_invertido_usd.loc[fecha:] += tx['total_usd'] * factor
        cap_invertido_clp.loc[fecha:] += tx['total_clp'] * factor
        cap_invertido_uf.loc[fecha:] += tx['total_uf'] * factor

    valor_yo_usd = pd.Series(0.0, index=calendario)
    for ticker in df_tx['ticker'].unique():
        ticker_yf = ticker + ".L" if not ticker.endswith(".L") else ticker
        valor_yo_usd += df_saldos_yo[ticker] * data_precios[ticker_yf]

    valor_bench_usd = df_saldo_bench * data_precios['FTAW.AS']
    valor_yo_clp = valor_yo_usd * data_precios['USD']
    valor_bench_clp = valor_bench_usd * data_precios['USD']
    valor_yo_uf = valor_yo_clp / data_precios['UF']
    valor_bench_uf = valor_bench_clp / data_precios['UF']

    df_rendimiento = pd.DataFrame({
        'YO_USD': np.where(cap_invertido_usd > 0, ((valor_yo_usd / cap_invertido_usd) - 1) * 100, 0.0),
        'BENCH_USD': np.where(cap_invertido_usd > 0, ((valor_bench_usd / cap_invertido_usd) - 1) * 100, 0.0),
        'YO_CLP': np.where(cap_invertido_clp > 0, ((valor_yo_clp / cap_invertido_clp) - 1) * 100, 0.0),
        'BENCH_CLP': np.where(cap_invertido_clp > 0, ((valor_bench_clp / cap_invertido_clp) - 1) * 100, 0.0),
        'YO_UF': np.where(cap_invertido_uf > 0, ((valor_yo_uf / cap_invertido_uf) - 1) * 100, 0.0),
        'BENCH_UF': np.where(cap_invertido_uf > 0, ((valor_bench_uf / cap_invertido_uf) - 1) * 100, 0.0)
    }, index=calendario)

    m = {}
    for divisa in ['USD', 'CLP', 'UF']:
        m[divisa] = {
            'yo': calcular_metricas_avanzadas(df_rendimiento[f'YO_{divisa}']),
            'bench': calcular_metricas_avanzadas(df_rendimiento[f'BENCH_{divisa}'])
        }


    pct_yo_usd = df_rendimiento['YO_USD'].iloc[-1]
    pct_yo_clp = df_rendimiento['YO_CLP'].iloc[-1]
    pct_yo_uf = df_rendimiento['YO_UF'].iloc[-1]

    mult_yo_usd = 1 + (pct_yo_usd / 100)
    mult_be_usd = 1 + (df_rendimiento['BENCH_USD'].iloc[-1] / 100)
    mult_yo_clp = 1 + (pct_yo_clp / 100)
    mult_be_clp = 1 + (df_rendimiento['BENCH_CLP'].iloc[-1] / 100)
    mult_yo_uf = 1 + (pct_yo_uf / 100)
    mult_be_uf = 1 + (df_rendimiento['BENCH_UF'].iloc[-1] / 100)
    

    color_pct_usd = "#16a34a" if pct_yo_usd >= 0 else "#dc2626"
    color_pct_clp = "#16a34a" if pct_yo_clp >= 0 else "#dc2626"
    color_pct_uf = "#16a34a" if pct_yo_uf >= 0 else "#dc2626"

    sign_usd = "+" if pct_yo_usd > 0 else ""
    sign_clp = "+" if pct_yo_clp > 0 else ""
    sign_uf = "+" if pct_yo_uf > 0 else ""


    COLOR_YO = '#1e293b'     
    COLOR_BENCH = '#94a3b8'  


    columnas_retorno = ['YO_USD', 'BENCH_USD', 'YO_CLP', 'BENCH_CLP', 'YO_UF', 'BENCH_UF']
    min_absoluto = df_rendimiento[columnas_retorno].min().min()
    max_absoluto = df_rendimiento[columnas_retorno].max().max()


    holgura = (max_absoluto - min_absoluto) * 0.05
    rango_y_fijo = [min_absoluto - holgura, max_absoluto + holgura]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['YO_USD'], name="Nekonometrics (USD)", line=dict(color=COLOR_YO, width=3), visible=True))
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['BENCH_USD'], name="FTAW (USD)", line=dict(color=COLOR_BENCH, width=1.5, dash='dot'), visible=True))
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['YO_CLP'], name="Nekonometrics (CLP)", line=dict(color=COLOR_YO, width=3), visible=False))
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['BENCH_CLP'], name="FTAW (CLP)", line=dict(color=COLOR_BENCH, width=1.5, dash='dot'), visible=False))
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['YO_UF'], name="Nekonometrics (Real UF)", line=dict(color=COLOR_YO, width=3), visible=False))
    fig.add_trace(go.Scatter(x=df_rendimiento.index, y=df_rendimiento['BENCH_UF'], name="FTAW (Real UF)", line=dict(color=COLOR_BENCH, width=1.5, dash='dot'), visible=False))

    fig.update_layout(
        template='plotly_white',
        updatemenus=[
            dict(
                type="buttons", direction="right", active=0, x=0.5, y=1.12, xanchor="center",
                buttons=list([
                    dict(label="🇺🇸 USD", method="update", args=[{"visible": [True, True, False, False, False, False]}, {"yaxis.title.text": "Retorno Neto USD (%)"}]),
                    dict(label="🇨🇱 CLP", method="update", args=[{"visible": [False, False, True, True, False, False]}, {"yaxis.title.text": "Retorno Neto CLP (%)"}]),
                    dict(label="🇨🇱 UF", method="update", args=[{"visible": [False, False, False, False, True, True]}, {"yaxis.title.text": "Retorno Neto UF (%)"}]),
                ]),
            )
        ],
        xaxis_title="Línea de Tiempo",
        yaxis_title="Retorno Neto USD (%)",
        hovermode="x unified",
        margin=dict(t=40, b=40, l=40, r=40),
        

        yaxis=dict(
            range=rango_y_fijo, #
            ticksuffix="%", 
            zeroline=True, 
            zerolinecolor='#475569', 
            zerolinewidth=2, 
            gridcolor='#f1f5f9'
        ),
        
        xaxis=dict(
            showgrid=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    graph_div_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')


    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    fecha_hoy = datetime.now()

    diferencia = relativedelta(fecha_hoy, fecha_inicio)

    anios = diferencia.years
    meses = diferencia.months
    días = diferencia.days


    componentes = []

    if anios == 1:
        componentes.append(f"{anios} Año")
    elif anios > 1:
        componentes.append(f"{anios} Años")

    if meses == 1:
        componentes.append(f"{meses} Mes")
    elif meses > 1:
        componentes.append(f"{meses} Meses")

    if días == 1:
        componentes.append(f"{días} Día")
    elif días > 1:
        componentes.append(f"{días} Días")


    if not componentes:
        texto_final = "0 Días" 
    elif len(componentes) == 1:
        texto_final = componentes[0]
    else:

        texto_final = ", ".join(componentes[:-1]) + " y " + componentes[-1]



    #anios = f"{anios} Año," if anios == 1 else f"{anios} Años,"



    frases = [
        "La paciencia es más rentable que la avaricia.",
        "Yo no veo pérdidas, yo veo ofertas.",
        "A todos les gusta renta variable hasta que empieza a variar para abajo.",
        "Compra caro, vende barato.",
        "No intento predecir el mercado, intento olvidarme de él.",
        "Al final Neko Money es un Excel pero automático.",
        "Esto empezó como una calculadora de rebalanceo. Luego ocurrieron cosas.",
        "Si tengo que mirar el portafolio todos los días es porque algo hice mal.",
        "Ahora sólo miro la página para ver si aún funciona.",
        "Si la página no se actualiza cuando corresponde, asuman que es porque se me cayó el internet.",
        "La automatización existe para que pueda dedicarme a cosas más interesantes.",
        "Me demoré más en ajustar los colores de la página que en programar todos los cálculos matemáticos.",
    ]

    frase_del_dia = random.choice(frases)

    
    inflacion_periodo = ((data_precios['UF'].iloc[-1] / data_precios['UF'].iloc[0]) - 1) * 100
    cagr_usd = m['USD']['yo']['CAGR']
    color_cagr = "#16a34a" if cagr_usd >= 0 else "#dc2626"
    alfa_usd = cagr_usd - m['USD']['bench']['CAGR']
    color_alfa = "#16a34a" if alfa_usd >= 0 else "#dc2626"
    signo_alfa = "+" if alfa_usd > 0 else ""


    diff_kpis = {}
    for divisa in ['USD', 'CLP', 'UF']:

        yo_sharpe = m[divisa]['yo']['Sharpe']
        be_sharpe = m[divisa]['bench']['Sharpe']
        sharpe_pct = ((yo_sharpe / be_sharpe) - 1) * 100 if be_sharpe != 0 else 0.0
        color_sharpe = "#16a34a" if sharpe_pct >= 0 else "#dc2626"
        signo_sharpe = "+" if sharpe_pct > 0 else ""
        

        yo_dd = m[divisa]['yo']['MaxDD']
        be_dd = m[divisa]['bench']['MaxDD']
        maxdd_pct = ((yo_dd / be_dd) - 1) * 100 if be_dd != 0 else 0.0

        color_maxdd = "#16a34a" if abs(yo_dd) <= abs(be_dd) else "#dc2626"
        signo_maxdd = "+" if maxdd_pct > 0 else ""
        
        diff_kpis[divisa] = {
            'sharpe_val': f"{signo_sharpe}{sharpe_pct:.1f}%", 'sharpe_color': color_sharpe,
            'maxdd_val': f"{signo_maxdd}{maxdd_pct:.1f}%", 'maxdd_color': color_maxdd
        }


    html_dashboard_completo = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Fintech Executive Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 24px;
            background-color: #f8fafc;
            color: #0f172a;
        }}
        .dashboard-wrapper {{
            max-width: 1280px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }}
        .grid-multipliers {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }}
        .multiplier-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
        }}
        .multiplier-header {{
            display: flex;
            justify-open: space-between;
            justify-content: space-between;
            align-items: center;
            font-size: 18px;
            font-weight: 600;
            color: #64748b;
        }}
        .multiplier-badge {{
            background: #f1f5f9;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
        }}
        .multiplier-value {{
            font-size: 38px;
            font-weight: 800;
            color: #1e293b;
            margin: 12px 0 0 0;
            letter-spacing: -0.03em;
        }}
        .multiplier-pct {{
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 12px;
            margin-top: -2px;
        }}
        .multiplier-footer {{
            font-size: 12px;
            color: #94a3b8;
            border-top: 1px dashed #e2e8f0;
            padding-top: 8px;
            margin-top: 4px;
        }}
        .chart-container {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        }}
        .grid-kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
        }}
        .kpi-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .kpi-big-value {{ font-size: 26px; font-weight: 800; margin-top: 6px; }}
        .kpi-subtitle {{ font-size: 11px; color: #64748b; margin-top: 2px; }}
        .kpi-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }}
        .kpi-table th, .kpi-table td {{ padding: 5px 0; text-align: right; }}
        .kpi-table th {{ font-size: 9px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }}
        .kpi-table td:first-child, .kpi-table th:first-child {{ text-align: left; font-weight: 600; color: #475569; }}
        .val-yo {{ font-weight: 700; color: #0f172a; }}
        .val-bench {{ color: #94a3b8; font-weight: 500; }}
        .card-highlight {{ background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-color: #cbd5e1; }}
    </style>
</head>
<body>

    <div class="dashboard-wrapper">
        
        <div>
            <div class="section-title">Rentabilidad Absoluta y Multiplicadores de Capital</div>
            <div class="grid-multipliers">
                <div class="multiplier-card">
                    <div class="multiplier-header"><span>🇺🇸 Dólares Estadounidenses</span><span class="multiplier-badge">USD</span></div>
                    <div class="multiplier-value">{mult_yo_usd:.2f}x</div>
                    <div class="multiplier-pct" style="color: {color_pct_usd};">{sign_usd}{pct_yo_usd:.2f}%</div>
                    <div class="multiplier-footer">Cada $1 es hoy <strong>${mult_yo_usd:.2f}</strong> (FTAW {mult_be_usd:.2f}x)</div>
                </div>
                <div class="multiplier-card">
                    <div class="multiplier-header"><span>🇨🇱 Pesos Chilenos</span><span class="multiplier-badge">CLP</span></div>
                    <div class="multiplier-value">{mult_yo_clp:.2f}x</div>
                    <div class="multiplier-pct" style="color: {color_pct_clp};">{sign_clp}{pct_yo_clp:.2f}%</div>
                    <div class="multiplier-footer">Cada $1 es hoy <strong>${mult_yo_clp:.2f}</strong> (FTAW {mult_be_clp:.2f}x)</div>
                </div>
                <div class="multiplier-card">
                    <div class="multiplier-header"><span>🇨🇱 Unidad de Fomento</span><span class="multiplier-badge">UF</span></div>
                    <div class="multiplier-value">{mult_yo_uf:.2f}x</div>
                    <div class="multiplier-pct" style="color: {color_pct_uf};">{sign_uf}{pct_yo_uf:.2f}%</div>
                    <div class="multiplier-footer">Poder de compra real: <strong>{mult_yo_uf:.2f}x</strong> (FTAW {mult_be_uf:.2f}x)</div>
                </div>
            </div>
        </div>

        <div>
            <div class="section-title">Curva de Rentabilidad Acumulada</div>
            <div class="chart-container">
                {graph_div_html}
            </div>
        </div>

        <div>
            <div class="section-title">Métricas de crecimiento y riesgo</div>
            <div class="grid-kpis">
                
                <div class="kpi-card card">
                    <div>
                        <div class="section-title" style="color: #0f172a; font-size:11px;">📈 CAGR Anualizado</div>
                        <div class="kpi-big-value" style="color: {color_cagr};">{cagr_usd:.2f}%</div>
                        <div class="kpi-subtitle">Retorno compuesto anual en USD</div>
                    </div>
                    <div style="margin-top: 14px; border-top: 1px dashed #cbd5e1; padding-top: 8px; display: flex; justify-content: space-between; font-size: 13px;">
                        <span style="color: {color_alfa}; font-weight: 700;">🚀 Alfa: {signo_alfa}{alfa_usd:.2f}%</span>
                        <span style="color: #94a3b8;">FTAW: {m['USD']['bench']['CAGR']:.2f}%</span>
                    </div>
                </div>

            

                <div class="kpi-card">
                    <div class="section-title" style="font-size:11px;">📊 Ratio Sharpe</div>
                    <table class="kpi-table">
                        <thead><tr><th>Divisa</th><th>Neko Money</th><th>FTAW</th><th>Diff</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>USD</td>
                                <td class="val-yo">{m['USD']['yo']['Sharpe']:.2f}</td>
                                <td class="val-bench">{m['USD']['bench']['Sharpe']:.2f}</td>
                                <td style="font-weight: 700; color: {diff_kpis['USD']['sharpe_color']};">{diff_kpis['USD']['sharpe_val']}</td>
                            </tr>
                            <tr>
                                <td>CLP</td>
                                <td class="val-yo">{m['CLP']['yo']['Sharpe']:.2f}</td>
                                <td class="val-bench">{m['CLP']['bench']['Sharpe']:.2f}</td>
                                <td style="font-weight: 700; color: {diff_kpis['CLP']['sharpe_color']};">{diff_kpis['CLP']['sharpe_val']}</td>
                            </tr>
                            <tr>
                                <td>UF</td>
                                <td class="val-yo">{m['UF']['yo']['Sharpe']:.2f}</td>
                                <td class="val-bench">{m['UF']['bench']['Sharpe']:.2f}</td>
                                <td style="font-weight: 700; color: {diff_kpis['UF']['sharpe_color']};">{diff_kpis['UF']['sharpe_val']}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="kpi-card">
                    <div class="section-title" style="font-size:11px;">📉 Max Drawdown</div>
                    <table class="kpi-table">
                        <thead><tr><th>Divisa</th><th>Neko Money</th><th>FTAW</th><th>Diff</th></tr></thead>
                        <tbody>
                            <tr>
                                <td>USD</td>
                                <td class="val-yo" style="color:#ef4444;">{m['USD']['yo']['MaxDD']:.1f}%</td>
                                <td class="val-bench">{m['USD']['bench']['MaxDD']:.1f}%</td>
                                <td style="font-weight: 700; color: {diff_kpis['USD']['maxdd_color']};">{diff_kpis['USD']['maxdd_val']}</td>
                            </tr>
                            <tr>
                                <td>CLP</td>
                                <td class="val-yo" style="color:#ef4444;">{m['CLP']['yo']['MaxDD']:.1f}%</td>
                                <td class="val-bench">{m['CLP']['bench']['MaxDD']:.1f}%</td>
                                <td style="font-weight: 700; color: {diff_kpis['CLP']['maxdd_color']};">{diff_kpis['CLP']['maxdd_val']}</td>
                            </tr>
                            <tr>
                                <td>UF</td>
                                <td class="val-yo" style="color:#ef4444;">{m['UF']['yo']['MaxDD']:.1f}%</td>
                                <td class="val-bench">{m['UF']['bench']['MaxDD']:.1f}%</td>
                                <td style="font-weight: 700; color: {diff_kpis['UF']['maxdd_color']};">{diff_kpis['UF']['maxdd_val']}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="kpi-card">
                    <div>
                        <div class="section-title" style="font-size:11px;">⏳ Tiempo invertido</div>
                        <div class="kpi-big-value" style="font-size: 18px; color:#1e293b; font-weight:700;">{texto_final}</div>
                        <div class="kpi-subtitle" style="font-size: 11px; color: #64748b; margin-top: 2px;">{frase_del_dia}</div>
                    </div>
                    <div style="margin-top: 14px; border-top: 1px dashed #e2e8f0; padding-top: 8px; display: flex; justify-content: space-between; font-size: 11px; color: #64748b;">
                        <span>Desde: {fecha_inicio.strftime('%Y-%m-%d')}</span>
                        <span style="color: #dc2626; font-weight: 600;">Inflación Total: {inflacion_periodo:.1f}%</span>
                    </div>
                </div>

            </div>
        </div>

    </div>

</body>
</html>
"""
    
    ruta_salida = "dashboard_premium.html"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html_dashboard_completo)
    print(f"✅ Generadas tarjetas KPI de ganancias, gráfico histórico de rentabilidad, y métricas de crecimiento y riesgo en: {ruta_salida}")



if __name__ == "__main__":
    inicializar_db_long()
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df_tx_inicial = pd.read_sql_query("SELECT * FROM transacciones", conn)
    except Exception as e:
        print(f"Error: {e}")
        df_tx_inicial = pd.DataFrame()
    finally:
        conn.close()

    if not df_tx_inicial.empty:
        df_tx_inicial['fecha'] = pd.to_datetime(df_tx_inicial['fecha'])
        fecha_desde_donde_actualizar = df_tx_inicial['fecha'].min()
        
        tickers_usuario = [t + ".L" if not t.endswith(".L") else t for t in df_tx_inicial['ticker'].unique()]
        lista_descarga_completa = list(set(tickers_usuario + ['FTAW.AS']))
        
        print("\nSincronizando precios de mercado...")
        actualizar_cache_long(variables_tickers=lista_descarga_completa, fecha_inicio=fecha_desde_donde_actualizar)
        
        print("\nCompilando y renderizando UI Financiera...")
        generar_dashboard_premium()
    else:
        print("Operación abortada: La tabla de transacciones está vacía.")
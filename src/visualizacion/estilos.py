import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


MATRICES_ORIGINALES = {
    "BENCHMARK": np.array([[0, 0, 0], [5, 7, 4], [22, 36, 25]]),
    "AVEM":      np.array([[3, 3, 2], [8, 4, 5], [20, 21, 30]]),
    "AVGS":      np.array([[45, 28, 10], [7, 7, 3], [0, 0, 0]]),
    "AVGC":      np.array([[5, 6, 2], [9, 11, 6], [17, 26, 16]])
}

MAPEO_ETFS = {
    "AVGS": MATRICES_ORIGINALES["AVGS"],
    "AVGC": MATRICES_ORIGINALES["AVGC"],
    "AVEM": MATRICES_ORIGINALES["AVEM"],
    #"AVUS": MATRICES_ORIGINALES["AVWC"], 
    #"AVEU": MATRICES_ORIGINALES["AVWC"], 
    #"AVPE": MATRICES_ORIGINALES["AVWC"]  
}

def exportar_bloque_style_box_html(ruta_csv, ruta_salida_html="bloque_2b_style_box.html") -> str:
    """
    Función todo-en-uno: Lee el CSV, calcula la matriz compuesta horizontal,
    normaliza la escala de color al valor máximo absoluto global, genera las 
    tarjetas KPI verticales lado a lado y exporta el HTML unificado.
    """

    df = pd.read_csv(ruta_csv)
    

    df['ticker_clean'] = df['ticker'].str.replace(r'\.L$', '', regex=True).str.strip().str.upper()

    df_filtrado = df[df['ticker_clean'].isin(MAPEO_ETFS)].copy()
    if df_filtrado.empty:
        raise ValueError("Error: No se encontraron tickers válidos de Avantis en el CSV.")
        
    total_proporcion = df_filtrado['proporcionActual'].sum()
    df_filtrado['peso_relativo'] = df_filtrado['proporcionActual'] / total_proporcion


    matriz_portafolio = np.zeros((3, 3))
    for _, row in df_filtrado.iterrows():
        ticker = row['ticker_clean']
        peso = row['peso_relativo']
        matriz_portafolio += MAPEO_ETFS[ticker] * peso


    matriz_bench = MATRICES_ORIGINALES["BENCHMARK"] * (100.0 / MATRICES_ORIGINALES["BENCHMARK"].sum())


    global_max = float(max(matriz_portafolio.max(), matriz_bench.max()))

 
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Neko Money</b>", "<b>FTAW</b>"),
        horizontal_spacing=0.01,  
        shared_yaxes=True
    )

    estilos = ["Value", "Blend", "Growth"]
    tamanos = ["Small", "Mid", "Large"]
    

    text_port = [[f"<b>{val:.1f}%</b>" if val > 0.1 else "<b>0.0%</b>" for val in row] for row in matriz_portafolio]
    text_bench = [[f"<b>{val:.1f}%</b>" if val > 0.1 else "<b>0.0%</b>" for val in row] for row in matriz_bench]


    fig.add_trace(
        go.Heatmap(
            z=matriz_portafolio, x=estilos, y=tamanos,
            text=text_port, texttemplate="%{text}",
            textfont=dict(size=14, family="Arial"),
            colorscale="reds", 
            showscale=False,
            zmin=0, zmax=global_max, 
            xgap=4, ygap=4, 
            hovertemplate="Neko Money - %{y} %{x}: <b>%{z:.2f}%</b><extra></extra>"
        ),
        row=1, col=1
    )


    fig.add_trace(
        go.Heatmap(
            z=matriz_bench, x=estilos, y=tamanos,
            text=text_bench, texttemplate="%{text}",
            textfont=dict(size=14, family="Arial"),
            colorscale="greys", 
            showscale=False,
            zmin=0, zmax=global_max,  
            xgap=4, ygap=4,
            hovertemplate="Benchmark - %{y} %{x}: <b>%{z:.2f}%</b><extra></extra>"
        ),
        row=1, col=2
    )


    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#cbd5e1", 
        height=360,         
        width=580,              
        margin=dict(l=0, r=0, t=80, b=0), 
        hovermode="closest"
    )

    fig.update_xaxes(
        side="top",
        tickfont=dict(size=14, color="#64748b", weight="bold"),
        fixedrange=True, showgrid=False, zeroline=False
    )

    fig.update_yaxes(
        tickfont=dict(size=14, color="#64748b", weight="bold"),
        fixedrange=True, showgrid=False, zeroline=False
    )


    fig['layout']['annotations'][0].update(font=dict(size=16, color="#334155", family="Arial", weight="bold"), y=1.1)
    fig['layout']['annotations'][1].update(font=dict(size=16, color="#334155", family="Arial", weight="bold"), y=1.1)

    plot_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

    port_small, port_mid, port_large = matriz_portafolio[0].sum(), matriz_portafolio[1].sum(), matriz_portafolio[2].sum()
    bench_small, bench_mid, bench_large = matriz_bench[0].sum(), matriz_bench[1].sum(), matriz_bench[2].sum()
    
    port_value, port_blend, port_growth = matriz_portafolio[:, 0].sum(), matriz_portafolio[:, 1].sum(), matriz_portafolio[:, 2].sum()
    bench_value, bench_blend, bench_growth = matriz_bench[:, 0].sum(), matriz_bench[:, 1].sum(), matriz_bench[:, 2].sum()

    html_final = f"""
    <div class="bloque-2b-stylebox" style="background: white; padding: 0px; font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto;">
        
        <div style="display: flex; justify-content: center; width: 100%; margin-bottom: 30px;">
            {plot_html}
        </div>

        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;">
            
            <div style="background: #f8fafc; padding: 12px 14px; border-radius: 10px; border-left: 4px solid #047857; display: flex; flex-direction: column; justify-content: space-between; gap: 12px;">
                <div style="font-size: 14px; color: #475569; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">Sesgo por Estilo</div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="font-weight: bold; color: #047857;">Value ★</span>
                    <span style="font-weight: bold; color: #047857;">{port_value:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_value:.1f}%</span></span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="color: #64748b;">Blend</span>
                    <span style="font-weight: bold; color: #1e293b;">{port_blend:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_blend:.1f}%</span></span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="color: #64748b;">Growth</span>
                    <span style="font-weight: bold; color: #1e293b;">{port_growth:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_growth:.1f}%</span></span>
                </div>
            </div>
            
            <div style="background: #f8fafc; padding: 12px 14px; border-radius: 10px; border-left: 4px solid #047857; display: flex; flex-direction: column; justify-content: space-between; gap: 8px;">
                <div style="font-size: 14px; color: #475569; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">Sesgo por Tamaño</div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="color: #64748b;">Large</span>
                    <span style="font-weight: bold; color: #1e293b;">{port_large:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_large:.1f}%</span></span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="color: #64748b;">Mid</span>
                    <span style="font-weight: bold; color: #1e293b;">{port_mid:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_mid:.1f}%</span></span>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 14px;">
                    <span style="font-weight: bold; color: #047857;">Small ★</span>
                    <span style="font-weight: bold; color: #047857;">{port_small:.1f}% <span style="font-weight: normal; color: #94a3b8; font-size: 12px;">vs {bench_small:.1f}%</span></span>
                </div>
            </div>

        </div>
    </div>
    """

    if ruta_salida_html:
        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Generado Style Box y tarjetas KPIs de factores en: {ruta_salida_html}")

    return html_final
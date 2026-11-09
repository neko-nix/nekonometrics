import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


FONDO   = "#0f0d0a"
SUP     = "#17140f"
SUP2    = "#1f1b14"
BORDE   = "#2b2519"
TEXTO   = "#e8e2d4"
FUERTE  = "#f7f2e4"
MUTED   = "#a89c85"
FAINT   = "#7a705e"
ORO     = "#f0b64b"
ORO_DIM = "#b8862f"

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

 
    # ── Escalas: dorado = vos · gris = referencia ──
    COLORSCALE_ORO = [
        [0.00, "#14110d"],
        [0.22, "#2b2114"],
        [0.48, "#5c4112"],
        [0.72, "#9a6a1c"],
        [0.90, "#c8973a"],
        [1.00, "#f5c862"],
    ]
    COLORSCALE_GRIS = [
        [0.00, "#14110d"],
        [0.30, "#282420"],
        [0.60, "#4a443a"],
        [0.85, "#7d7568"],
        [1.00, "#b8ae9c"],
    ]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("<b>Nekonometrics</b>", "<b>FTAW</b>"),
        horizontal_spacing=0.05,
        shared_yaxes=True,
    )

    # ── 1. Títulos (SOLO los dos subtítulos) ──
    for ann in fig.layout.annotations[:2]:
        ann.update(
            font=dict(size=15, color=FUERTE, family="'Segoe UI',Arial,sans-serif", weight=700),
            y=1.08,
        )

    estilos = ["Value", "Blend", "Growth"]
    tamanos = ["Small", "Mid", "Large"]

    # ── 2. PANEL 1: Nekonometrics (oro) — SIN text ──
    fig.add_trace(
        go.Heatmap(
            z=matriz_portafolio, x=estilos, y=tamanos,
            colorscale=COLORSCALE_ORO,
            showscale=False,
            zmin=0, zmax=global_max,
            xgap=3, ygap=3,
            hovertemplate="Nekonometrics · %{y} %{x}: <b>%{z:.1f}%</b><extra></extra>"
        ),
        row=1, col=1
    )

    # ── 3. PANEL 2: FTAW (gris) — SIN text ──
    fig.add_trace(
        go.Heatmap(
            z=matriz_bench, x=estilos, y=tamanos,
            colorscale=COLORSCALE_GRIS,
            showscale=False,
            zmin=0, zmax=global_max,
            xgap=3, ygap=3,
            hovertemplate="FTAW · %{y} %{x}: <b>%{z:.1f}%</b><extra></extra>"
        ),
        row=1, col=2
    )

    # ── 4. Números: una annotation por celda, con su propio color ──
    def agregar_etiquetas(matriz, fila, col, umbral):
        piso = global_max if global_max else 1.0
        for i, tam in enumerate(tamanos):
            for j, est in enumerate(estilos):
                v = matriz[i][j]
                fig.add_annotation(
                    x=est, y=tam, row=fila, col=col,
                    text=(f"<b>{v:.1f}%</b>" if v > 0.1 else "<b>0.0%</b>"),
                    showarrow=False,
                    font=dict(
                        size=14,
                        family="'Segoe UI',Arial,sans-serif",
                        color=("#1a1408" if (v / piso) > umbral else "#f7f2e4"),
                    ),
                )

    agregar_etiquetas(matriz_portafolio, 1, 1, 0.80)
    agregar_etiquetas(matriz_bench,     1, 2, 0.88)

    # ── 5. Layout ──
    fig.update_layout(
        paper_bgcolor=FONDO,
        plot_bgcolor=FONDO,
        height=360,
        margin=dict(l=58, r=10, t=78, b=10),
        hovermode="closest",
        font=dict(family="'Segoe UI',Arial,sans-serif", color=TEXTO),
        hoverlabel=dict(
            bgcolor=SUP2, bordercolor=ORO,
            font=dict(color="#f5e6c8", size=12),
        ),
    )

    # ── 6. Ejes ──
    fig.update_xaxes(
        side="top",
        tickfont=dict(size=12, color=ORO_DIM, weight=700),
        fixedrange=True, showgrid=False, zeroline=False,
        linecolor=BORDE,
    )

    fig.update_yaxes(
        tickfont=dict(size=12, color=MUTED, weight=700),
        fixedrange=True, showgrid=False, zeroline=False,
    )

    plot_html = fig.to_html(include_plotlyjs="cdn", full_html=False)



    port_small, port_mid, port_large = matriz_portafolio[0].sum(), matriz_portafolio[1].sum(), matriz_portafolio[2].sum()
    bench_small, bench_mid, bench_large = matriz_bench[0].sum(), matriz_bench[1].sum(), matriz_bench[2].sum()
    
    port_value, port_blend, port_growth = matriz_portafolio[:, 0].sum(), matriz_portafolio[:, 1].sum(), matriz_portafolio[:, 2].sum()
    bench_value, bench_blend, bench_growth = matriz_bench[:, 0].sum(), matriz_bench[:, 1].sum(), matriz_bench[:, 2].sum()

    html_final = f"""
    <div class="bloque-2b-stylebox"
         style="background:{FONDO}; padding:0; font-family:'Segoe UI',Arial,sans-serif;
                max-width:560px; margin:0 auto;">

        <div style="display:flex; justify-content:center; width:100%; margin-bottom:14px;">
            {plot_html}
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px;">

            <div style="background:{SUP2}; border:1px solid {BORDE}; border-left:3px solid {ORO};
                        border-radius:10px; padding:13px 15px; display:flex; flex-direction:column;
                        justify-content:space-between; gap:10px;">
                <div style="font-size:11px; font-weight:700; letter-spacing:1.4px;
                            text-transform:uppercase; color:{ORO_DIM};
                            border-bottom:1px solid {BORDE}; padding-bottom:6px;">
                    Sesgo por Estilo</div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="font-weight:700; color:{ORO};">Value ★</span>
                    <span style="font-weight:700; color:#ffffff;">{port_value:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_value:.1f}%</span></span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="color:{MUTED};">Blend</span>
                    <span style="font-weight:700; color:{FUERTE};">{port_blend:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_blend:.1f}%</span></span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="color:{MUTED};">Growth</span>
                    <span style="font-weight:700; color:{FUERTE};">{port_growth:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_growth:.1f}%</span></span>
                </div>
            </div>

            <div style="background:{SUP2}; border:1px solid {BORDE}; border-left:3px solid {ORO};
                        border-radius:10px; padding:13px 15px; display:flex; flex-direction:column;
                        justify-content:space-between; gap:10px;">
                <div style="font-size:11px; font-weight:700; letter-spacing:1.4px;
                            text-transform:uppercase; color:{ORO_DIM};
                            border-bottom:1px solid {BORDE}; padding-bottom:6px;">
                    Sesgo por Tamaño</div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="color:{MUTED};">Large</span>
                    <span style="font-weight:700; color:{FUERTE};">{port_large:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_large:.1f}%</span></span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="color:{MUTED};">Mid</span>
                    <span style="font-weight:700; color:{FUERTE};">{port_mid:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_mid:.1f}%</span></span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; font-size:13px;">
                    <span style="font-weight:700; color:{ORO};">Small ★</span>
                    <span style="font-weight:700; color:#ffffff;">{port_small:.1f}%
                        <span style="font-weight:400; color:{FAINT}; font-size:11px;">vs {bench_small:.1f}%</span></span>
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
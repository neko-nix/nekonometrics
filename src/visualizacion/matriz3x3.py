import os
import re
from pathlib import Path
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import sqlite3


# ── TEMA OSCURO DORADO ──
FONDO   = "#0f0d0a"
SUP     = "#17140f"
BORDE   = "#2b2519"
BORDE_2 = "#221d15"
TEXTO   = "#e8e2d4"
FUERTE  = "#f7f2e4"
MUTED   = "#a89c85"
FAINT   = "#7a705e"
ORO      = "#f0b64b"   # el dorado validado
ORO_DIM  = "#b8862f"   # dorado oscuro: se lee en textos chicos (6.4:1)
ORO_BRIGHT = "#ffd280" # para hovers
VERDE   = "#4ade80"
ROJO    = "#f87171"
SUP2    = "#1f1b14"   # superficie de los mini-tiles



DATA_DIR = "data"
COSTO_BENCH_DEFAULT = 0.07 

# MAPEO_ACTIVOS = {
#     "AVUS.DE": ("Norteamérica", "Core / Blend"),
#     "AVEU.DE": ("Europa", "Core / Blend"),
#     "AVEM.DE": ("Emergentes", "Core / Blend"),
#     "AVWC.DE": ("Desarrollados", "Core / Blend"),
#     "AVWS.DE": ("Desarrollados", "Small Cap Value"),
#     "AVPE.DE": ("Pacífico", "Core / Blend"),
# }

MAPEO_ACTIVOS = {
    "AVGC.L": ("Desarrollados", "Core / Blend"),
    "AVGS.L": ("Desarrollados", "Small Cap Value"),
    "AVEM.L": ("Emergentes", "Core / Blend")
}



# DICCIONARIO_COSTOS = {
#     "AVUS.DE": 0.20,
#     "AVEU.DE": 0.25,
#     "AVEM.DE": 0.35,
#     "AVWC.DE": 0.22,
#     "AVWS.DE": 0.39,
#     "AVPE.DE": 0.25,
# }

DICCIONARIO_COSTOS = {
    "AVGC.L": 0.22,
    "AVGS.L": 0.39,
    "AVEM.L": 0.35,
}



def generar_bloque_treemap_y_factores_html(
    csv_path, costo_bench=COSTO_BENCH_DEFAULT
):
    if not Path(csv_path).exists():
        print(f"Error Crítico: No se encontró el archivo {csv_path}")
        return
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.upper()
    col_ticker = [c for c in df.columns if "TICKER" in c][0]
    col_prop = [c for c in df.columns if "PROPORCIONACTUAL" in c or "PESO" in c][0]

    df["PROP_NUM"] = (
        df[col_prop].astype(str).str.replace("%", "", regex=False).str.strip()
    )
    df["PROP_NUM"] = pd.to_numeric(df["PROP_NUM"], errors="coerce").fillna(0)
    if df["PROP_NUM"].max() <= 1.0:
        df["PROP_NUM"] = df["PROP_NUM"] * 100


    df["TICKER_ORIGINAL"] = df[col_ticker].astype(str).str.strip().str.upper()
    df["TICKER_BASE"] = df["TICKER_ORIGINAL"].str.split(".").str[0]



    df["Region"] = df["TICKER_ORIGINAL"].map(
        lambda x: MAPEO_ACTIVOS.get(x, ("Otros", "Otros"))[0]
    )
    df["Factor"] = df["TICKER_ORIGINAL"].map(
        lambda x: MAPEO_ACTIVOS.get(x, ("Otros", "Otros"))[1]
    )
    df["TER"] = df["TICKER_ORIGINAL"].map(DICCIONARIO_COSTOS).fillna(0.0)







    
    html_tarjeta2 = ""
    col_ideal = [c for c in df.columns if "IDEAL" in c]

    if col_ideal:
        col_id = col_ideal[0]

        df["IDEAL_NUM"] = df[col_id].astype(str).str.replace("%", "", regex=False).str.strip()
        df["IDEAL_NUM"] = pd.to_numeric(df["IDEAL_NUM"], errors="coerce").fillna(0)
        if df["IDEAL_NUM"].max() <= 1.0:
            df["IDEAL_NUM"] = df["IDEAL_NUM"] * 100

        df["DIF_REBALANCEO"] = df["PROP_NUM"] - df["IDEAL_NUM"]
        max_abs = df["DIF_REBALANCEO"].abs().max() or 1.0

        tiles = ""
        for _, row in df.sort_values("DIF_REBALANCEO", ascending=True).iterrows():
            ticker = row["TICKER_ORIGINAL"]
            ideal  = row["IDEAL_NUM"]
            actual = row["PROP_NUM"]
            dif    = row["DIF_REBALANCEO"]
            ancho  = abs(dif) / max_abs * 100

            if dif < -0.2:
                color_dif, badge = ORO, "▼"
            elif dif > 0.2:
                color_dif, badge = ROJO, "▲"
            else:
                color_dif, badge = VERDE, "✓"

            tiles += f"""
            <div style="background:{SUP2}; border:1px solid {BORDE}; border-radius:9px;
                        padding:13px 15px; display:flex; flex-direction:column; gap:9px;">
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span style="font-family:ui-monospace,SFMono-Regular,monospace; font-size:14px;
                                 font-weight:700; color:{FUERTE}; letter-spacing:0.3px;">{ticker}</span>
                    <span style="font-size:13px; font-weight:700; color:{color_dif};">
                        {badge} {dif:+.1f}%</span>
                </div>
                <div style="font-size:11px; color:{MUTED};">
                    Actual <b style="color:{TEXTO};">{actual:.1f}%</b>
                    &nbsp;·&nbsp;
                    Objetivo <b style="color:{TEXTO};">{ideal:.1f}%</b>
                </div>
                <div style="height:6px; background:{BORDE}; border-radius:3px; overflow:hidden;">
                    <div style="height:100%; width:{ancho:.0f}%; background:{color_dif};
                                border-radius:3px;"></div>
                </div>
            </div>
            """

        html_tarjeta2 = f"""
        <div style="background:{SUP}; border:1px solid {BORDE}; border-radius:10px; padding:16px 18px;">
            <div style="display:flex; justify-content:space-between; align-items:baseline;
                        flex-wrap:wrap; gap:8px; margin-bottom:14px;">
                <div>
                    <div style="font-size:11px; font-weight:700; letter-spacing:1.4px;
                                text-transform:uppercase; color:{ORO_DIM};">
                        Desviaciones del objetivo</div>
                    <div style="font-size:12px; color:{MUTED}; margin-top:2px;">
                        Peso actual vs. peso ideal</div>
                </div>
                <div style="font-size:11px; color:{FAINT};">
                    <span style="color:{ORO};">▼</span> falta &nbsp;·&nbsp;
                    <span style="color:{ROJO};">▲</span> exceso &nbsp;·&nbsp;
                    <span style="color:{VERDE};">✓</span> ±0.2 pp
                </div>
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
                        gap:10px;">
                {tiles}
            </div>
        </div>
        """



        # ── Grupo de color (LO QUE FALTABA) ──
    df["Grupo_Color"] = df.apply(
        lambda r: (
            "Desarrollados SCV" if r["Region"] == "Desarrollados" and r["Factor"] == "Small Cap Value"
            else ("Desarrollados Core" if r["Region"] == "Desarrollados" else r["Region"])
        ), axis=1
    )





    # ── Charcoal profundo + filete dorado ──
    paleta_colores = {
        "Desarrollados Core": "#14110d",   # casi el fondo: lo define el marco
        "Desarrollados SCV":  "#201b14",   # el más claro = protagonista
        "Emergentes":         "#1a1611",   # intermedio
        "Otros":              "#12100c",
    }
    fig = px.treemap(
        df, path=["TICKER_ORIGINAL"], values="PROP_NUM",
        color="Grupo_Color",
        color_discrete_map=paleta_colores, 
        
        custom_data=["Region", "Factor", "TER"],
    )
    fig.update_traces(
        texttemplate=(
            "<b>%{label}</b><br>"
            "<span style='font-size:12px; color:#d6d0c2;'>"
            "%{customdata[0]} · %{customdata[1]}<br>TER %{customdata[2]:.2f}%</span><br>"
            "<span style='font-size:18px; color:#ffffff;'><b>%{value:.1f}%</b></span>"
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Peso: <b>%{value:.2f}%</b><br>"
            "Región: %{customdata[0]}<br>"
            "Factor: %{customdata[1]}<br>"
            "TER: %{customdata[2]:.2f}%"
            "<extra></extra>"
        ),
        textfont=dict(size=15, color="#f7f2e4"),
        textposition="middle center",
        marker=dict(
            line=dict(color="#b8862f", width=2),
            cornerradius=4,
        ),
        hoverlabel=dict(
            bgcolor="#1f1b14",
            bordercolor=ORO,
            font=dict(color="#f5e6c8", size=12),
        ),
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        height=420,
        plot_bgcolor=FONDO,
        paper_bgcolor=FONDO,
        font=dict(color=TEXTO, size=12),
        hovermode="closest",
    )
    plot_html_div = fig.to_html(include_plotlyjs="cdn", full_html=False)



  
    bloque_kpi = f"""
        <div style="margin-top:14px; padding:0 4px 4px 4px;">{html_tarjeta2}</div>
    """ if html_tarjeta2 else ""

    html_completo = f"""
    <div class="bloque-1b-container"
         style="font-family:'Segoe UI',Tahoma,sans-serif; background:{FONDO};
                padding:0; border-radius:12px;">
        <div style="width:100%;">
            {plot_html_div}
        </div>
        {bloque_kpi}
    </div>
    """

    output_file = "bloque1b_treemap_y_factores.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_completo)
    print(f"✅ Generado Treemap de composición y desviaciones del objetivo en: {output_file}")
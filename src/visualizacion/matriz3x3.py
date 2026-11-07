import os
import re
from pathlib import Path
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import sqlite3


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


    suma_proporciones = df["PROP_NUM"].sum()
    tu_costo_ponderado = (
        (df["TER"] * df["PROP_NUM"]).sum() / suma_proporciones
        if suma_proporciones > 0
        else 0
    )
    dif_costo = tu_costo_ponderado - costo_bench
    text_costo = f"▲ +{dif_costo:.3f}% extra anual por captura de factores"


    col_ideal = [c for c in df.columns if "IDEAL" in c]
    
    if col_ideal:
        col_id = col_ideal[0]
  
        df["IDEAL_NUM"] = df[col_id].astype(str).str.replace("%", "", regex=False).str.strip()
        df["IDEAL_NUM"] = pd.to_numeric(df["IDEAL_NUM"], errors="coerce").fillna(0)
        if df["IDEAL_NUM"].max() <= 1.0:
            df["IDEAL_NUM"] = df["IDEAL_NUM"] * 100

        df["DIF_REBALANCEO"] = df["PROP_NUM"] - df["IDEAL_NUM"]
        
        titulo_kpi2 = "Desviaciones del Objetivo"
        subtitulo_kpi2 = "Peso Ideal vs. Brecha Actual"
        

        df_ordenado = df.sort_values(by="DIF_REBALANCEO", ascending=True)
        filas_tickers_html = ""
        
        for idx, row in df_ordenado.iterrows():
            ticker = row["TICKER_ORIGINAL"]
            ideal = row["IDEAL_NUM"]
            dif = row["DIF_REBALANCEO"]
            

            if dif < -0.2:  
                color_dif = "#b91c1c" 
                signo_dif = ""
                badge = "▼"
            elif dif > 0.2:
                color_dif = "#475569"  
                signo_dif = "+"
                badge = "▲"
            else:
                color_dif = "#10b981"  
                signo_dif = "±"
                badge = "✓"
                
          
            border_style = "" if idx == df_ordenado.index[-1] else "border-bottom: 1px dashed #e2e8f0;"
            
            filas_tickers_html += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0px 0; {border_style} font-size: 12px;">
                <span style="font-weight: bold; color: #1e293b; min-width: 5px;">{ticker}</span>
                <span style="color: #64748b;">Objetivo: <b>{ideal:.1f}%</b></span>
                <span style="color: {color_dif}; font-weight: bold; text-align: right; min-width: 5px;">
                    {badge} {signo_dif}{dif:.1f}%
                </span>
            </div>
            """
            
 
        html_tarjeta2 = f"""
        <div class="factor-card" style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="font-size: 10px; color: #475569; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">{titulo_kpi2}</div>
                <div style="font-size: 11px; color: #475569; margin-top: 2px; margin-bottom: 8px;">{subtitulo_kpi2}</div>
            </div>
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; gap: 2px;">
                {filas_tickers_html}
            </div>
        </div>
        """
    else:
      
        pesos_relativos = df["PROP_NUM"] / (suma_proporciones if suma_proporciones > 0 else 1) * 100
        hhi = (pesos_relativos ** 2).sum()
        text_kpi2 = "✓ Excelente diversificación" if hhi < 1500 else "⚠ Concentración moderada"
        
        html_tarjeta2 = f"""
        <div class="factor-card" style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
            <div style="font-size: 10px; color: #475569; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Concentración de Cartera (HHI)</div>
            <div style="font-size: 11px; color: #475569; margin-top: 2px;">Índice Herfindahl-Hirschman (Menor = Más Diversificado)</div>
            <div style="font-size: 15px; margin: 8px 0 4px 0; color: #1e293b;">HHI: <b>{hhi:.0f} pts</b></div>
            <div style="font-size: 11px; color: #475569; font-weight: bold;">{text_kpi2}</div>
        </div>
        """


    df["Grupo_Color"] = df.apply(
        lambda r: (
            "Desarrollados SCV" if r["Region"] == "Desarrollados" and r["Factor"] == "Small Cap Value"
            else ("Desarrollados Core" if r["Region"] == "Desarrollados" else r["Region"])
        ), axis=1
    )


    paleta_colores = {
        "Desarrollados Core": "#2a0808",  # Negro Rojizo (Mucha densidad)
        "Desarrollados SCV":  "#991b1b",  # Tu rojo Neko central actual
        "Emergentes":         "#cc1b3d",  # Rojo Coral / Rosa Neón (Mucha luz)
    }
    fig = px.treemap(
        df, path=["TICKER_ORIGINAL"], values="PROP_NUM",
        color="Grupo_Color",
        color_discrete_map=paleta_colores, 
        
        custom_data=["Region", "Factor", "TER"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br><span style='font-size:13px; font-weight: normal; opacity: 0.85;'>%{customdata[0]}<br>%{customdata[1]}<br>TER: <b>%{customdata[2]:.2f}%</b></span><br><span style='font-size:14px;'><b>%{value:.1f}%</b></span>",
        textfont=dict(size=14, color="white"), textposition="middle center",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), showlegend=False, height=400, plot_bgcolor="white", paper_bgcolor="white")

    plot_html_div = fig.to_html(include_plotlyjs="cdn", full_html=False)

  
    html_completo = f"""
    <div class="bloque-1b-container" style="font-family: Arial, sans-serif; background: white; padding: 5px; border-radius: 12px;">
        <div class="treemap-wrapper" style="width: 100%; height: auto;">
            {plot_html_div}
        </div>

        <div class="factor-cards-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 15px; padding: 0 10px;">
             
            <div class="factor-card" style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 10px; color: #475569; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">Eficiencia de Costos (TER)</div>
                    <div style="font-size: 11px; color: #475569; margin-top: 2px;">Costo Anual Ponderado (Mayor=Más Caro)</div>
                    <div style="font-size: 15px; margin: 8px 0 4px 0; color: #1e293b;">
                        <span style="color:#1e293b; font-weight:bold;">Neko Money:</span> {tu_costo_ponderado:.3f}% 
                        <span style="color:#cbd5e1; margin: 0 4px;"><br></span> 
                        <span style="color:#1e293b; font-weight:bold;">FTAW:</span> {costo_bench:.3f}%
                    </div>
                </div>
                <div style="font-size: 11px; color: #b91c1c; font-weight: bold; margin-top: auto;">
                    {text_costo}
                </div>
            </div>

            {html_tarjeta2}

        </div>
    </div>
    """

    output_file = "bloque1b_treemap_y_factores.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_completo)
    print(f"✅ Generado Treemap de composición del portafolio y KPIs de costos y proporción objetivo en: {output_file}")
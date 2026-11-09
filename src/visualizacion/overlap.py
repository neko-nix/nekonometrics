import pandas as pd
import plotly.graph_objects as go
import re

def generar_sankey_overlap_puro(df_tabla, csv_ftaw):

    def limpiar_pais(texto):
        if pd.isna(texto):
            return ""
        texto_limpio = re.sub(r'[^a-zA-Z ]', '', str(texto))
        return texto_limpio.strip().upper()

    df_yo = df_tabla.copy()
    df_yo.columns = [str(c).strip().upper() for c in df_yo.columns]
    
    col_ticker_yo = [c for c in df_yo.columns if 'TICKER' in c or 'ASSET_TICKER' in c][0]
    col_prop_yo = [c for c in df_yo.columns if 'PROPORCIONACTUAL' in c or 'PESO' in c][0]
    col_pais_yo = [c for c in df_yo.columns if 'PAIS' in c or 'COUNTRY' in c or 'REGION' in c][0]
    
    df_yo['PESO_YO'] = df_yo[col_prop_yo].astype(str).str.replace('%', '').str.strip()
    df_yo['PESO_YO'] = pd.to_numeric(df_yo['PESO_YO'], errors='coerce').fillna(0)
    
    df_yo = df_yo[df_yo[col_ticker_yo].notna() & (df_yo['PESO_YO'] > 0)]
    df_yo = df_yo[~df_yo[col_ticker_yo].astype(str).str.upper().str.contains('CASH|EFECTIVO|NAN|USD|CLP|TOTAL')]
    
    df_yo['LLAVE_UNICA'] = df_yo.apply(
        lambda r: f"{str(r[col_ticker_yo]).strip().upper()}_{limpiar_pais(r[col_pais_yo])}", axis=1
    )
    

    try:
        with open(csv_ftaw, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
        linea_header = 0
        for idx, linea in enumerate(lineas):
            if 'Ticker' in linea or 'Ticker' in linea.split(',')[0]:
                linea_header = idx
                break
        df_ftaw_raw = pd.read_csv(csv_ftaw, skiprows=linea_header, quotechar='"')
        df_ftaw_raw.columns = [str(c).strip().upper() for c in df_ftaw_raw.columns]
        
        col_ticker_ftaw = [c for c in df_ftaw_raw.columns if 'TICKER' in c][0]
        col_peso_ftaw = [c for c in df_ftaw_raw.columns if 'WEIGHT' in c or 'PESO' in c or 'POND' in c][0]
        col_pais_ftaw = [c for c in df_ftaw_raw.columns if c in ['LOCATION', 'MARKET', 'COUNTRY', 'PAIS']][0]
        
        df_ftaw = df_ftaw_raw[[col_ticker_ftaw, col_pais_ftaw, col_peso_ftaw]].copy()
        df_ftaw.columns = ['TICKER', 'PAIS', 'PESO_FTAW']
        
        df_ftaw['PESO_FTAW'] = df_ftaw['PESO_FTAW'].astype(str).str.replace('"', '').str.replace('%', '').str.strip()
        df_ftaw['PESO_FTAW'] = pd.to_numeric(df_ftaw['PESO_FTAW'], errors='coerce').fillna(0)
        
        df_ftaw = df_ftaw[df_ftaw['TICKER'].notna() & (df_ftaw['PESO_FTAW'] > 0)]
        df_ftaw = df_ftaw[~df_ftaw['TICKER'].astype(str).str.upper().str.contains('CASH|EFECTIVO|NAN|USD|CLP')]
        
        df_ftaw['LLAVE_UNICA'] = df_ftaw.apply(
            lambda r: f"{str(r['TICKER']).strip().upper()}_{limpiar_pais(r['PAIS'])}", axis=1
        )
        
    except Exception as e:
        print(f"Error al procesar CSV de BlackRock: {e}")
        return

    set_yo = set(df_yo['LLAVE_UNICA'])
    set_ftaw = set(df_ftaw['LLAVE_UNICA'])
    
    n_empresas_yo = len(set_yo)
    n_empresas_ftaw = len(set_ftaw)
    n_compartidas = len(set_yo.intersection(set_ftaw))
    

    df_yo_agrupado = df_yo.groupby('LLAVE_UNICA')['PESO_YO'].sum().reset_index()
    df_ftaw_agrupado = df_ftaw.groupby('LLAVE_UNICA')['PESO_FTAW'].sum().reset_index()
    
    df_yo_agrupado['PESO_YO'] = (df_yo_agrupado['PESO_YO'] / df_yo_agrupado['PESO_YO'].sum()) * 100
    df_ftaw_agrupado['PESO_FTAW'] = (df_ftaw_agrupado['PESO_FTAW'] / df_ftaw_agrupado['PESO_FTAW'].sum()) * 100
    
    df_overlap = pd.merge(df_yo_agrupado, df_ftaw_agrupado, on='LLAVE_UNICA', how='inner')
    portfolio_overlap = df_overlap[['PESO_YO', 'PESO_FTAW']].min(axis=1).sum()
    

    active_share = 100 - portfolio_overlap


    
    pct_nombre   = n_compartidas / n_empresas_ftaw * 100   # ~83%
    pct_fuera    = 100 - pct_nombre

    # Paleta (misma familia que el treemap)
    COL_COMUN = "#96660f"   # oro → lo que SÍ comparto
    COL_PROPIO= "#2a2118"   # bronce oscuro → lo que es sólo mío
    FONDO     = "#ffffff"

    fig = go.Figure()

    # ── ANILLO EXTERIOR: POR PESO (dinero) ──
    fig.add_trace(go.Pie(
        values=[portfolio_overlap, active_share],
        labels=["Común", "Sólo mío"],
        hole=0.66,                                      # ← antes: 0.74
        domain=dict(x=[0, 1], y=[0, 1]),                # ← REEMPLAZA radius=1.00
        sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[COL_COMUN, COL_PROPIO],
                    line=dict(color=FONDO, width=2)),
        texttemplate="<b>%{percent}</b>",
        textfont=dict(size=15, color="white"),
        textposition="inside",
        showlegend=False,
        hovertemplate="<b>Por peso</b><br>%{label}: %{percent}<extra></extra>",
    ))

    fig.add_trace(go.Pie(
        values=[pct_nombre, pct_fuera],
        labels=["En mi cartera", "Fuera"],
        hole=0.45,                                      # ← antes: 0.28
        domain=dict(x=[0.20, 0.80], y=[0.20, 0.80]),    # ← REEMPLAZA radius=0.70
        sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[COL_COMUN, COL_PROPIO],
                    line=dict(color=FONDO, width=2)),
        texttemplate="<b>%{percent}</b>",
        textfont=dict(size=14, color="white"),
        textposition="inside",
        showlegend=False,
        hovertemplate="<b>Por nombre</b><br>%{label}: %{percent}<extra></extra>",
    ))

    # ── El número del centro ──
    #fig.add_annotation(
    #    text=f"<b style='font-size:26px;'>{active_share:.0f}%</b><br>"
    #        f"<span style='font-size:11px; color:#64748b;'>ACTIVE SHARE</span>",
    #    x=0.5, y=0.5, xref="paper", yref="paper",
    #    showarrow=False,
    #)

    fig.update_layout(
        plot_bgcolor=FONDO, paper_bgcolor=FONDO,
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        showlegend=False,
    )


        # ── Etiqueta dinámica en el centro de la dona ──
    fig.add_annotation(
        text=f"<b style='font-size:30px;'>{active_share:.0f}%</b><br>"
             f"<span style='font-size:11px; letter-spacing:1px; color:#64748b;'>ACTIVE SHARE</span>",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False,
    )

    fig.update_layout(
        plot_bgcolor=FONDO, paper_bgcolor=FONDO,
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        showlegend=False,
    )

    leyenda_html = f"""
    <div style="font-family:'Segoe UI',sans-serif; text-align:center;
                padding:0 20px 18px 20px; background:{FONDO}; margin:0;">
        <div style="font-size:13px; color:#475569;">
            <span style="color:#96660f; font-size:16px;">●</span>
            <b>En común</b> &nbsp;
            <span style="color:#2a2118; font-size:16px;">●</span>
            <b>Sólo Neko</b>
        </div>
        <div style="font-size:12px; color:#64748b; margin-top:7px; line-height:1.6;">
            <b>Anillo exterior</b> = % del capital ·
            <b>Anillo interior</b> = % de las empresas
        </div>
        <div style="font-size:12px; color:#94a3b8; margin-top:4px;">
            {n_compartidas:,} de {n_empresas_ftaw:,} empresas del FTAW
            ({pct_nombre:.0f}%) · {portfolio_overlap:.1f}% del capital
        </div>
    </div>
    """


    
    html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)

    html_str = html_str.replace("</body>", leyenda_html + "</body>")

    svg_filter = """
    <body>
    <svg width="0" height="0" style="position: absolute;">
      <defs>
        <filter x="-0.08" y="-0.05" width="1.16" height="1.1" id="badge-blanco">
          <feFlood flood-color="white" flood-opacity="0.90" result="bg" />
          <feMerge>
            <feMergeNode in="bg" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    </svg>
    """
    

    custom_css = """
        <style>
            body { margin: 0; background: #ffffff; }
            text.node-label { text-shadow: none !important; stroke: none !important; }
        </style>    
    """
    html_str = html_str.replace("<body>", svg_filter)
    html_str = html_str.replace("</head>", f"{custom_css}</head>")

    
    

    output_html = "dona_overlap_puro.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_str)
        
    print(f"✅ Generado Sankey de solapamiento entre Nekonometrics y FTAW en {output_html}")
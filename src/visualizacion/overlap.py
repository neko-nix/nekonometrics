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


    
    color_yo = "#8b0000"         # Rojo Guinda
    color_ftaw = "#474747"       # Gris Pizarra
    color_overlap = "#047857"    # Verde Esmeralda


    nodes_labels = [

        f"<b>Neko Money</b><br>100% | {n_empresas_yo:,} empresas", 
        f"<b>FTAW</b><br>100% | {n_empresas_ftaw:,} empresas",    
        f"<b>Sólo Neko (Active Share)</b><br>{active_share:.2f}% del capital", 
        f"<b>Sólo FTAW</b><br>{active_share:.2f}% del capital",      
        f"<b>Overlap Financiero: {portfolio_overlap:.2f}%</b><br>({n_compartidas:,} empresas comunes)" 
    ]
    
    nodes_colors = [color_yo, color_ftaw, color_yo, color_ftaw, color_overlap]

    sources = [0, 0, 1, 1]
    targets = [2, 4, 3, 4]
    values  = [
        active_share,     
        portfolio_overlap,
        active_share,  
        portfolio_overlap 
    ]
    
    link_colors = [
        "rgba(139, 0, 0, 0.4)",
        "rgba(139, 0, 0, 0.4)", 
        "rgba(71, 71, 71, 0.4)",
        "rgba(71, 71, 71, 0.4)" 
    ]


    
    fig = go.Figure(data=[go.Sankey(
        textfont=dict(color="#1e293b", size=13, family="Arial"),
        node=dict(
            pad=35,         
            thickness=35,  
            line=dict(color="#1e293b", width=1),
            label=nodes_labels,
            color=nodes_colors,
            
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            hovertemplate="<b>%{source.label}</b> aporta<br><b>%{value:.2f}%</b> a <b>%{target.label}</b><extra></extra>"
        )
    )])
    
    fig.update_layout(
        #title={
        #    "text": f"<b>Simetría de Portafolio: Overlap vs. Active Share</b><br><span style='font-size:13px;color:#64748b;'>Análisis macro de asignación y coincidencias financieras reales</span>",
        #    "font": {"size": 18, "color": "#1e293b", "family": "Arial"},
        #    "y": 0.93, "x": 0.5, "xanchor": "center"
        #},
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=40, r=40, t=0, b=40)
    )


    html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)

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
        text.node-label {
            text-shadow: none !important;
            stroke: none !important;
            filter: url(#badge-blanco); /* 
        }
    </style>
    """
    
    html_str = html_str.replace("<body>", svg_filter)
    html_str = html_str.replace("</head>", f"{custom_css}</head>")
    

    output_html = "sankey_overlap_puro.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_str)
        
    print(f"✅ Generado Sankey de solapamiento entre Neko Money y FTAW en {output_html}")
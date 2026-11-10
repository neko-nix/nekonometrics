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
    COL_COMUN  = "#56422d"   # marrón oscuro → va al valor [0] = "Común"
    COL_PROPIO = "#f0b64b"   # dorado       → va al valor [1] = "Sólo mío"
    
    FONDO     = "#17140f"

    fig = go.Figure()

    categorias = ["Capital", "Empresas"]
    comunes    = [portfolio_overlap, pct_nombre]
    propios    = [active_share,     pct_fuera]

    fig.add_trace(go.Bar(
        x=categorias, y=comunes,
        marker=dict(color='#56422d', line=dict(color=FONDO, width=2)),
        text=[f"{v:.0f}%" for v in comunes],
        textposition='auto', insidetextanchor='middle',
        textfont=dict(size=16, color='#e8e2d4', family='Arial'),
        name="En común", legendgroup="comun", showlegend=True,
        cliponaxis=False,
        hovertemplate="<b>%{x}</b> · en común: %{y:.1f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=categorias, y=propios,
        marker=dict(color='#f0b64b', line=dict(color=FONDO, width=2)),
        text=[f"{v:.0f}%" for v in propios],
        textposition='auto', insidetextanchor='middle',
        textfont=dict(size=16, color='#2a2118', family='Arial'),   # oscuro sobre oro ✅
        name="Diferencial", legendgroup="propio", showlegend=True,
        cliponaxis=False,
        hovertemplate="<b>%{x}</b> · diferencial: %{y:.1f}%<extra></extra>",
    ))

    fig.update_layout(
        barmode='stack',
        bargap=0.52,                       # columnas no tan gordas ✅
        plot_bgcolor=FONDO, paper_bgcolor=FONDO,
        height=480,
        margin=dict(l=20, r=20, t=45, b=35),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=14, color='#e8e2d4'),
            ticks='',
        ),
        yaxis=dict(
            range=[0, 100], showgrid=False, zeroline=False,
            showticklabels=False, ticks='',   # los % ya están adentro ✅
        ),
        legend=dict(orientation='h', y=1.16, x=0.5, xanchor='center',
                    font=dict(size=12, color='#a89c85'),
                    bgcolor='rgba(0,0,0,0)'),
    )



    # ══════════════════════════════════════════════════════════
    #  1) UNIÓN DE AMBAS CARTERAS  ⚠️ ANTES de fig2
    # ══════════════════════════════════════════════════════════
    df_all = pd.merge(
        df_yo_agrupado, df_ftaw_agrupado,
        on='LLAVE_UNICA', how='outer'
    ).fillna(0)

    df_all['DELTA']  = df_all['PESO_YO'] - df_all['PESO_FTAW']
    df_all['NOMBRE'] = df_all['LLAVE_UNICA'].str.rsplit('_', n=1).str[0]

    print(f"Unión: {len(df_all):,} nombres "
          f"({len(df_yo_agrupado):,} míos, {len(df_ftaw_agrupado):,} del FTAW)")
    print(f"Σ PESO_YO   = {df_all['PESO_YO'].sum():.2f}  (debe ser 100)")
    print(f"Σ PESO_FTAW = {df_all['PESO_FTAW'].sum():.2f}  (debe ser 100)")
    print(f"Σ|Δ|/2      = {(0.5 * df_all['DELTA'].abs().sum()):.2f}  "
          f"(debe ser ≈ {active_share:.2f})")

    # ══════════════════════════════════════════════════════════
    #  2) TOP 10 SOBRE + TOP 10 SUB  (nace acá ✅)
    # ══════════════════════════════════════════════════════════
    top = pd.concat([
        df_all.nlargest(10, 'DELTA'),
        df_all.nsmallest(10, 'DELTA')
    ]).drop_duplicates(subset='LLAVE_UNICA').sort_values('DELTA')

    colores = ['#f0b64b' if v > 0 else '#8f5522' for v in top['DELTA']]

    print(f"top: {len(top)} barras  (min {top['DELTA'].min():+.2f} pp, "
          f"max {top['DELTA'].max():+.2f} pp)")

    # ══════════════════════════════════════════════════════════
    #  3) fig2  ⚠️ recién acá, con top ya definido ✅
    # ══════════════════════════════════════════════════════════
    fig2 = go.Figure(go.Bar(
        x=top['NOMBRE'], y=top['DELTA'],
        marker=dict(color=colores, line=dict(color=FONDO, width=1)),
        hovertemplate="<b>%{x}</b><br>Δ peso: %{y:+.2f} pp<extra></extra>",
    ))

    fig2.update_layout(
        plot_bgcolor=FONDO, paper_bgcolor=FONDO,
        height=540,
        margin=dict(l=55, r=20, t=45, b=120),
        bargap=0.35,
        title=dict(
            text="Δ de peso vs FTAW · puntos porcentuales",
            font=dict(size=13, color='#a89c85'),
            x=0.5, xanchor='center'
        ),
        xaxis=dict(tickangle=-55, tickfont=dict(size=10, color='#a89c85'),
                   showgrid=False, zeroline=True, zerolinecolor='#3d2e20'),
        yaxis=dict(showgrid=True, gridcolor='#241c14', zeroline=True,
                   zerolinecolor='#8a7d6a', zerolinewidth=1,
                   ticksuffix=' pp', tickfont=dict(size=10, color='#8a7d6a')),
        showlegend=False,
    )

    # ══════════════════════════════════════════════════════════
    #  4) HTMLs
    # ══════════════════════════════════════════════════════════
    header_html = f"""
    <div style="font-family:'Segoe UI',sans-serif; background:{FONDO};
                padding:14px 0 0 0; text-align:center;">
        <div style="font-size:34px; color:#f0b64b; font-weight:600; line-height:1.1;">
            {active_share:.0f}%
        </div>
        <div style="font-size:10px; letter-spacing:2px; color:#a89c85;
                    margin-top:2px;">ACTIVE SHARE</div>
        <div style="font-size:12px; color:#8a7d6a; margin-top:8px;">
            {n_compartidas:,} de {n_empresas_ftaw:,} empresas del FTAW <br>
            {portfolio_overlap:.1f}% del capital replicado
        </div>
    </div>
    """

    leyenda_html = f"""

    """

    custom_css = """
        <style>
            body { margin: 0; background: #0f0d0a; }
        </style>
    """

    # ══════════════════════════════════════════════════════════
    #  5) ENSAMBLADO
    # ══════════════════════════════════════════════════════════
    #fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False)

    html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)
    html_str = html_str.replace("</head>", custom_css + "</head>")
    html_str = html_str.replace("<body>", "<body>" + header_html, 1)
    #html_str = html_str.replace("</body>", fig2_html + leyenda_html + "</body>")
    html_str = html_str.replace("</body>", leyenda_html + "</body>")
    output_html = "dona_overlap_puro.html"
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_str)

    print(f"✅ Overlap Nekonometrics vs FTAW → {output_html}")
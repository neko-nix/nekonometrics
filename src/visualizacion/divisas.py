import pandas as pd
import plotly.graph_objects as go
import re

def generar_esquema_monedas(df_tabla):

    mapa_monedas = {
        'UNITED STATES': '🇺🇸 USD', 'CAYMAN ISLANDS': '🇺🇸 USD', 'DESCONOCIDO  CASH': '🇺🇸 USD',
        'JAPAN': '🇯🇵 JPY',
        'TAIWAN': '🇹🇼 TWD',
        'SOUTH KOREA': '🇰🇷 KRW',
        'CHINA': '🇨🇳 CNY',
        'UNITED KINGDOM': '🇬🇧 GBP',
        'CANADA': '🇨🇦 CAD',
        'INDIA': '🇮🇳 INR',
        'AUSTRALIA': '🇦🇺 AUD',
        'SWITZERLAND': '🇨🇭 CHF',
        'SWEDEN': '🇸🇪 SEK',
        'ISRAEL': '🇮🇱 ILS',
        'BRAZIL': '🇧🇷 BRL',
        'SOUTH AFRICA': '🇿🇦 ZAR',
        'SAUDI ARABIA': '🇸🇦 SAR',
        'SINGAPORE': '🇸🇬 SGD',
        'HONG KONG': '🇭🇰 HKD', 'BERMUDA': '🇭🇰 HKD',
        'NORWAY': '🇳🇴 NOK',
        'DENMARK': '🇩🇰 DKK',
        'MEXICO': '🇲🇽 MXN',
        'MALAYSIA': '🇲🇾 MYR',
        'THAILAND': '🇹🇭 THB',
        'POLAND': '🇵🇱 PLN',
        'TURKEY': '🇹🇷 TRY',
        'INDONESIA': '🇮🇩 IDR',
        'CHILE': '🇨🇱 CLP',
        'KUWAIT': '🇰🇼 KWD',
        'QATAR': '🇶🇦 QAR',
        'PHILIPPINES': '🇵🇭 PHP',
        'PERU': '🇵🇪 PEN',
        'HUNGARY': '🇭🇺 HUF',
        'COLOMBIA': '🇨🇴 COP',
        'NEW ZEALAND': '🇳🇿 NZD',
        'CZECH REPUBLIC': '🇨🇿 CZK',
        'EGYPT': '🇪🇬 EGP',
        'BAHRAIN': '🇧🇭 BHD',
        # --- EUROZONA ---
        'FRANCE': '🇪🇺 EUR', 'GERMANY': '🇪🇺 EUR', 'NETHERLANDS': '🇪🇺 EUR', 'ITALY': '🇪🇺 EUR', 
        'SPAIN': '🇪🇺 EUR', 'AUSTRIA': '🇪🇺 EUR', 'BELGIUM': '🇪🇺 EUR', 'FINLAND': '🇪🇺 EUR', 
        'GREECE': '🇪🇺 EUR', 'IRELAND': '🇪🇺 EUR', 'PORTUGAL': '🇪🇺 EUR'
    }

    df = df_tabla.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    
  
    if 'COUNTRY' in df.columns:
        col_pais = 'COUNTRY'
    elif 'COUNTRY_CLEAN' in df.columns:
        col_pais = 'COUNTRY_CLEAN'
    else:
        col_pais = [c for c in df.columns if 'PAIS' in c or 'COUNTRY' in c][0]
        
    if 'PESO_MUESTRA' in df.columns:
        col_peso = 'PESO_MUESTRA'
    elif 'POND_WEIGHT' in df.columns:
        col_peso = 'POND_WEIGHT'
    else:
    
        col_peso = [c for c in df.columns if 'WEIGHT' in c or 'MUESTRA' in c or 'PESO' in c][0]

 
    df['PAIS_CLEAN'] = df[col_pais].apply(lambda x: re.sub(r'[^a-zA-Z ]', '', str(x)).strip().upper())
    
 
    df['PESO_NUM'] = df[col_peso].astype(str).str.replace('%', '').str.replace('<', '').str.strip()
    df['PESO_NUM'] = pd.to_numeric(df['PESO_NUM'], errors='coerce').fillna(0.0)

    df['MONEDA'] = df['PAIS_CLEAN'].map(mapa_monedas).fillna('Otras Divisas')
    

    df_monedas = df.groupby('MONEDA')['PESO_NUM'].sum().reset_index()
    

    suma_pesos = df_monedas['PESO_NUM'].sum()
    if suma_pesos > 0:
        df_monedas['PESO_NUM'] = (df_monedas['PESO_NUM'] / suma_pesos) * 100

    UMBRAL = 1.0
    monedas_grandes = df_monedas[df_monedas['PESO_NUM'] >= UMBRAL].copy()
    monedas_chicas = df_monedas[df_monedas['PESO_NUM'] < UMBRAL]
    
    #print(df_monedas)

    if not monedas_chicas.empty:
        fila_otras = pd.DataFrame([{
            'MONEDA': 'Otras Divisas (<1%)',
            'PESO_NUM': monedas_chicas['PESO_NUM'].sum()
        }])
        df_final = pd.concat([monedas_grandes, fila_otras], ignore_index=True)
    else:
        df_final = monedas_grandes


    df_final = df_final.sort_values(by='PESO_NUM', ascending=False)

    colores_dict = {
        # --- BLOQUE NORTEAMÉRICA Y EFECTIVO ---
        '🇺🇸 USD': '#3b5fc4',   # ← en vez de #1e3a8a
        
        # --- BLOQUE ANGLOSAJÓN / PACÍFICO (AZULES) ---
        '🇪🇺 EUR': '#0284c7',  # Azul cielo bandera europea
        '🇦🇺 AUD': '#2563eb',  # Azul marino australiano
        '🇳🇿 NZD': '#1d4ed8',  # Azul Nueva Zelanda
        '🇵🇭 PHP': '#3b82f6',  # Azul Filipinas
        
        # --- BLOQUE COREA Y REINO UNIDO (GRISES / PIZARRAS) ---
        '🇰🇷 KRW': '#475569',  # Gris pizarra (Elegancia minimalista de los trigramas)
        '🇬🇧 GBP': '#64748b',  # Gris azulado profundo (Reino Unido)
        
        # --- BLOQUE ASIA CORONA DE ROJOS (DIFERENCIADOS) ---
        '🇨🇳 CNY': '#dc2626',  # Rojo Escarlata Imperial (China)
        '🇯🇵 JPY': '#be123c',  # Rojo Carmín (El sol naciente de Japón)
        '🇹🇼 TWD': '#f43f5e',  # Rojo Coral Brillante (Taiwán)
        '🇭🇰 HKD': '#fda4af',  # Rosa Orquídea (Bermudas / Hong Kong)
        '🇸🇬 SGD': '#f87171',  # Rojo Suave (Singapur)
        
        # --- BLOQUE EUROPA NO-EUR (ROJOS NÓRDICOS Y ORIENTALES) ---
        '🇨🇭 CHF': '#ef4444',  # Rojo Suizo Puro
        '🇨🇦 CAD': '#991b1b',  # Rojo Arce Oscuro (Canadá)
        '🇳🇴 NOK': '#b91c1c',  # Rojo Nórdico (Noruega)
        '🇩🇰 DKK': '#9a3412',  # Rojo Ladrillo (Dinamarca)
        '🇹🇷 TRY': '#e11d48',  # Rojo Turco
        '🇵🇱 PLN': '#fda4af',  # Blanco/Rojo Polaco
        '🇮🇩 IDR': '#f43f5e',  # Rojo Indonesia
        '🇨🇿 CZK': '#1e4ed8',  # Azul Checo
        '🇧🇭 BHD': '#f43f5e',  # Rojo Bahrein
        
        # --- BLOQUE LATINOAMÉRICA (VERDES Y AMARILLOS) ---
        '🇧🇷 BRL': '#15803d',  # Verde Amazonia (Brasil)
        '🇨🇱 CLP': '#d52b1e',  # Azul Estrella Solitaria (Tu patria)
        '🇲🇽 MXN': '#166534',  # Verde Bandera Mexicano
        '🇨🇴 COP': '#eab308',  # Amarillo Oro Colombiano
        '🇵🇪 PEN': '#ef4444',  # Rojo Perú
        
        # --- BLOQUE MEDIO ORIENTE / ÁFRICA (VERDES OSCUROS Y ORES) ---
        '🇸🇦 SAR': '#14532d',  # Verde Sagrado (Arabia Saudita)
        '🇿🇦 ZAR': '#16a34a',  # Verde Sudafricano
        '🇮🇳 INR': '#ea580c',  # Naranja Azafrán (India)
        '🇮🇱 ILS': '#0284c7',  # Azul Israel
        '🇲🇾 MYR': '#1e3a8a',  # Azul Malasia
        '🇹🇭 THB': '#1e4ed8',  # Azul Tailandia
        '🇰🇼 KWD': '#059669',  # Verde Kuwait
        '🇶🇦 QAR': '#7f1d1d',  # Burdeos Qatarí (Granate profundo)
        '🇭🇺 HUF': '#15803d',  # Verde Húngaro
        '🇪🇬 EGP': '#78350f',  # Dorado Tierra / Águila Egipcia
        
        # --- CATEGORÍA COMODÍN ---
        'Otras Divisas (<1%)': '#cbd5e1',  # Gris claro para el "resto del mundo" agrupado
        'Otras Divisas': '#cbd5e1'
    }
    

    colores_lista = [colores_dict.get(m, '#94a3b8') for m in df_final['MONEDA']]

    fig = go.Figure(data=[go.Pie(
        labels=df_final['MONEDA'],
        values=df_final['PESO_NUM'],
        hole=0.6,
        marker=dict(colors=colores_lista, line=dict(color='#0f0d0a', width=3)),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate='<b>Divisa: %{label}</b><br>Exposición Real: %{value:.2f}%<extra></extra>',
        textfont=dict(size=15, color='#e8e2d4', family='Arial')
    )])


    df_usd = df_final[df_final['MONEDA'] == '🇺🇸 USD']
    peso_usd_real = df_usd['PESO_NUM'].values[0] if not df_usd.empty else 0.0
    
    subtitulo = f"Tu portafolio es un <b>{peso_usd_real:.1f}% Rígido en USD</b>. Alta cobertura natural contra la devaluación del CLP."

    fig.update_layout(
        #title={
        #    'text': f"<b>Exposición Cambiaria Real del Portafolio</b><br><span style='font-size:13px;color:#1e3a8a;'>{subtitulo}</span>",
        #    'font': {'size': 16, 'color': '#2c3e50', 'family': 'Arial'},
        #    'y': 0.94, 'x': 0.5, 'xanchor': 'center'
        #},
        #width=850,
        #height=550, 
        showlegend=False,
        paper_bgcolor='#17140f',
        plot_bgcolor='#17140f',
        margin=dict(l=0, r=0, t=0, b=0)
    )

    output_html = "exposicion_monedas_portafolio.html"
    fig.write_html(output_html, include_plotlyjs="cdn")

    # Parche de fondo de página
    with open(output_html, 'r', encoding='utf-8') as f:
        html_str = f.read()

    html_str = html_str.replace(
        "</head>",
        "<style>html,body{margin:0;padding:0;background:#0f0d0a;"
        "font-family:'Segoe UI',sans-serif;}</style></head>"
    )

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_str)
    print(f"✅ Generada dona de exposición a monedas en: {output_html}")
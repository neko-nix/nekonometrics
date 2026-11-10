import pandas as pd
import plotly.express as px
import os
import numpy as np

def generar_mapa_global(carpeta_holdings, csv_rebalanceo):


    df_cartera = pd.read_csv(csv_rebalanceo)

    pesos_reales = df_cartera.set_index('ticker')['proporcionActual'].to_dict()

    
    mapping = {
        'AVEM.L': 'avem', 'AVGC.L': 'avgc', 'AVGS.L': 'avgs'
    }
    total_world_data = []

    for ticker, file_id in mapping.items():
        file_path = os.path.join(carpeta_holdings, f'All holdings_{file_id}.csv')
        
        if not os.path.exists(file_path):
            print(f"No se encontró: {file_path}")
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                skip_val = 0
                for i, line in enumerate(lines):
                    if 'COMPANY' in line.upper() and 'TICKER' in line.upper():
                        skip_val = i
                        break
            
            df = pd.read_csv(
                file_path, 
                skiprows=skip_val, 
                on_bad_lines='skip',
                engine='python'
            )
            
            df.columns = [str(c).strip().upper() for c in df.columns]
            col_pais = 'COUNTRY'
            if col_pais not in df.columns:
                posibles = [c for c in df.columns if 'COUNTRY' in c or 'REGION' in c]
                if posibles:
                    col_pais = posibles[0]
                else:
                    print(f"No se halló columna de país en {ticker}. Columnas: {df.columns.tolist()}")
                    continue

            df['WEIGHT'] = pd.to_numeric(df['WEIGHT'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
            
            country_weights = df.groupby(col_pais)['WEIGHT'].sum().reset_index()
            country_weights.columns = ['COUNTRY', 'WEIGHT']            

            peso_etf_en_cartera = pesos_reales.get(ticker, 0)
            country_weights['POND_WEIGHT'] = (country_weights['WEIGHT'] ) * peso_etf_en_cartera
            total_world_data.append(country_weights)
            #print(f"Procesado {ticker} con éxito.")

        except Exception as e:
            print(f"Error en {ticker}: {e}")

    if not total_world_data:
        print("No hay datos para concatenar.")
        return

    full_map = pd.concat(total_world_data)
    final_geo = full_map.groupby('COUNTRY')['POND_WEIGHT'].sum().reset_index()

    final_geo['ESCALA_VISUAL'] = np.log10(final_geo['POND_WEIGHT'] + 0.02)
    #print(final_geo['POND_WEIGHT'])
    #print(final_geo['ESCALA_VISUAL'])

    

    ISO3 = {
        'UNITED STATES': 'USA', 'CAYMAN ISLANDS': 'CYM', 'BERMUDA': 'BMU',
        'TAIWAN': 'TWN', 'TAIWAN, PROVINCE OF CHINA': 'TWN',
        'SOUTH KOREA': 'KOR', 'HONG KONG': 'HKG', 'CZECH REPUBLIC': 'CZE',
        'UNITED KINGDOM': 'GBR', 'SAUDI ARABIA': 'SAU', 'SOUTH AFRICA': 'ZAF',
        'NEW ZEALAND': 'NZL', 'UNITED ARAB EMIRATES': 'ARE',
    }

    final_geo['PAIS_UP'] = final_geo['COUNTRY'].astype(str).str.upper().str.strip()
    final_geo = final_geo[final_geo['PAIS_UP'] != 'DESCONOCIDO / CASH']   # ← cash no es un país

    final_geo['ISO3'] = final_geo['PAIS_UP'].map(ISO3)
    faltantes = final_geo[final_geo['ISO3'].isna()]['COUNTRY'].tolist()

    if faltantes:
        print(f"⚠️ Sin ISO3: {faltantes}")
    else:
        print("✅ Todos los países tienen ISO3")

    final_geo['POS_COLOR'] = final_geo['POND_WEIGHT'].rank(method='average', pct=True)

    fig = px.choropleth(
        final_geo,
        locations="COUNTRY",
        locationmode='country names',
        color="ESCALA_VISUAL",
        hover_data={"POND_WEIGHT": ":.2f", "ESCALA_VISUAL": False},
        hover_name="COUNTRY",
        color_continuous_scale=[
            [0.00, '#4a3524'],   # L .046  nogal           (hue 27°)
            [0.15, '#6b4326'],   # L .073  nogal rojizo    (hue 26°)  ← era #6b4a2a
            [0.30, '#8f5522'],   # L .125  COBRE           (hue 28°)  ← era #8a5f1f 💀
            [0.45, '#b06f28'],   # L .207  ámbar cobrizo   (hue 32°)  ← era #a97d28 💀
            [0.60, '#d18f2e'],   # L .334  ámbar claro     (hue 36°)  ← era #c79a34 💀
            [0.80, '#f0b64b'],   # L .56   ORO (tu marca)  (hue 40°)  ✅ igual
            [1.00, '#ffeec6'],   # L .90   marfil dorado   (hue 41°)  ✅ igual 
        ],
        labels={'POND_WEIGHT': '% del Total', "ESCALA_VISUAL": "Peso del país"}
    )

    fig.update_geos(
        bgcolor='#0f0d0a',
        showocean=False,
        showlakes=False,
        showrivers=False,
        showframe=False,
        showland=True,
        landcolor='#1f1913',            # ← países SIN datos: huecos oscuros ✅
        showcoastlines=True,
        coastlinecolor='#3d2e20',       # ← costa oscura sobre el oro
        showcountries=True,
        countrycolor='#2a2118',         # ← bordes oscuros: mosaico nítido
    )

    min_log = final_geo['ESCALA_VISUAL'].min()
    max_log = final_geo['ESCALA_VISUAL'].max()

    tick_positions = np.linspace(min_log, max_log, 5)
    porcentajes_calculados = (10**tick_positions) - 0.02
    tick_labels = []
    for p in porcentajes_calculados:
        if p < 0.01:
            tick_labels.append("< 0.01%")
        else:
            tick_labels.append(f"{p:.1f}%")

    fig.update_layout(
        paper_bgcolor='#0f0d0a',
        plot_bgcolor='#0f0d0a',
        hoverlabel=dict(
            bgcolor='#1f1913',
            bordercolor='#3d2e20',
            font=dict(color='#e8e2d4', size=12)
        ),
        coloraxis=dict(
            colorbar=dict(
                tickmode="array",
                tickvals=list(tick_positions),
                ticktext=tick_labels,
                tickfont=dict(size=12, color='#a89c85'),
                orientation="h",
                len=0.90,
                y=-0.12,
                x=0.5,
                xanchor="center",
                thickness=10,
                outlinewidth=0,
                title=dict(text="% del portafolio",
                           font=dict(size=11, color='#a89c85')),
            )
        ),
        margin=dict(l=0, r=0, t=0, b=70)     # ← 70 para que entre la colorbar
    )

    #fig.show()
    outputName = "mapa_interactivo.html"
    fig.write_html(outputName, include_plotlyjs="cdn")

    with open(outputName, 'r', encoding='utf-8') as f:
        html_str = f.read()

    html_str = html_str.replace(
        "</head>",
        "<style>html,body{margin:0;padding:0;background:#0f0d0a;"
        "font-family:'Segoe UI',sans-serif;}</style></head>"
    )

    with open(outputName, 'w', encoding='utf-8') as f:
        f.write(html_str)
    print(f"✅ Generado mapa interactivo con éxito en {outputName}")

#generar_mapa_global('data/', "data/ultimosDatos.csv")
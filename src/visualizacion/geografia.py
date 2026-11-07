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

    final_geo['ESCALA_VISUAL'] = np.log10(final_geo['POND_WEIGHT'] + 0.1)
    #print(final_geo['POND_WEIGHT'])
    #print(final_geo['ESCALA_VISUAL'])


    # Graficar
    fig = px.choropleth(
        final_geo, 
        locations="COUNTRY",
        locationmode='country names',
        color="ESCALA_VISUAL",
        hover_data={"POND_WEIGHT": ":.2f", "ESCALA_VISUAL": False},
        hover_name="COUNTRY",
        color_continuous_scale='reds',
        #title = 'Distribución Geográfica del Capital',
        labels={'POND_WEIGHT': '% del Total', "ESCALA_VISUAL": "Peso del país"}
    )

    fig.update_geos(
        showocean=False, oceancolor="LightBlue",
        showlakes=False, lakecolor="LightBlue",
        showcountries=True, countrycolor="Black"
    )

    min_log = final_geo['ESCALA_VISUAL'].min()
    max_log = final_geo['ESCALA_VISUAL'].max()

    tick_positions = np.linspace(min_log, max_log, 5)
    porcentajes_calculados = (10**tick_positions) - 0.1
    tick_labels = []
    for p in porcentajes_calculados:
        if p < 0.01:
            tick_labels.append("0.0%")
        else:
            tick_labels.append(f"{p:.1f}%")

    fig.update_layout(
        coloraxis=dict(
            colorbar=dict(
                tickmode="array",
                tickvals=list(tick_positions), 
                ticktext=tick_labels,
                #title_font_size=30, 
                tickfont_size=15,
                orientation = "h",
                len = 0.95,
                y = -0.15,
                x = 0.5,
                xanchor = "center"
            )
        )#,
        #title_font_size = 30
    )

    fig.update_layout(
    #    height=600,    
        margin=dict(l=0, r=0, t=0, b=0) 
    )

    #fig.show()
    outputName = "mapa_interactivo.html"
    fig.write_html(outputName, include_plotlyjs="cdn")
    print(f"✅ Generado mapa interactivo con éxito en {outputName}")

#generar_mapa_global('data/', "data/ultimosDatos.csv")
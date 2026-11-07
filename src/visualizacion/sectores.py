import pandas as pd
import plotly.graph_objects as go
import urllib.request
from pathlib import Path

mapeo_sectores = {
    # 💻 Tecnología
    'INFORMATION TECHNOLOGY': '💻 Tecnología',
    'TECHNOLOGY': '💻 Tecnología',
    'TECNOLOGÍA DE LA INFORMACIÓN': '💻 Tecnología',
    
    # 🏦 Financiero
    'FINANCIALS': '🏦 Financiero',
    'FINANCIAL SERVICES': '🏦 Financiero',
    'FINANCIEROS': '🏦 Financiero',
    
    # 🩺 Salud
    'HEALTH CARE': '🩺 Salud',
    'HEALTHCARE': '🩺 Salud',
    'CUIDADO DE LA SALUD': '🩺 Salud',
    
    # 🛍️ Consumo Cíclico
    'CONSUMER DISCRETIONARY': '🛍️ Consumo Cíclico',
    'CONSUMER CYCLICAL': '🛍️ Consumo Cíclico',
    'CONSUMO DISCRECIONAL': '🛍️ Consumo Cíclico',
    
    # 🛒 Consumo Básico
    'CONSUMER STAPLES': '🛒 Consumo Básico',
    'CONSUMER DEFENSIVE': '🛒 Consumo Básico',
    'PRODUCTOS BÁSICOS DE CONSUMO': '🛒 Consumo Básico',
    
    # 🏗️ Industrial
    'INDUSTRIALS': '🏗️ Industrial',
    'INDUSTRIALES': '🏗️ Industrial',
    
    # ⚡ Energía
    'ENERGY': '⚡ Energía',
    'ENERGÍA': '⚡ Energía',
    
    # 🧪 Materiales
    'MATERIALS': '🧪 Materiales',
    'MATERIALES': '🧪 Materiales',
    
    # 💧 Servicios Básicos
    'UTILITIES': '💧 Servicios Básicos',
    'SERVICIOS': '💧 Servicios Básicos',
    
    # 🏢 Bienes Raíces
    'REAL ESTATE': '🏢 Bienes Raíces',
    'INMOBILIARIO': '🏢 Bienes Raíces',
    
    # 📣 Comunicación
    'COMMUNICATION SERVICES': '📣 Comunicación',
    'COMMUNICATION': '📣 Comunicación',
    'TELECOMMUNICATIONS': '📣 Comunicación',
    'COMUNICACIÓN': '📣 Comunicación',
    
    # 💵 Efectivo
    'EFECTIVO Y DERIVADOS': '💵 Efectivo / Cash',
    'CASH': '💵 Efectivo / Cash',
    'CASH AND/OR DERIVATIVES': '💵 Efectivo / Cash',
    'LIQUIDEZ': '💵 Efectivo / Cash',
    'OTROS': '💵 Efectivo / Cash', 
    'OTHER': '💵 Efectivo / Cash',
}


def obtener_sector_unificado(val):
    if pd.isna(val):
        return None
    
    val_str = str(val).strip()
    

    if val_str in mapeo_sectores.values():
        return val_str
        
    if val_str.startswith("📦 "):
        val_str = val_str[2:]

    val_clean = val_str.upper().strip()
    
    if val_clean in ['NAN', 'NONE', '', 'UNKNOWN', 'TOTAL']:
        return None
        
    return mapeo_sectores.get(val_clean, f"📦 {val_str.title()}")


def generar_comparativa_sectores_ftaw(df_tabla, csv_ftaw):

    df_tabla['SECTOR_UNIFICADO'] = df_tabla['SECTOR_CLEAN'].apply(obtener_sector_unificado)
    df_tabla = df_tabla.dropna(subset=['SECTOR_UNIFICADO'])
    
    mis_sectores = df_tabla.groupby('SECTOR_UNIFICADO')['PESO_MUESTRA'].sum().reset_index()
    mis_sectores.columns = ['SECTOR', 'PORCENTAJE_YO']

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
        
        col_peso_ftaw = None
        for c in df_ftaw_raw.columns:
            if 'WEIGHT' in c or 'PESO' in c or 'POND' in c:
                col_peso_ftaw = c
                break
                
        if col_peso_ftaw is None:
            print("Error: No se encontró la columna de peso/porcentaje.")
            return

        df_ftaw_raw[col_peso_ftaw] = (
            df_ftaw_raw[col_peso_ftaw]
            .astype(str)
            .str.replace('"', '', regex=False)
            .str.replace('%', '', regex=False)
            .str.strip()
        )
        df_ftaw_raw[col_peso_ftaw] = pd.to_numeric(df_ftaw_raw[col_peso_ftaw], errors='coerce').fillna(0)
        
        df_ftaw_raw['SECTOR_UNIFICADO'] = df_ftaw_raw['SECTOR'].apply(obtener_sector_unificado)
        df_ftaw_raw = df_ftaw_raw.dropna(subset=['SECTOR_UNIFICADO'])
        
        ftaw_sectores = df_ftaw_raw.groupby('SECTOR_UNIFICADO')[col_peso_ftaw].sum().reset_index()
        ftaw_sectores.columns = ['SECTOR', 'PORCENTAJE_FTAW']
        
    except Exception as e:
        print(f"Error al procesar el CSV de FTAW: {e}")
        return

    df_sectores = pd.merge(mis_sectores, ftaw_sectores, on='SECTOR', how='outer').fillna(0)
    df_sectores = df_sectores.sort_values(by='PORCENTAJE_YO', ascending=True)

    df_sectores['DIFERENCIA'] = df_sectores['PORCENTAJE_YO'] - df_sectores['PORCENTAJE_FTAW']
    def generar_etiqueta_eje(row):
        dif = row['DIFERENCIA']
        color = "#15803d" if dif > 0 else ("#e74c3c" if dif < 0 else "#95a5a6")
        signo = "+" if dif > 0 else ""
        return f"{row['SECTOR']} <br><span style='font-size:12px; color:{color};'><b>Dif: {signo}{dif:.2f}%</b></span>"
    
    df_sectores['Y_LABEL'] = df_sectores.apply(generar_etiqueta_eje, axis=1)

 
    
    fig = go.Figure()
    max_weight = max(df_sectores['PORCENTAJE_FTAW'].max(), df_sectores['PORCENTAJE_YO'].max())
    fig.add_trace(go.Bar(
        y=df_sectores['Y_LABEL'], 
        x=df_sectores['PORCENTAJE_FTAW'],
        name='FTAW',
        orientation='h',
        marker=dict(
            color=df_sectores['PORCENTAJE_FTAW'], 
            colorscale='greys',           
            cauto=False,                   
            cmin=-10,                   
            cmax=max_weight
        ),
        hovertemplate='%{y}<br>FTAW: %{x:.2f}%<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        y=df_sectores['Y_LABEL'], 
        x=df_sectores['PORCENTAJE_YO'],
        name='Neko Money',
        orientation='h',
        marker=dict(
            color=df_sectores['PORCENTAJE_YO'], 
            colorscale='reds',       
            cauto=False,                   
            cmin=-10,                   
            cmax=max_weight
              
        ),
        hovertemplate='%{y}<br>Nekonometrics: %{x:.2f}%<extra></extra>'
    ))

    fig.update_layout(
        #title={
        #    'text': '<b>Asignación Sectorial: Mi Portafolio vs. FTAW (iShares)</b>',
        #    'font': {'size': 16, 'color': '#2c3e50', 'family': 'Arial'},
        #    'y': 0.95, 'x': 0.5, 'xanchor': 'center'
        #},
        barmode='group',
        bargap=0.15,      
        bargroupgap=0.05,   
        #height=650,   
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=0, b=0) 
        #margin=dict(l=200, r=20, t=60, b=60) # Aumenté margen izquierdo por si el texto es largo
    )

    fig.update_xaxes(showgrid=True, gridcolor='#f5f7f8', ticksuffix='%', zeroline=True, zerolinecolor='black')
    

    fig.update_yaxes(
        showgrid=False,
        categoryorder='array',
        categoryarray=df_sectores['Y_LABEL'],
        tickfont=dict(
            size=15,  
            color='#2c3e50',
            family='Arial'
        )
    )

    output_html = "comparativa_sectores_ftaw.html"
    fig.write_html(output_html, include_plotlyjs="cdn")
    print(f"✅ Generado comparación de exposición a factores en: {output_html}!")
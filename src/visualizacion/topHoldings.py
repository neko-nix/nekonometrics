import os
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from src.visualizacion import tablaPaises, sectores, overlap, divisas

def generar_top_holdings(carpeta_holdings, csv_rebalanceo):
    if not Path(csv_rebalanceo).exists():
        print(f"Error: {csv_rebalanceo} no existe.")
        return

    df_cartera = pd.read_csv(csv_rebalanceo)
    pesos_reales = df_cartera.set_index('ticker')['proporcionActual'].to_dict()

    # mapping = {
    #     'AVEM.DE': 'avem', 'AVWC.DE': 'avwc', 'AVWS.DE': 'avws'
    # }

    mapping = {
        'AVEM.L': 'avem', 'AVGC.L': 'avgc', 'AVGS.L': 'avgs'
    }
    

    all_holdings_data = []

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
            
  
            col_empresa = 'COMPANY'
            if col_empresa not in df.columns:
                posibles = [c for c in df.columns if 'NAME' in c or 'COMPANY' in c or 'DESCRIPTION' in c]
                if posibles:
                    col_empresa = posibles[0]
                else:
                    print(f"No se halló columna de empresa en {ticker}. Columnas: {df.columns.tolist()}")
                    continue


            df['WEIGHT'] = pd.to_numeric(df['WEIGHT'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)
            

            peso_etf_en_cartera = pesos_reales.get(ticker, 0)
            

            if peso_etf_en_cartera == 0:
                continue

            df_limpio = df[[col_empresa, 'TICKER', 'WEIGHT', "COUNTRY", "BASEMARKETVALUE", "SECTOR", "ISIN"]].copy()
            df_limpio.columns = ['COMPANY', 'ASSET_TICKER', 'WEIGHT', "COUNTRY", "MARKET_VALUE", "SECTOR", "ISIN"]
            
            df_limpio["WEIGHT"] = df_limpio["MARKET_VALUE"] / df_limpio["MARKET_VALUE"].sum()
            df_limpio['POND_WEIGHT'] = df_limpio['WEIGHT'] * peso_etf_en_cartera
            
            all_holdings_data.append(df_limpio)

        except Exception as e:
            print(f"Error en {ticker}: {e}")

    if not all_holdings_data:
        print("No hay datos de holdings para consolidar.")
        return


    df_consolidado = pd.concat(all_holdings_data, ignore_index=True)

    df_global = df_consolidado.groupby(['COMPANY', 'ASSET_TICKER', "COUNTRY", "SECTOR", "ISIN"])['POND_WEIGHT'].sum().reset_index()


    # mapeo_sinonimos = {
    #     'GOOGL': 'GOOG',  
    #     '2330': 'TSM',  
    # }
    # df_global['ASSET_TICKER'] = df_global['ASSET_TICKER'].replace(mapeo_sinonimos)

    import re

    def limpiar_nombre_con_isin(row):
        isin = str(row['ISIN']).strip().upper()
        nom = str(row['COMPANY']).upper()
        
        # Mapeo de Empresas según el ISIN
        mapeo_isin = {
            'TW0002330008': 'Taiwan Semiconductor Company', 
            'US8740391003': 'Taiwan Semiconductor Company', 
            'US02079K1079': 'Alphabet',              
            'US02079K3059': 'Alphabet',               
            "US30303M1027": "Meta Platforms",
            'KR7000660001': 'SK Hynix',
            'US7960508882': 'Samsung Electronics'          
        }
        
        if isin in mapeo_isin:
            return mapeo_isin[isin]
            
       
        patrones_ruido = [
            r'\b[A-Z]{3}\s?\d+[\d\.]*',
            r'\b(CHF|USD|EUR|HKD|TWD|CNY|GBP|ILS|KRW)\.?\d+',
            r'\bCL\s?[A-Z0-9]\b',
            r'\b(COMMON STOCK|COMMON|STOCK|CORP|INC|LTD|LLC|NV|PLC|CO|INTL|HOLDINGS|REG|SH|SHARES|CRP|ADR|GDR|SPONS|NY|SHS|SHRS)\b\.?',
            r'\s?\+.*', r'\s/.*', r'\s\(.*\)'
        ]
        
        for patron in patrones_ruido:
            nom = re.sub(patron, '', nom, flags=re.IGNORECASE)
            
        return nom.strip().title()

    
    df_global['COMPANY_CLEAN'] = df_global.apply(limpiar_nombre_con_isin, axis=1)
    

    df_global = df_global.groupby(['COMPANY_CLEAN', 'ASSET_TICKER', "COUNTRY", "SECTOR"])['POND_WEIGHT'].sum().reset_index()
    df_global_ordenado = df_global.sort_values(by='POND_WEIGHT', ascending=False)
    #df_global_ordenado.to_csv("holdingsTotales.csv", index=False)
    
    df_top10 = (
        df_global.groupby('COMPANY_CLEAN')
        .agg({
            'POND_WEIGHT': 'sum',  
            'ASSET_TICKER': lambda x: ' / '.join(x.dropna().unique()),  
            'COUNTRY': 'first'    
        })
        .reset_index()
    )

    
    df_top10 = df_top10.sort_values(by='POND_WEIGHT', ascending=False).head(10)
    df_top10 = df_top10.iloc[::-1]

 
    df_tabla = df_global_ordenado.copy()
    
    
    peso_total_por_pais = df_tabla.groupby('COUNTRY')['POND_WEIGHT'].transform('sum')
    df_tabla['PESO_RELATIVO_PAIS'] = df_tabla['POND_WEIGHT'] / peso_total_por_pais
    
    
    df_tabla['PESO_MUESTRA'] = df_tabla['POND_WEIGHT'] * 100
    df_tabla['PESO_REL_MUESTRA'] = df_tabla['PESO_RELATIVO_PAIS'] * 100
    
    
    df_tabla['COUNTRY_CLEAN'] = df_tabla['COUNTRY'].astype(str).str.upper().str.strip().map(
        lambda x: "South Korea" if x in ['KOREA, REPUBLIC OF', 'SOUTH KOREA'] else x.title()
    )
    
    
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
        'CASH': '💵 Efectivo / Cash'
    }
    
    
    df_tabla['SECTOR_CLEAN'] = df_tabla['SECTOR'].astype(str).str.upper().str.strip().map(
        lambda x: mapeo_sectores.get(x, f"📦 {x.title()}")
    )
    
    

    #print(df_tabla.head(10))
    
    tablaPaises.generar_reporte_paises(df_tabla)
   
    ruta_csv = "data/ftaw_holdings.csv"
    #if descargar_holdings_ftaw(ruta_csv):
    sectores.generar_comparativa_sectores_ftaw(df_tabla, ruta_csv)

    overlap.generar_sankey_overlap_puro(df_tabla, ruta_csv)

    #costos.generar_comparativa_costos_hardcoded(pd.read_csv("data/ultimosDatos.csv"))

    divisas.generar_esquema_monedas(df_tabla)

    #factores.generar_analisis_factores()
        
   
    
    
    df_json = df_tabla[['COMPANY_CLEAN', 'ASSET_TICKER', 'SECTOR_CLEAN', 'COUNTRY_CLEAN']].copy()

    df_json.columns = ['empresa', 'ticker', 'sector', 'pais']
    
    
    df_json['peso_global_num'] = df_tabla['PESO_MUESTRA']
    df_json['peso_rel_pais_num'] = df_tabla['PESO_REL_MUESTRA']
    
    
    df_json['peso_global_str'] = df_tabla['PESO_MUESTRA'].map(lambda x: f"{x:.2f}%" if x >= 0.01 else "< 0.01%")
    df_json['peso_rel_pais_str'] = df_tabla['PESO_REL_MUESTRA'].map(lambda x: f"{x:.2f}%" if x >= 0.01 else "< 0.01%")
    

    json_pure_data = df_json.to_json(orient='records', force_ascii=False)
    
   
    html_final = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Holdings Nekonometrics</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.dataTables.min.css">
        
    <style>
        :root {{
            --bg:      #0f0d0a;
            --surface: #17140f;
            --surface2:#1f1b14;
            --tabaco:  #241c14;
            --border:  #2a2018;
            --border2: #3d2f22;
            --bronce:  #54402c;
            --text:    #e8e2d4;
            --strong:  #f7f2e4;
            --muted:   #a89c85;
            --faint:   #8a8070;
            --oro:     #f0b64b;
            --oro-br:  #ffd280;
            --oro-dim: #c89a45;
            --ink:     #1f1710;   /* texto SOBRE oro */
        }}

        body {{
            background-color: transparent !important;
            margin: 0; padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            color: var(--text);
        }}

        #tabla-dinamica {{
            width: 100% !important;
            margin-top: 10px !important;
            border-collapse: collapse !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }}

        /* ── CABECERA: oro sobre tabaco ── */
        #tabla-dinamica thead th {{
            background-color: var(--tabaco) !important;
            color: var(--oro) !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            padding: 11px 12px !important;
            border-bottom: 2px solid var(--bronce) !important;
            text-align: left !important;
        }}

        /* ── CELDAS ── */
        #tabla-dinamica tbody td {{
            font-size: 14px !important;
            padding: 10px 12px !important;
            border-bottom: 1px solid var(--border) !important;
            color: var(--text) !important;
            line-height: 1.4 !important;
        }}
        #tabla-dinamica tbody tr:nth-child(even) {{
            background-color: rgba(240, 182, 75, 0.030) !important;
        }}
        #tabla-dinamica tbody tr:hover {{
            background-color: rgba(240, 182, 75, 0.070) !important;
        }}

        /* ── FILTRO / BUSCADOR ── */
        .dataTables_wrapper .dataTables_filter {{ font-size: 14px !important; color: var(--muted) !important; }}
        .dataTables_wrapper .dataTables_filter input {{
            background: var(--surface) !important;
            border: 1px solid var(--border2) !important;
            border-radius: 4px !important;
            padding: 5px 10px !important;
            margin-left: 8px !important;
            font-size: 14px !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: var(--oro) !important;
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(240,182,75,0.15) !important;
        }}

        /* ── SELECTOR "10 / 15 / 25" (era blanco puro) ── */
        .dataTables_wrapper select,
        .dataTables_wrapper input {{
            background: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border2) !important;
            border-radius: 4px !important;
        }}

        /* ── INFO + PAGINACIÓN ── */
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_paginate {{
            font-size: 14px !important;
            color: var(--muted) !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button {{
            color: var(--muted) !important;
            border: 1px solid transparent !important;
            border-radius: 4px !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
            background: rgba(240,182,75,0.12) !important;
            color: var(--oro) !important;
            border-color: var(--border2) !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current,
        .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
            background: var(--oro) !important;
            color: var(--ink) !important;
            border: 1px solid var(--oro) !important;
            border-radius: 4px !important;
            font-weight: 700 !important;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled,
        .dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover {{
            color: var(--faint) !important;
            background: transparent !important;
        }}

        /* ── BOTÓN "COLUMNAS VISIBLES": oro con tinta oscura ── */
        .dt-button.buttons-colvis {{
            background: var(--oro) !important;
            color: var(--ink) !important;
            border: 1px solid var(--oro) !important;
            border-radius: 4px !important;
            padding: 6px 12px !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            margin-bottom: 15px !important;
        }}
        .dt-button.buttons-colvis:hover {{
            background: var(--oro-br) !important;
            border-color: var(--oro-br) !important;
        }}

        /* ── FLECHITAS DE ORDEN: invisibles en oscuro (esto las reemplaza) ── */
        table.dataTable thead th.sorting,
        table.dataTable thead th.sorting_asc,
        table.dataTable thead th.sorting_desc {{ background-image: none !important; }}
        table.dataTable thead th.sorting::after {{
            content: "⇅"; float: right; opacity: .30; color: var(--faint); font-size: 11px;
        }}
        table.dataTable thead th.sorting_asc::after {{
            content: "▲"; float: right; color: var(--oro); font-size: 10px;
        }}
        table.dataTable thead th.sorting_desc::after {{
            content: "▼"; float: right; color: var(--oro); font-size: 10px;
        }}
    </style>
    <body>

        <table id="tabla-dinamica" class="display compact" border="0">
            <thead>
                <tr>
                    <th>Empresa</th>
                    <th>Ticker</th>
                    <th>Sector</th>
                    <th>País</th>
                    <th>Peso Global</th>
                    <th>Peso Rel. País</th>
                </tr>
            </thead>
        </table>

        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
        <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.colVis.min.js"></script>
        
        <script>
            $(document).ready(function() {{
                var mapeoBanderas = {{
                    "United States": "🇺🇸", "Canada": "🇨🇦", "Mexico": "🇲🇽",
                    "Costa Rica": "🇨🇷", "Cuba": "🇨🇺", "Dominican Republic": "🇩🇴", 
                    "El Salvador": "🇸🇻", "Guatemala": "🇬🇹", "Honduras": "🇭🇳", 
                    "Jamaica": "🇯🇲", "Nicaragua": "🇳🇮", "Panama": "🇵🇦", 
                    "Puerto Rico": "🇵🇷", "Bahamas": "🇧🇸", "Trinidad And Tobago": "🇹🇹",
                    "Argentina": "🇦🇷", "Bolivia": "🇧🇴", "Brazil": "🇧🇷", 
                    "Chile": "🇨🇱", "Colombia": "🇨🇴", "Ecuador": "🇪🇨", 
                    "Guyana": "🇬🇾", "Paraguay": "🇵🇾", "Peru": "🇵🇪", 
                    "Suriname": "🇸🇷", "Uruguay": "🇺🇾", "Venezuela": "🇻🇪",
                    "United Kingdom": "🇬🇧", "Germany": "🇩🇪", "France": "🇫🇷", 
                    "Italy": "🇮🇹", "Spain": "🇪🇸", "Netherlands": "🇳🇱", 
                    "Belgium": "🇧🇪", "Switzerland": "🇨🇭", "Austria": "🇦🇹", 
                    "Ireland": "🇮🇪", "Luxembourg": "🇱🇺", "Monaco": "🇲🇨",
                    "Denmark": "🇩🇰", "Finland": "🇫🇮", "Norway": "🇳🇴", 
                    "Sweden": "🇸🇪", "Iceland": "🇮🇸",
                    "Portugal": "🇵🇹", "Greece": "🇬🇷", "Poland": "🇵🇱", 
                    "Czech Republic": "🇨🇿", "Czechia": "🇨🇿", "Hungary": "🇭🇺", 
                    "Romania": "🇷🇴", "Slovakia": "🇸🇰", "Slovenia": "🇸🇮", 
                    "Bulgaria": "🇧🇬", "Croatia": "🇭🇷", "Lithuania": "🇱🇹", 
                    "Latvia": "🇱🇻", "Estonia": "🇪🇪", "Cyprus": "🇨🇾", 
                    "Malta": "🇲🇹", "Turkey": "🇹🇷", "Ukraine": "🇺🇦", 
                    "Russia": "🇷🇺", "Belarus": "🇧🇾", "Moldova": "🇲🇩",
                    "Albania": "🇦🇱", "Serbia": "🇷🇸", "Bosnia And Herzegovina": "🇧🇦",
                    "Montenegro": "🇲🇪", "North Macedonia": "🇲🇰", "Georgia": "🇬🇪",
                    "Japan": "🇯🇵", "China": "🇨🇳", "South Korea": "🇰🇷", 
                    "Taiwan": "🇹🇼", "Taiwan, Province Of China": "🇹🇼", "Hong Kong": "🇭🇰", 
                    "Macau": "🇲🇴", "Singapore": "🇸🇬", "Malaysia": "🇲🇾", 
                    "Indonesia": "🇮🇩", "Philippines": "🇵🇭", "Thailand": "🇹🇭", 
                    "Vietnam": "🇻🇳", "Cambodia": "🇰🇭", "Laos": "🇱🇦", 
                    "Myanmar": "🇲🇲", "Mongolia": "🇲🇳", "Brunei": "🇧🇳",
                    "India": "🇮🇳", "Pakistan": "🇵🇰", "Bangladesh": "🇧🇩", 
                    "Sri Lanka": "🇱🇰", "Nepal": "🇳🇵", "Kazakhstan": "🇰🇿", 
                    "Uzbekistan": "🇺🇿", "Kyrgyzstan": "🇰🇬", "Tajikistan": "🇹🇯", 
                    "Turkmenistan": "🇹🇲", "Afghanistan": "🇦🇫", "Maldives": "🇲🇻",
                    "Israel": "🇮🇱", "Saudi Arabia": "🇸🇦", "United Arab Emirates": "🇦🇪", 
                    "Qatar": "🇶🇦", "Kuwait": "🇰🇼", "Bahrain": "🇧🇭", 
                    "Oman": "🇴🇲", "Jordan": "🇯🇴", "Egypt": "🇪🇬", 
                    "Lebanon": "🇱🇧", "Iran": "🇮🇷", "Iraq": "🇮🇶", 
                    "Syria": "🇸🇾", "Yemen": "🇾🇪",
                    "Australia": "🇦🇺", "New Zealand": "🇳🇿", "Papua New Guinea": "🇵🇬", 
                    "Fiji": "🇫🇯", "Samoa": "🇼🇸", "Tonga": "🇹🇴", 
                    "Solomon Islands": "🇸🇧", "Vanuatu": "🇻🇺",
                    "South Africa": "🇿🇦", "Nigeria": "🇳🇬", "Kenya": "🇰🇪", 
                    "Morocco": "🇲🇦", "Algeria": "🇩🇿", "Tunisia": "🇹🇳", 
                    "Ghana": "🇬🇭", "Angola": "🇦🇴", "Ivory Coast": "🇨🇮",
                    "Cote D'Ivoire": "🇨🇮", "Ethiopia": "🇪🇹", "Tanzania": "🇹🇿", 
                    "Uganda": "🇺🇬", "Zambia": "🇿🇲", "Zimbabwe": "🇿🇼", 
                    "Mauritius": "🇲🇺", "Botswana": "🇧🇼", "Namibia": "🇳🇦", 
                    "Senegal": "🇸🇳", "Cameroon": "🇨🇲", "Mozambique": "🇲🇿",
                    "Madagascar": "🇲🇬", "Libya": "🇱🇾", "Sudan": "🇸🇩",
                    "Gabon": "🇬🇦", "Mali": "🇲🇱", "Burkina Faso": "🇧🇫",
                    "Malawi": "🇲🇼", "Rwanda": "🇷🇼", "Chad": "🇹🇩",
                    "Somalia": "🇸🇴", "Guinea": "🇬🇳", "Benin": "🇧🇯",
                    "Burundi": "🇧🇮", "Togo": "🇹🇬", "Sierra Leone": "🇸🇱",
                    "Congo": "🇨🇬", "Congo, Democratic Republic": "🇨🇩", "Djibouti": "🇩🇯",
                    "Equatorial Guinea": "🇬🇶", "Eritrea": "🇪🇷", "Eswatini": "🇸🇿",
                    "Gambia": "🇬🇲", "Guinea-Bissau": "🇬🇼", "Lesotho": "🇱🇸",
                    "Liberia": "🇱🇷", "Mauritania": "🇲🇷", "Niger": "🇳🇪",
                    "Sao Tome And Principe": "🇸🇹", "Seychelles": "🇸🇨", "South Sudan": "🇸🇸",
                    "Cayman Islands": "🇰🇾", "Bermuda": "🇧🇲", "British Virgin Islands": "🇻🇬", 
                    "Jersey": "🇯🇪", "Guernsey": "🇬🇬", "Isle Of Man": "🇮🇲", 
                    "Gibraltar": "🇬🇮", "Liechtenstein": "🇱🇮", "Curacao": "🇨🇼", 
                    "Aruba": "🇦🇼", "Marshall Islands": "🇲🇭"
                }};
                
                var datosPortafolio = {json_pure_data};

                $('#tabla-dinamica').DataTable({{
                    "data": datosPortafolio,
                    "deferRender": true,
                    "pageLength": 15, 
                    "lengthMenu": [[10, 15, 25, 50, 100, -1], [10, 15, 25, 50, 100, "Todos"]],         
                    
                    
                    
                    
                    "columns": [
                        {{ "data": "empresa" }},
                        {{ "data": "ticker" }},
                        {{ "data": "sector" }},
                        {{ "data": "pais" }},
                        {{ "data": "peso_global_num" }}, 
                        {{ "data": "peso_rel_pais_num" }}
                    ],
                    
                    
                    "order": [[4, "desc"]],

                    "dom": 'Blfrtip', 
                    "buttons": [
                        {{
                            extend: 'colvis',
                            text: '👁️ Columnas Visibles',
                            postfixButtons: [ 'colvisRestore' ]
                        }}
                    ],
                    
                    "columnDefs": [
                        {{
                            "targets": [3], 
                            "render": function ( data, type, row ) {{
                                if ( type === 'sort' || type === 'type' ) {{
                                    return data; 
                                }}
                                var emoji = mapeoBanderas[data] || '🌐';
                                return emoji + " " + data;
                            }}
                        }},
                        
                        {{
                            "targets": [4], 
                            "render": function ( data, type, row ) {{
                                // Si DataTables está dibujando la celda en pantalla, dale el string con %
                                if ( type === 'display' ) {{
                                    return row.peso_global_str;
                                }}
                                // Si está ordenando o filtrando, usa el número puro (data)
                                return data;
                            }}
                        }},
                       
                        {{
                            "targets": [5], 
                            "render": function ( data, type, row ) {{
                                if ( type === 'display' ) {{
                                    return row.peso_rel_pais_str;
                                }}
                                return data;
                            }}
                        }}
                    ],
                    "language": {{
                        "url": "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json"
                    }}
                }});
            }});
        </script>
    </body>
    
    </html>
    """
    
    output_tabla = "tabla_holdings.html"
    with open(output_tabla, "w", encoding="utf-8") as f:
        f.write(html_final)
        
    print(f"✅ Generada Tabla dinámica con lista completa de holdings de Nekonometrics en: {output_tabla}")
   
    #print(df_top10)


    
    bench_by_ticker = {}
    bench_by_name = {}
    ruta_csv="data/ftaw_holdings.csv"

    try:
        if Path(ruta_csv).exists():
            with open(ruta_csv, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()
            
            linea_header = 0
            for idx, linea in enumerate(lineas):
                if 'Ticker' in linea or 'Ticker' in linea.split(',')[0]:
                    linea_header = idx
                    break
            
            df_ftaw_raw = pd.read_csv(ruta_csv, skiprows=linea_header, quotechar='"')
            df_ftaw_raw.columns = [str(c).strip().upper() for c in df_ftaw_raw.columns]
            
            col_peso = next((c for c in df_ftaw_raw.columns if 'WEIGHT' in c or 'PESO' in c or 'POND' in c), None)
            col_name = next((c for c in df_ftaw_raw.columns if 'NAME' in c or 'COMPANY' in c or 'DESCR' in c), None)
            col_ticker = next((c for c in df_ftaw_raw.columns if 'TICKER' in c or 'ASSET' in c), None)
            
            if col_peso and col_name:
                
                df_ftaw_raw[col_peso] = pd.to_numeric(
                    df_ftaw_raw[col_peso].astype(str).str.replace('%', '').str.replace('"', '').str.strip(), 
                    errors='coerce'
                ).fillna(0) / 100.0
                
                for _, r in df_ftaw_raw.iterrows():
                    t = str(r[col_ticker]).upper().strip() if col_ticker else ""
                    n = str(r[col_name]).upper().strip()
                    w = r[col_peso]
                    if t and t != 'NAN': bench_by_ticker[t] = bench_by_ticker.get(t, 0) + w
                    if n and n != 'NAN': bench_by_name[n] = bench_by_name.get(n, 0) + w
    except Exception as e:
        print(f"Nota: No se pudo cruzar el detalle del Benchmark para el Top 10 ({e}). Se mostrará solo tu portafolio.")

    
    bench_weights = []
    for idx, row in df_top10.iterrows():
        comp_clean = str(row['COMPANY_CLEAN']).upper().strip()
        tickers = [t.strip().upper() for t in str(row['ASSET_TICKER']).split('/')]
        
        w_bench = 0
        matched = False
        for t in tickers:
            t_base = t.split('.')[0]  
            if t in bench_by_ticker:
                w_bench += bench_by_ticker[t]
                matched = True
            elif t_base in bench_by_ticker:
                w_bench += bench_by_ticker[t_base]
                matched = True
                
        if not matched:
            if comp_clean in bench_by_name:
                w_bench = bench_by_name[comp_clean]
            else:
                for b_name, b_w in bench_by_name.items():
                    if comp_clean in b_name or b_name in comp_clean:
                        w_bench = b_w
                        break
        bench_weights.append(w_bench)
        
    df_top10['BENCH_WEIGHT'] = bench_weights

    
    mapeo_banderas = {
        'UNITED STATES': '🇺🇸', 'JAPAN': '🇯🇵', 'SOUTH KOREA': '🇰🇷', 'KOREA, REPUBLIC OF': '🇰🇷',
        'TAIWAN': '🇹🇼', 'TAIWAN, PROVINCE OF CHINA': '🇹🇼', 'CHINA': '🇨🇳', 'AUSTRIA': '🇦🇹',
        'NETHERLANDS': '🇳🇱', 'UNITED KINGDOM': '🇬🇧', 'AUSTRALIA': '🇦🇺', 'ITALY': '🇮🇹',
        'SWITZERLAND': '🇨🇭', 'GERMANY': '🇩🇪', 'FRANCE': '🇫🇷', 'CANADA': '🇨🇦', 'CHILE': '🇨🇱'
    }


    for idx, row in df_top10.iterrows():
        ticker_primer = str(row['ASSET_TICKER']).split('/')[0].strip()
        pais_emisor = str(row['COUNTRY']).upper().strip()
        emoji_bandera = mapeo_banderas.get(pais_emisor, '🌐')




    max_weight = max(df_top10['POND_WEIGHT'].max(), df_top10['BENCH_WEIGHT'].max())


    
    
    fig = go.Figure()

    # ── FTAW: champagne apagado (la referencia) ──
    fig.add_trace(go.Bar(
        y=df_top10['COMPANY_CLEAN'],
        x=df_top10['BENCH_WEIGHT'],
        name='FTAW',
        orientation='h',
        marker=dict(color='#56422d'),
        text=df_top10['BENCH_WEIGHT'].map(lambda x: f"{x:.2%}" if x > 0 else "0.00%"),
        textposition='outside',
        textfont=dict(size=12, color='#e8e2d4', family='Arial'),
        hovertemplate='<b>%{y}</b><br>Peso FTAW: %{x:.2%}<extra></extra>'
    ))

    # ── Nekonometrics: ORO (el protagonista) ──
    fig.add_trace(go.Bar(
        y=df_top10['COMPANY_CLEAN'],
        x=df_top10['POND_WEIGHT'],
        name='Nekonometrics',
        orientation='h',
        marker=dict(color='#f0b64b'),
        text=df_top10['POND_WEIGHT'].map(lambda x: f"{x:.2%}"),
        textposition='outside',
        textfont=dict(size=12, color='#e8e2d4', family='Arial'),
        hovertemplate='<b>%{y}</b><br>Peso Neko: %{x:.2%}<extra></extra>'
    ))


    
    fig.update_xaxes(
        showgrid=True, gridcolor='#241c14', tickformat=".2%",
        zeroline=True, zerolinecolor='#54402c', zerolinewidth=1,
        tickfont=dict(size=13, color='#a89c85')
    )
    
    fig.update_yaxes(
        showticklabels=False,
        tickfont=dict(size=14, color='#1e293b', family='Arial'),
        showgrid=False,
        type='category',
        ticklabelposition="inside",        
    )

    anotaciones_holdings = []
    for idx, row in df_top10.iterrows():
        ticker_primer = str(row['ASSET_TICKER']).split('/')[0].strip()
        pais_emisor = str(row['COUNTRY']).upper().strip()
        emoji_bandera = mapeo_banderas.get(pais_emisor, '🌐')
        nombre_clean = row['COMPANY_CLEAN']

        anotaciones_holdings.append(dict(
            x=0, y=nombre_clean,
            text=f"{emoji_bandera} <b>{nombre_clean}</b> <span style='color:#a89c85; font-size:12px;'>({ticker_primer})</span>",
            showarrow=False, xref="x", yref="y",
            xanchor="left", yanchor="bottom", yshift=14,
            font=dict(color='#e8e2d4', size=13, family='Arial')
        ))

        # ── Etiquetas fuera del área de datos ──


    peso_total_top10_yo = df_top10['POND_WEIGHT'].sum()
    peso_total_top10_bench = df_top10['BENCH_WEIGHT'].sum()

    fig.update_layout(
        title={
            'text': f'<b>Concentración en el Top 10<br>Nekonometrics: {peso_total_top10_yo:.2%} vs FTAW: {peso_total_top10_bench:.2%}</b>',
            'font': {'size': 16, 'color': '#f7f2e4', 'family': 'Arial'},
            'y': 0.96, 'x': 0.5, 'xanchor': 'center'
        },
        barmode='group', bargap=0.4, bargroupgap=0.05,
        margin=dict(l=5, r=0, t=50, b=0),
        plot_bgcolor='#17140f',
        paper_bgcolor='#17140f',
        font=dict(color='#e8e2d4'),
        annotations=anotaciones_holdings,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.10,
            xanchor="center", x=0.5,
            font=dict(size=12, color='#a89c85'),
            bgcolor='rgba(0,0,0,0)'
        ),
        hoverlabel=dict(bgcolor='#241c15', bordercolor='#f0b64b',
                        font=dict(color='#f5e6c8', size=12)),
    )

    output_html = "top_holdings.html"
    fig.write_html(output_html, include_plotlyjs="cdn")
    print(f"✅ Generado gráfico de Top Holdings Comparativo en: {output_html}")


#generar_top_holdings("data/", "data/ultimosDatos.csv")
#generar_datos_paises()
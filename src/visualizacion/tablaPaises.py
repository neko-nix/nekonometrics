import pandas as pd

MAPEO_REGIONES = {
    # 🇨🇦🇺🇸 Norteamérica
    "Bermuda": "Norteamérica", "Canada": "Norteamérica", "United States": "Norteamérica", "Cayman Islands": "Norteamérica",
    # 🇧🇷🇨🇱 Latinoamérica y Caribe
    "Brazil": "Latinoamérica", "Chile": "Latinoamérica", "Colombia": "Latinoamérica", "Mexico": "Latinoamérica", "Peru": "Latinoamérica",
    # 🇪🇺 Europa
    "Austria": "Europa", "Belgium": "Europa", "Czech Republic": "Europa", "Denmark": "Europa", "Finland": "Europa",
    "France": "Europa", "Germany": "Europa", "Greece": "Europa", "Hungary": "Europa", "Ireland": "Europa",
    "Italy": "Europa", "Netherlands": "Europa", "Norway": "Europa", "Poland": "Europa", "Portugal": "Europa",
    "Spain": "Europa", "Sweden": "Europa", "Switzerland": "Europa", "United Kingdom": "Europa",
    # 🌏 Asia-Pacífico
    "Australia": "Asia-Pacífico", "China": "Asia-Pacífico", "Hong Kong": "Asia-Pacífico", "India": "Asia-Pacífico",
    "Indonesia": "Asia-Pacífico", "Japan": "Asia-Pacífico", "Malaysia": "Asia-Pacífico", "New Zealand": "Asia-Pacífico",
    "Philippines": "Asia-Pacífico", "Singapore": "Asia-Pacífico", "South Korea": "Asia-Pacífico", "Taiwan": "Asia-Pacífico",
    "Taiwan, Province Of China": "Asia-Pacífico", "Thailand": "Asia-Pacífico",
    # 🌍 África / Medio Oriente
    "Bahrain": "África / Medio Oriente", "Egypt": "África / Medio Oriente", "Israel": "África / Medio Oriente",
    "Kuwait": "África / Medio Oriente", "Qatar": "África / Medio Oriente", "Saudi Arabia": "África / Medio Oriente",
    "South Africa": "África / Medio Oriente", "Turkey": "África / Medio Oriente", "United Arab Emirates": "África / Medio Oriente",
    # 🌐 Otros
    "Desconocido / Cash": "Otros"
}


def generar_reporte_paises(df_tabla, nombre_salida="tabla_paises.html"):
    df = df_tabla.copy()
    
    df['region'] = df['COUNTRY_CLEAN'].map(MAPEO_REGIONES).fillna('Otros')
    
    df_paises = df.groupby('COUNTRY_CLEAN').agg(
        region=('region', 'first'),
        peso_global_num=('PESO_MUESTRA', 'sum'),
        cant_empresas=('COMPANY_CLEAN', 'count')
    ).reset_index()
    

    df_lideres = df.sort_values(by='PESO_MUESTRA', ascending=False).drop_duplicates(subset=['COUNTRY_CLEAN'])
    df_lideres = df_lideres[['COUNTRY_CLEAN', 'COMPANY_CLEAN', 'PESO_MUESTRA', 'PESO_REL_MUESTRA']]
    df_lideres.columns = ['COUNTRY_CLEAN', 'top_empresa', 'top_empresa_peso_global_num', 'top_empresa_peso_pais_num']
    df_paises = pd.merge(df_paises, df_lideres, on='COUNTRY_CLEAN', how='left')
    
    df_paises['peso_region_total'] = df_paises.groupby('region')['peso_global_num'].transform('sum')
    df_paises['peso_continente_num'] = (df_paises['peso_global_num'] / df_paises['peso_region_total']) * 100

    df_paises['peso_global_str'] = df_paises['peso_global_num'].map(lambda x: f"{x:.2f}%" if x >= 0.01 else "< 0.01%")
    df_paises['peso_continente_str'] = df_paises['peso_continente_num'].map(lambda x: f"{x:.2f}%" if x >= 0.01 else "< 0.01%")
    df_paises['top_empresa_peso_global_str'] = df_paises['top_empresa_peso_global_num'].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and x >= 0.01 else ("< 0.01%" if pd.notnull(x) else "-"))
    df_paises['top_empresa_peso_pais_str'] = df_paises['top_empresa_peso_pais_num'].map(lambda x: f"{x:.2f}%" if pd.notnull(x) and x >= 0.01 else ("< 0.01%" if pd.notnull(x) else "-"))
    df_paises['top_empresa'] = df_paises['top_empresa'].fillna("-")
    

    df_json = df_paises[['COUNTRY_CLEAN', 'region', 'peso_global_num', 'peso_global_str', 'peso_continente_num', 'peso_continente_str', 'cant_empresas', 'top_empresa', 'top_empresa_peso_global_num', 'top_empresa_peso_global_str', 'top_empresa_peso_pais_num', 'top_empresa_peso_pais_str']].copy()
    df_json.columns = ['pais', 'region', 'peso_global_num', 'peso_global_str', 'peso_continente_num', 'peso_continente_str', 'cant_empresas', 'top_empresa', 'top_empresa_peso_global_num', 'top_empresa_peso_global_str', 'top_empresa_peso_pais_num', 'top_empresa_peso_pais_str']
    df_json = df_json.sort_values(by='peso_global_num', ascending=False)
    json_paises = df_json.to_json(orient='records', force_ascii=False)


    html_final = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.dataTables.min.css">
        <link rel="stylesheet" type="text/css" href="styles.css">
        <style>
            /* ── Base ── */
            body {{
                background-color: transparent !important;   /* ← NO TOCAR: va en iframe */
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 14px;
                color: #e8e2d4;
            }}

            /* ── Tabla ── */
            #tabla-paises {{
                width: 100% !important;
                margin-top: 10px !important;
                border-collapse: collapse !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            }}

            #tabla-paises thead th {{
                background-color: #1f1913 !important;
                color: #f0b64b !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                padding: 11px 12px !important;
                border-bottom: 2px solid #3d2e20 !important;
                text-align: left !important;
                background-image: none !important;   /* apaga las flechas PNG invisibles */
            }}

            #tabla-paises tbody td {{
                font-size: 14px !important;
                padding: 10px 12px !important;
                border-bottom: 1px solid #241c14 !important;
                line-height: 1.4 !important;
                color: #d8d1c2 !important;
            }}

            #tabla-paises tbody tr:nth-child(even) {{
                background-color: #14100b !important;
            }}
            #tabla-paises tbody tr:hover {{
                background-color: #2a2118 !important;
            }}

            /* ── Flechas de orden ── */
            #tabla-paises thead th.sorting::after      {{ content: " ⇅"; font-size: 10px; color: #6b5d4a; }}
            #tabla-paises thead th.sorting_asc::after  {{ content: " ▲"; font-size: 10px; color: #f0b64b; }}
            #tabla-paises thead th.sorting_desc::after {{ content: " ▼"; font-size: 10px; color: #f0b64b; }}

            /* ── Botón de columnas ── */
            .dt-button.buttons-colvis {{
                background: #1f1913 !important;
                color: #f0b64b !important;
                border: 1px solid #3d2e20 !important;
                border-radius: 6px !important;
                padding: 6px 12px !important;
                font-size: 14px !important;
                font-weight: 600 !important;
                margin-bottom: 10px !important;
            }}
            .dt-button.buttons-colvis:hover {{
                background: #2a2118 !important;
                border-color: #f0b64b !important;
            }}

            /* ── Menú desplegable del colvis (viene blanco) ── */
            .dt-button-collection {{
                background: #1f1913 !important;
                border: 1px solid #3d2e20 !important;
                border-radius: 6px !important;
            }}
            .dt-button-collection a.dt-button {{
                color: #e8e2d4 !important;
                background: transparent !important;
            }}
            .dt-button-collection a.dt-button:hover {{
                background: #2a2118 !important;
                color: #f0b64b !important;
            }}

            /* ── Buscador ── */
            .dataTables_wrapper .dataTables_filter {{ font-size: 14px !important; color: #a89c85; }}
            .dataTables_wrapper .dataTables_filter input {{
                background: #14100b !important;
                border: 1px solid #3d2e20 !important;
                border-radius: 6px !important;
                padding: 5px 10px !important;
                font-size: 14px !important;
                color: #e8e2d4 !important;
            }}
            .dataTables_wrapper .dataTables_filter input:focus {{
                border-color: #f0b64b !important;
                outline: none;
            }}
            .dataTables_wrapper .dataTables_filter input::placeholder {{ color: #6b5d4a; }}

            /* ── Textos nativos de DataTables (vienen gris oscuro) ── */
            .dataTables_wrapper .dataTables_info,
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_length label,
            .dataTables_wrapper .dataTables_filter label {{
                color: #a89c85 !important;
                font-size: 14px !important;
            }}

            .dataTables_wrapper .dataTables_length select {{
                background: #14100b !important;
                color: #e8e2d4 !important;
                border: 1px solid #3d2e20 !important;
                border-radius: 6px !important;
                padding: 4px 8px !important;
            }}

            /* ── Paginación ── */
            .dataTables_wrapper .dataTables_paginate {{ font-size: 14px !important; }}
            .dataTables_wrapper .dataTables_paginate .paginate_button {{
                color: #a89c85 !important;
                background: transparent !important;
                border: 1px solid transparent !important;
                border-radius: 6px !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button:hover {{
                background: #2a2118 !important;
                color: #f0b64b !important;
                border-color: #3d2e20 !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button.current,
            .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
                background: #f0b64b !important;
                color: #1f1710 !important;
                border: 1px solid #f0b64b !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button.disabled,
            .dataTables_wrapper .dataTables_paginate .paginate_button.disabled:hover {{
                color: #6b5d4a !important;
                background: transparent !important;
            }}
        </style>
    </head>
    <body>

        <table id="tabla-paises" class="display compact" border="0">
            <thead>
                <tr>
                    <th>País</th>
                    <th>Región / Continente</th>
                    <th>Peso Global</th>
                    <th>Peso en Región</th>
                    <th>N° Empresas</th>
                    <th>Empresa Líder</th>
                    <th>Líder (Peso Global)</th>
                    <th>Líder (Peso País)</th>
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
                    "United States": "🇺🇸", "Canada": "🇨🇦", "Mexico": "🇲🇽", "Argentina": "🇦🇷", "Brazil": "🇧🇷", "Chile": "🇨🇱", "Colombia": "🇨🇴", "Peru": "🇵🇪", "United Kingdom": "🇬🇧", "Germany": "🇩🇪", "France": "🇫🇷", "Italy": "🇮🇹", "Spain": "🇪🇸", "Netherlands": "🇳🇱", "Belgium": "🇧🇪", "Switzerland": "🇨🇭", "Austria": "🇦🇹", "Ireland": "🇮🇪", "Denmark": "🇩🇰", "Finland": "🇫🇮", "Norway": "🇳🇴", "Sweden": "🇸🇪", "Portugal": "🇵🇹", "Greece": "🇬🇷", "Poland": "🇵🇱", "Czech Republic": "🇨🇿", "Hungary": "🇭🇺", "Turkey": "🇹🇷", "Japan": "🇯🇵", "China": "🇨🇳", "South Korea": "🇰🇷", "Taiwan": "🇹🇼", "Taiwan, Province Of China": "🇹🇼", "Hong Kong": "🇭🇰", "Singapore": "🇸🇬", "Malaysia": "🇲🇾", "Indonesia": "🇮🇩", "Philippines": "🇵🇭", "Thailand": "🇹🇭", "India": "🇮🇳", "Israel": "🇮🇱", "Saudi Arabia": "🇸🇦", "United Arab Emirates": "🇦🇪", "Qatar": "🇶🇦", "Kuwait": "🇰🇼", "Bahrain": "🇧🇭", "Egypt": "🇪🇬", "Australia": "🇦🇺", "New Zealand": "🇳🇿", "South Africa": "🇿🇦", "Cayman Islands": "🇰🇾", "Bermuda": "🇧🇲"
                }};

                var datosPaises = {json_paises};

                $('#tabla-paises').DataTable({{
                    "data": datosPaises,
                    "deferRender": true,
                    "pageLength": 15,
                    "lengthMenu": [[10, 15, 25, 50, 100, -1], [10, 15, 25, 50, 100, "Todos"]],
                    "order": [[2, "desc"]], 
                    "columns": [
                        {{ "data": "pais" }},
                        {{ "data": "region" }},
                        {{ "data": "peso_global_num" }},
                        {{ "data": "peso_continente_num" }},
                        {{ "data": "cant_empresas" }},
                        {{ "data": "top_empresa" }},
                        {{ "data": "top_empresa_peso_global_num" }},
                        {{ "data": "top_empresa_peso_pais_num" }}
                    ],
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
                            "targets": [0],
                            "render": function ( data, type, row ) {{
                                if ( type === 'sort' || type === 'type' ) {{ return data; }}
                                var emoji = mapeoBanderas[data] || '🌐';
                                return emoji + " " + data;
                            }}
                        }},
                        {{
                            "targets": [2],
                            "render": function ( data, type, row ) {{ return type === 'display' ? row.peso_global_str : data; }}
                        }},
                        {{
                            "targets": [3],
                            "render": function ( data, type, row ) {{ return type === 'display' ? row.peso_continente_str : data; }}
                        }},
                        {{
                            "targets": [6],
                            "render": function ( data, type, row ) {{ return type === 'display' ? row.top_empresa_peso_global_str : data; }}
                        }},
                        {{
                            "targets": [7],
                            "render": function ( data, type, row ) {{ return type === 'display' ? row.top_empresa_peso_pais_str : data; }}
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

    with open(nombre_salida, "w", encoding="utf-8") as f:
        f.write(html_final)
        
    print(f"✅ Generada Sub-tabla de países en: {nombre_salida}!")
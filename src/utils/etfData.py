import json
import re
import html
import requests
import pandas as pd
import urllib.request
from pathlib import Path
import os
from pypdf import PdfReader

def descargarHoldings(URL_WEB, pathSave):

    print("1. Descargando el HTML de la página...")

    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    

    response = requests.get(URL_WEB, headers=HEADERS, timeout=30)
    response.raise_for_status()

    print("2. Decodificando y limpiando las secuencias de escape de JavaScript (Unicode)...")
    html_limpio = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), response.text)
    html_limpio = html_limpio.replace('\\"', '"')
    html_limpio = html.unescape(html_limpio)

    print("3. Minando bloques de datos individuales (Holdings)...")
    bloques = re.findall(r'\{[^{}]+\}', html_limpio)

    holdings_detectados = []

    for b in bloques:
        b_lower = b.lower()

        if ('ticker' in b_lower or 'symbol' in b_lower) and ('company' in b_lower or 'name' in b_lower or 'security' in b_lower):
            try:
                b_json = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', b)
                b_json = b_json.replace("'", '"')
                row_dict = json.loads(b_json)
                holdings_detectados.append(row_dict)
            except Exception:

                pares = re.findall(r'["\']?([a-zA-Z0-9_]+)["\']?\s*:\s*["\']?([^"\',}]+)["\']?', b)
                row_dict = {k.strip(): v.strip() for k, v in pares}
                if 'ticker' in row_dict or 'TICKER' in row_dict or 'symbol' in row_dict:
                    holdings_detectados.append(row_dict)

    if not holdings_detectados:
        raise ValueError(f"Error crítico: No se encontraron holdings dentro del JavaScript de {URL_WEB}")

    print(f"¡Éxito! Se detectaron {len(holdings_detectados)} registros potenciales.")

    df = pd.DataFrame(holdings_detectados)
    df.columns = [str(col).strip().upper() for col in df.columns]

    print("\n--- COLUMNAS REALES ENCONTRADAS EN EL JSON ---")
    print(df.columns.tolist())

    col_ticker = next((c for c in ['TICKER', 'SYMBOL', 'CUSIP', 'ISIN'] if c in df.columns), None)
    col_nombre = next((c for c in ['COMPANY', 'NAME', 'SECURITYNAME', 'DESCRIPTION', 'HOLDING'] if c in df.columns), None)

    subset_para_duplicados = []
    
    if col_ticker:
        df = df.dropna(subset=[col_ticker])
        subset_para_duplicados.append(col_ticker)
        
    if col_nombre:
        subset_para_duplicados.append(col_nombre)

    if subset_para_duplicados:
        df = df.drop_duplicates(subset=subset_para_duplicados, keep='first')

    df = df.rename(columns={'NAME': 'COMPANY'})

    print("\n--- VISTA PREVIA DE LOS DATOS INTERNOS EXTRAÍDOS ---")
    print(df.head())

    archivo_salida = pathSave
    df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')
    print(f"\n¡Proceso completado! Los datos se guardaron en: {archivo_salida}")


def enriquecer_ucits_con_multiples_usa(path_ucits, lista_paths_usa, path_salida):
    """
    Toma un CSV UCITS y busca los países en una LISTA de múltiples CSVs de EE.UU.
    creando una base de datos maestra de ISINs.
    """
    if not Path(path_ucits).exists():

        raise FileNotFoundError(f"Error crítico: El archivo UCITS original no existe en: {path_ucits}")

    df_ucits = pd.read_csv(path_ucits)
    df_ucits.columns = df_ucits.columns.str.strip().str.upper()
    df_ucits['ISIN'] = df_ucits['ISIN'].astype(str).str.strip().str.upper()

    lista_dfs_usa = []
    
    for path in lista_paths_usa:
        if Path(path).exists():
            df_temp = pd.read_csv(path)
            df_temp.columns = df_temp.columns.str.strip().str.upper()
            
            columnas_interes = [c for c in ['ISIN', 'COUNTRY', 'SECTOR'] if c in df_temp.columns]
            df_temp = df_temp[columnas_interes].dropna(subset=['ISIN'])
            
            df_temp['ISIN'] = df_temp['ISIN'].astype(str).str.strip().str.upper()
            lista_dfs_usa.append(df_temp)
            print(f"-> Cargado correctamente: {path} ({df_temp.shape[0]} filas)")
        else:
            print(f"-> Advertencia: Archivo no encontrado (se ignorará): {path}")

    if not lista_dfs_usa:

        raise ValueError("Error crítico: No se pudo cargar ningún archivo válido de EE.UU. para enriquecer UCITS.")

    df_usa_gigante = pd.concat(lista_dfs_usa, ignore_index=True)

    df_usa_gigante = df_usa_gigante[
        df_usa_gigante['COUNTRY'].notna() & 
        (~df_usa_gigante['COUNTRY'].astype(str).str.upper().isin(['NONE', 'NAN', '']))
    ]

    df_mapeo_maestro = df_usa_gigante.drop_duplicates(subset=['ISIN'])
    print(f" Base de datos maestra generada con {df_mapeo_maestro.shape[0]} ISINs únicos con país.")

    columnas_a_borrar = [c for c in ['COUNTRY', 'SECTOR'] if c in df_ucits.columns]
    df_ucits = df_ucits.drop(columns=columnas_a_borrar)

    df_enriquecido = pd.merge(df_ucits, df_mapeo_maestro, on='ISIN', how='left')

    df_enriquecido['COUNTRY'] = df_enriquecido['COUNTRY'].fillna('Desconocido / Cash')
    if 'SECTOR' in df_enriquecido.columns:
        df_enriquecido['SECTOR'] = df_enriquecido['SECTOR'].fillna('Otros')

    diccionario_paises_isin = {
        'KR': 'SOUTH KOREA', 'TW': 'TAIWAN', 'US': 'UNITED STATES', 
        'KY': 'CAYMAN ISLANDS', 'HK': 'HONG KONG', 'CN': 'CHINA', 
        'JP': 'JAPAN', 'GB': 'UNITED KINGDOM', 'DE': 'GERMANY', 
        'FR': 'FRANCE', 'CH': 'SWITZERLAND', 'NL': 'NETHERLANDS',
        'IN': 'INDIA', 'BR': 'BRAZIL', 'AU': 'AUSTRALIA', 'CA': 'CANADA',
        'QA': 'QATAR', 'MY': 'MALAYSIA', 'ID': 'INDONESIA',
        'SA': 'SAUDI ARABIA', 'ZA': 'SOUTH AFRICA', 'PH': 'PHILIPPINES',
        'TR': 'TURKEY', 'BM': 'BERMUDA'  
    }

    def rescatar_por_isin(row):
        if row['COUNTRY'] == 'Desconocido / Cash' or pd.isna(row['COUNTRY']):
            prefijo = str(row['ISIN'])[:2].upper()
            return diccionario_paises_isin.get(prefijo, 'Desconocido / Cash')
        return row['COUNTRY']

    df_enriquecido['COUNTRY'] = df_enriquecido.apply(rescatar_por_isin, axis=1)

    df_enriquecido.to_csv(path_salida, index=False, encoding='utf-8-sig')
    
    encontrados = df_enriquecido[df_enriquecido['COUNTRY'] != 'Desconocido / Cash'].shape[0]
    total = df_enriquecido.shape[0]

    print(f"\n¡Proceso completado! Se rescató el país para {encontrados} de {total} acciones ({encontrados/total:.1%}).")
    print(f"Archivo guardado en: {path_salida}")


def descargar_holdings_ftaw(output_path="data/ftaw_holdings.csv"):
    url_blackrock = "https://www.blackrock.com/uk/individual/products/349410/fund/1472631233320.ajax?fileType=csv&fileName=FTAW_holdings&dataType=fund"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print("Descargando holdings actualizados de FTAW (BlackRock)...")
    

    req = urllib.request.Request(
        url_blackrock, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )

    with urllib.request.urlopen(req, timeout=30) as response, open(output_path, 'wb') as out_file:
        out_file.write(response.read())
        
    print(f"¡CSV de FTAW guardado con éxito en: {output_path}!")
    return True
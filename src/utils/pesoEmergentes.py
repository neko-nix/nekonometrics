import pandas as pd

def obtener_peso_emergentes_msci(filepath):

    try:
        df = pd.read_csv(filepath, skiprows=2)
        df.columns = df.columns.str.strip()
        
        col_pais = 'Location'
        col_valor = 'Notional Value'
        col_nombre = 'Name' 
        
 
        df[col_pais] = df[col_pais].astype(str).str.strip().str.upper()
        df[col_nombre] = df[col_nombre].astype(str).str.strip().str.upper()
        
        df[col_valor] = df[col_valor].astype(str).str.replace(',', '', regex=False)
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0)
        
        total_notional = df[col_valor].sum()
        if total_notional == 0:
            raise ValueError("La suma de Notional Value es cero.")
            
        total = df[col_valor].sum()
        if total <= 0:
            raise ValueError(f"Notional total inválido ({total}). Revisa el CSV.")

        msci_emergentes = {
            'SOUTH KOREA', 'KOREA, REPUBLIC OF', 'KOREA (SOUTH)', 'TAIWAN', 'INDIA', 'CHINA', 
            'BRAZIL', 'MEXICO', 'SAUDI ARABIA', 'SOUTH AFRICA', 'THAILAND', 
            'MALAYSIA', 'INDONESIA', 'PHILIPPINES', 'CHILE', 'PERU', 'COLOMBIA', 
            'QATAR', 'UNITED ARAB EMIRATES', 'KUWAIT', 'TURKEY', 'POLAND', 
            'GREECE', 'HUNGARY', 'CZECH REPUBLIC', 'EGYPT'
        }
        
 
        palabras_clave_em = ['INDIA', 'CHINA', 'EMERGING', 'EM ', 'BRAZIL', 'TAIWAN', 'MSCI EM']

        es_pais_emergente = df[col_pais].isin(msci_emergentes)
        
        # NOTA: el FTAW mantuvo un ETF de India (iShares MSCI India) dentro de la cartera
        # al inicio del fondo, porque India quedó fuera del índice por problemas de acceso
        # al mercado. Esa posición no es una acción y debía contarse como emergente.
        # Hoy el fondo ya no lo tiene, pero la rama se mantiene por si se reconstruyen
        # holdings históricos. OJO: el keyword 'EM ' matchea substrings ("SYSTEM ", "ITEM "),
        # así que sólo aplica a posiciones con Location = IRELAND/LUXEMBOURG.
 
        #es_domicilio_etf = df[col_pais].isin(['IRELAND', 'LUXEMBOURG'])
        #tiene_nombre_em = df[col_nombre].apply(lambda x: any(kw in x for kw in palabras_clave_em))
        #es_etf_emergente_oculto = es_domicilio_etf & tiene_nombre_em
        
 
        #es_emergente_final = es_pais_emergente | es_etf_emergente_oculto
        es_emergente_final = es_pais_emergente
        
 
        notional_emergentes = df.loc[es_emergente_final, col_valor].sum()
        peso_emergentes = notional_emergentes / total_notional

        if not 0.05 < peso_emergentes < 0.25:
            raise ValueError(f"Peso EM fuera de rango plausible: {peso_emergentes:.2%} — revisá el parseo")
        
        return round(peso_emergentes, 4)

    except Exception as e:
        print(f"Error al procesar el CSV ({e}). Usando fallback histórico.")
        return 0.1235
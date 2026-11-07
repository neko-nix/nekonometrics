import sys
from pathlib import Path


from src.utils.paths import DATA_DIR 

from src.visualizacion import geografia, matriz3x3, topHoldings, rendimiento_historico, estilos

def generar_reportes_visuales():

    dir_datos = Path(DATA_DIR)
    csv_datos = dir_datos / "ultimosDatos.csv"
    ruta_style_box = "bloque_2b_style_box.html"

    if not csv_datos.exists():
        print(f"Error crítico: No se encuentra el archivo base {csv_datos}")
        sys.exit(1)


    pipeline = [
        (
            "Mapa Geográfico Global", 
            geografia.generar_mapa_global, 
            (str(dir_datos), str(csv_datos)), 
            {}
        ),
        (
            "Treemap y Análisis de Factores", 
            matriz3x3.generar_bloque_treemap_y_factores_html, 
            (str(csv_datos),), 
            {}
        ),
        (
            "Style Box (Caja de Estilos)", 
            estilos.exportar_bloque_style_box_html, 
            (str(csv_datos), str(ruta_style_box)), 
            {}
        ),
        (
            "Distribución Top Holdings", 
            topHoldings.generar_top_holdings, 
            (str(dir_datos), str(csv_datos)), 
            {}
        ),
        (
            "Dashboard de Rendimiento Histórico", 
            rendimiento_historico.generar_dashboard_premium, 
            (), 
            {}
        )
    ]

    print("\n" + "="*65)
    print(" INICIANDO GENERACIÓN DE VISUALIZACIONES DEL PORTAFOLIO")
    print("="*65)


    for nombre, funcion, args, kwargs in pipeline:
        try:
            #print(f" -> Generando {nombre:.<35}", end=" ", flush=True)
            funcion(*args, **kwargs)
            #print("OK")
        except Exception as e:

            print("FALLÓ")
            print(f"    Detalle del error en '{nombre}': {e}\n")

    print("="*65)
    print(f"Proceso finalizado.")

if __name__ == "__main__":
    generar_reportes_visuales()
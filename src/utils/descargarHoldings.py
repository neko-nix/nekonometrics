import sys 
from src.utils import etfData

print("Iniciando descarga de holdings de ETFs...")

# 1. Descarga de FTAW
try:
    print("Descargando holdings de FTAW...")
    etfData.descargar_holdings_ftaw()
    print("FTAW completado con éxito.")
except Exception as e:
    print(f"Error crítico al descargar FTAW: {e}")
    sys.exit(1)

urlsEEUU = [
        #["https://www.avantisinvestors.com/avantis-investments/total-holdings/808/?type=etf", "data/All holdings_808.csv"], # AVES Emerging Value
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/824/?type=etf", "data/All holdings_824.csv"], # AVEE Emerging Small Cap
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/118/?type=etf", "data/All holdings_118.csv"], # AVEM Emerging Markets
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/116/?type=etf", "data/All holdings_116.csv"], # AVDE International Equity
        #["https://www.avantisinvestors.com/avantis-investments/total-holdings/807/?type=etf", "data/All holdings_807.csv"], # AVIV International Value
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/120/?type=etf", "data/All holdings_120.csv"], # AVDV International Small Cap Value
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/114/?type=etf", "data/All holdings_114.csv"], # AVUS US Equity
        #["https://www.avantisinvestors.com/avantis-investments/total-holdings/806/?type=etf", "data/All holdings_806.csv"], # AVLV US Value
        ["https://www.avantisinvestors.com/avantis-investments/total-holdings/119/?type=etf", "data/All holdings_119.csv"]  # AVUV US Small Cap Value
]

urlsUCITS = [
    ["https://www.avantisinvestors.com/ucitsetf/total-holdings/20910451307042/?type=ucitsetf",  "data/All holdings_avem.csv"], # AVEM Emerging Equity
    #["https://www.avantisinvestors.com/ucitsetf/total-holdings/339814050701062/?type=ucitsetf", "data/All holdings_aveu.csv"], # AVEU Europe Equity
    ["https://www.avantisinvestors.com/ucitsetf/total-holdings/840303451307042/?type=ucitsetf", "data/All holdings_avgc.csv"], # AVWC Global Equity
    ["https://www.avantisinvestors.com/ucitsetf/total-holdings/295032351307042/?type=ucitsetf", "data/All holdings_avgs.csv"], # AVWS Global Small Cap Value
    #["https://www.avantisinvestors.com/ucitsetf/total-holdings/167749050701062/?type=ucitsetf", "data/All holdings_avpe.csv"], # AVPE Pacific Equity
    #["https://www.avantisinvestors.com/ucitsetf/total-holdings/574426540701062/?type=ucitsetf", "data/All holdings_avus.csv"]  # AVUS America Equity
]


mis_archivos_usa = [
    #"data/All holdings_808.csv",
    "data/All holdings_824.csv",
    "data/All holdings_118.csv", 
    "data/All holdings_116.csv",
    #"data/All holdings_807.csv",
    "data/All holdings_120.csv",
    "data/All holdings_114.csv",
    #"data/All holdings_806.csv",
    "data/All holdings_119.csv"
]


print("\nIniciando descarga de holdings de EE.UU...")
for linkUrl, pathSave in urlsEEUU:
    nombre_archivo = pathSave.split("/")[-1]
    try:
        print(f"   -> Descargando {nombre_archivo}...")
        etfData.descargarHoldings(linkUrl, pathSave)
    except Exception as e:
        print(f"Error crítico al descargar holdings de EE.UU. ({nombre_archivo}): {e}")
        sys.exit(1) 


print("\nIniciando descarga y enriquecimiento de holdings UCITS...")
for linkUrl, pathSave in urlsUCITS:
    nombre_archivo = pathSave.split("/")[-1]
    try:
        print(f"   -> Descargando {nombre_archivo}...")
        etfData.descargarHoldings(linkUrl, pathSave)
        
        print(f"   -> Enriqueciendo {nombre_archivo} con datos de EE.UU...")
        etfData.enriquecer_ucits_con_multiples_usa(pathSave, mis_archivos_usa, pathSave)
    except Exception as e:
        print(f"Error crítico en flujo UCITS ({nombre_archivo}): {e}")
        sys.exit(1)

print("\n¡Sincronización y enriquecimiento de holdings completado con éxito!")
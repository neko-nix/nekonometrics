# metrics.py
from pathlib import Path
import pandas as pd

COSTO_BENCH = 0.07
DICCIONARIO_COSTOS = {"AVGC.L": 0.22, "AVGS.L": 0.39, "AVEM.L": 0.35}

MAPEO_ACTIVOS = {
    "AVGC.L": ("Desarrollados", "Core / Blend"),
    "AVGS.L": ("Desarrollados", "Small Cap Value"),
    "AVEM.L": ("Emergentes", "Core / Blend"),
}

def calcular_contexto(csv_path, costo_bench=COSTO_BENCH):
    """ÚNICA fuente de verdad para costo, desvío y fondos.
    Devuelve un dict. No escribe archivos. No tiene estado."""
    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el CSV de composición: {p}")

    df = pd.read_csv(p)
    df.columns = df.columns.str.strip().str.upper()

    col_ticker = next((c for c in df.columns if "TICKER" in c), None)
    col_prop   = next((c for c in df.columns if "PROPORCIONACTUAL" in c or "PESO" in c), None)
    if not col_ticker or not col_prop:
        raise ValueError(f"Faltan columnas. Hay: {list(df.columns)}")

    def _num(serie):
        s = pd.to_numeric(
            serie.astype(str).str.replace("%", "", regex=False).str.strip(),
            errors="coerce",
        ).fillna(0.0)
        return s * 100 if s.max() <= 1.0 else s

    df["PESO"] = _num(df[col_prop])
    df["TICKER"] = df[col_ticker].astype(str).str.strip().str.upper()

    # ⚠️ TER: si falta un ticker, esto AVISA en vez de asumir 0
    faltantes = sorted(set(df["TICKER"]) - set(DICCIONARIO_COSTOS))
    if faltantes:
        raise KeyError(
            f"Falta TER para {faltantes}. Agregalos a DICCIONARIO_COSTOS "
            f"(si no, el costo ponderado sale ARTIFICIALMENTE BAJO)."
        )
    df["TER"] = df["TICKER"].map(DICCIONARIO_COSTOS)

    peso_total = df["PESO"].sum()
    costo = (df["TER"] * df["PESO"]).sum() / peso_total if peso_total else 0.0

    # Objetivo
    col_ideal = next((c for c in df.columns if "IDEAL" in c), None)
    if col_ideal:
        df["OBJETIVO"] = _num(df[col_ideal])
        df["DIF"] = df["PESO"] - df["OBJETIVO"]
        idx_max = df["DIF"].abs().idxmax()
        desvio_max_pp = float(df.loc[idx_max, "DIF"])
        desvio_ticker = df.loc[idx_max, "TICKER"]
    else:
        df["OBJETIVO"] = None
        df["DIF"] = None
        desvio_max_pp = None
        desvio_ticker = None

    return {
        "costo": {
            "nekonometrics": round(float(costo), 4),
            "bench":         round(float(costo_bench), 4),
            "lastre":        round(float(costo - costo_bench), 4),
        },
        "desvio": {
            "max_pp":  None if desvio_max_pp is None else round(desvio_max_pp, 2),
            "ticker":  desvio_ticker,
        },
        "fondos": [
            {
                "ticker":   r["TICKER"],
                "peso":     round(float(r["PESO"]), 2),
                "ter":      float(r["TER"]),
                "objetivo": None if r["OBJETIVO"] is None else round(float(r["OBJETIVO"]), 2),
                "dif":      None if r["DIF"] is None else round(float(r["DIF"]), 2),
            }
            for _, r in df.iterrows()
        ],
    }
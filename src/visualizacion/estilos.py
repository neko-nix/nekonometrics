import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ══════════════════════════════════════════════════════
#  1. TEMA  (una sola vez, sin duplicados) ✅
# ══════════════════════════════════════════════════════
FONDO      = "#0f0d0a"
SUP        = "#17140f"
SUP2       = "#1f1b14"
BORDE      = "#2a2018"
TEXTO      = "#e8e2d4"
FUERTE     = "#f7f2e4"
MUTED      = "#a89c85"
FAINT      = "#8a8070"
ORO        = "#f0b64b"
ORO_DIM    = "#c89a45"
ORO_BRIGHT = "#ffd280"


# ══════════════════════════════════════════════════════
#  2. DATOS
# ══════════════════════════════════════════════════════
MATRICES_ORIGINALES = {
    "BENCHMARK": np.array([[0, 0, 0], [5, 7, 4], [22, 36, 25]]),
    "AVEM":      np.array([[3, 3, 2], [8, 4, 5], [20, 21, 30]]),
    "AVGS":      np.array([[45, 28, 10], [7, 7, 3], [0, 0, 0]]),
    "AVGC":      np.array([[5, 6, 2], [9, 11, 6], [17, 26, 16]]),
}

MAPEO_ETFS = {
    "AVGS": MATRICES_ORIGINALES["AVGS"],
    "AVGC": MATRICES_ORIGINALES["AVGC"],
    "AVEM": MATRICES_ORIGINALES["AVEM"],
}

ESTILOS = ["Value", "Blend", "Growth"]
TAMANOS = ["Small", "Mid", "Large"]
GAMMA   = 0.65


# ══════════════════════════════════════════════════════
#  3. RAMPA DE COLOR  (módulo, no dentro de la función) ✅
# ══════════════════════════════════════════════════════
COLORSCALE_ORO = [
    [0.00, "#17120d"],
    [0.16, "#241c14"],
    [0.32, "#33271b"],
    [0.46, "#4a3826"],
    [0.60, "#7f6040"],
    [0.66, "#a8906f"],
    [0.82, "#cfa869"],
    [1.00, "#f2cb7d"],
]

COLORSCALE_GRIS = [
    [0.00, "#17120d"],
    [0.22, "#26221c"],
    [0.42, "#3a352d"],
    [0.60, "#5a5247"],
    [0.66, "#8a7f6c"],
    [0.82, "#ab9f8a"],
    [1.00, "#c4b8a2"],
]


# ══════════════════════════════════════════════════════
#  4. HELPERS  (arriba, cerrados, sin código después del return) ✅
# ══════════════════════════════════════════════════════
def _curva(m, zmax):
    return (np.clip(m, 0, zmax) / zmax) ** GAMMA


def _figura_matriz_html(matriz, global_max, colorscale, titulo,
                        umbral=0.63, incluir_js=False):
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        x=ESTILOS, y=TAMANOS,
        z=_curva(matriz, global_max),
        customdata=matriz,
        colorscale=colorscale,
        showscale=False,
        zmin=0, zmax=1,
        xgap=3, ygap=3,
        hovertemplate=(
            f"{titulo} · %{{y}} %{{x}}: "
            "<b>%{customdata:.1f}%</b><extra></extra>"
        ),
    ))

    for i, tam in enumerate(TAMANOS):
        for j, est in enumerate(ESTILOS):
            v   = matriz[i][j]
            pos = (max(float(v), 0.0) / global_max) ** GAMMA
            fig.add_annotation(
                x=est, y=tam,
                text=f"<b>{v:.1f}%</b>",
                showarrow=False,
                font=dict(
                    size=14, family="'Segoe UI',Arial,sans-serif",
                    color=("#1f1710" if pos > umbral else "#f7f2e4"),
                ),
            )

    fig.update_layout(
        title=dict(
            text=f"<b>{titulo}</b>",
            x=0.5, xanchor="center", y=0.88, yanchor="top",
            font=dict(size=14, color=FUERTE),
        ),
        paper_bgcolor=SUP,
        plot_bgcolor=SUP,
        height=350,
        margin=dict(l=48, r=8, t=82, b=8),
        showlegend=False,
        hovermode="closest",
        font=dict(family="'Segoe UI',Arial,sans-serif", color=TEXTO),
        hoverlabel=dict(
            bgcolor=SUP2, bordercolor=ORO,
            font=dict(color="#f5e6c8", size=12),
        ),
    )

    fig.update_xaxes(
        side="top",
        tickfont=dict(size=11, color=ORO_DIM),
        fixedrange=True, showgrid=False, zeroline=False,
        linecolor=BORDE,
    )
    fig.update_yaxes(
        tickfont=dict(size=11, color=MUTED),
        fixedrange=True, showgrid=False, zeroline=False,
    )

    return fig.to_html(
        include_plotlyjs=("cdn" if incluir_js else False),
        full_html=False,
        config={"displayModeBar": False, "responsive": True},
    )


def _tarjetas_kpi_html(mp, mb):
    port_small = mp[0].sum(); port_mid = mp[1].sum(); port_large = mp[2].sum()
    bench_small = mb[0].sum(); bench_mid = mb[1].sum(); bench_large = mb[2].sum()

    port_value = mp[:, 0].sum(); port_blend = mp[:, 1].sum(); port_growth = mp[:, 2].sum()
    bench_value = mb[:, 0].sum(); bench_blend = mb[:, 1].sum(); bench_growth = mb[:, 2].sum()

    def fila(nombre, v_port, v_bench, destacado=False):
        color_nombre = ORO if destacado else MUTED
        peso         = "700" if destacado else "400"
        color_val    = "#ffffff" if destacado else FUERTE

        return f"""
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; font-size:13px;">
                        <span style="color:{color_nombre}; font-weight:{peso};">{nombre}</span>
                        <span style="font-weight:700; color:{color_val};">{v_port:.1f}%
                            <span style="font-weight:400; color:{FAINT}; font-size:11px;">
                                vs {v_bench:.1f}%</span></span>
                    </div>"""

    def tarjeta(titulo, filas):
        return f"""
            <div style="background:{SUP2}; border:1px solid {BORDE};
                        border-radius:10px; padding:13px 15px; display:flex;
                        flex-direction:column; justify-content:space-between; gap:10px;">
                <div style="font-size:13px; font-weight:700; letter-spacing:1.4px;
                            text-transform:uppercase; color:{ORO_DIM};
                            border-bottom:1px solid {BORDE}; padding-bottom:6px;">
                    {titulo}</div>
                {filas}
            </div>"""

    estilo = tarjeta("Sesgo por Estilo", "".join([
        fila("Value ★", port_value, bench_value, destacado=True),
        fila("Blend", port_blend, bench_blend),
        fila("Growth", port_growth, bench_growth),
    ]))

    tamano = tarjeta("Sesgo por Tamaño", "".join([
        fila("Large", port_large, bench_large),
        fila("Mid", port_mid, bench_mid),
        fila("Small ★", port_small, bench_small, destacado=True),
    ]))

    return estilo + tamano


# ══════════════════════════════════════════════════════
#  5. FUNCIÓN PRINCIPAL  (solo orquesta, no define nada) ✅
# ══════════════════════════════════════════════════════
def exportar_bloque_style_box_html(ruta_csv, ruta_salida_html="bloque_2b_style_box.html") -> str:

    df = pd.read_csv(ruta_csv)
    df["ticker_clean"] = (
        df["ticker"].str.replace(r"\.L$", "", regex=True).str.strip().str.upper()
    )

    df_filtrado = df[df["ticker_clean"].isin(MAPEO_ETFS)].copy()   # ← .copy() 🚩
    if df_filtrado.empty:
        raise ValueError("Error: No se encontraron tickers válidos de Avantis en el CSV.")

    total = df_filtrado["proporcionActual"].sum()
    df_filtrado["peso_relativo"] = df_filtrado["proporcionActual"] / total

    matriz_portafolio = np.zeros((3, 3))
    for _, row in df_filtrado.iterrows():
        matriz_portafolio += MAPEO_ETFS[row["ticker_clean"]] * row["peso_relativo"]

    matriz_bench = MATRICES_ORIGINALES["BENCHMARK"] * (
        100.0 / MATRICES_ORIGINALES["BENCHMARK"].sum()
    )

    # ── Escala COMPARTIDA: los dos paneles comparables ✅ ──
    global_max = float(max(matriz_portafolio.max(), matriz_bench.max())) or 1.0

    html_port = _figura_matriz_html(
        matriz_portafolio, global_max, COLORSCALE_ORO, "Nekonometrics",
        incluir_js=True,
    )
    html_bench = _figura_matriz_html(
        matriz_bench, global_max, COLORSCALE_GRIS, "FTAW",
        incluir_js=False,
    )

    html_kpis = _tarjetas_kpi_html(matriz_portafolio, matriz_bench)

    html_final = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}

  html, body {{
      margin: 0; padding: 0;
      background: {SUP};
      color: {TEXTO};               /* ← esto faltaba ✅ */
      font-family: 'Segoe UI', Arial, sans-serif;
      overflow-x: hidden;
  }}

  .bloque-2b-stylebox {{ width: 100%; padding: 0 4px 4px 4px; }}

  .matrices-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
      gap: 4px;
      margin-bottom: 10px;
  }}
  .matrices-row > div {{ min-width: 0; }}

  .kpis-row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(150px, 100%), 1fr));
      gap: 12px;
  }}
</style>
</head>

<body>
  <div class="bloque-2b-stylebox">
      <div class="matrices-row">
          {html_port}
          {html_bench}
      </div>
      <div class="kpis-row">
          {html_kpis}
      </div>
  </div>

  <script>
  (function () {{
    /* ── Mide y reajusta SOLO si el ancho del contenedor cambió ──
       Guard por-div: un resize no cambia el ancho del padre,
       así que el observer no se auto-dispara ✅               */
    function sync() {{
      if (!window.Plotly) return;

      var divs = document.querySelectorAll('.plotly-graph-div');  /* ← lazy ✅ */
      for (var i = 0; i < divs.length; i++) {{
        var gd = divs[i];
        if (!gd || !gd.data) continue;                            /* ← sin plot todavía ⏭️ */

        var w = gd.parentElement ? gd.parentElement.clientWidth
                                 : gd.clientWidth;
        if (w <= 0) continue;                                     /* ← iframe oculto ⏭️ */

        if (gd._lastW !== w) {{                                    /* ← solo si cambió ✅ */
          gd._lastW = w;
          try {{ Plotly.Plots.resize(gd); }} catch (e) {{}}
        }}
      }}
    }}

    /* Arranque escalonado: el grid del padre puede tardar en resolver */
    function boot() {{
      sync();
      requestAnimationFrame(sync);
      [60, 150, 300, 600, 1200].forEach(function (ms) {{ setTimeout(sync, ms); }});
    }}

    if (document.readyState === 'complete') boot();
    else window.addEventListener('load', boot);

    if (document.readyState === 'loading')
      document.addEventListener('DOMContentLoaded', sync);
    else sync();

    /* Observer sobre las CELDAS DEL GRID, no sobre el body ✅ */
    if (window.ResizeObserver) {{
      var ro = new ResizeObserver(sync);
      var celdas = document.querySelectorAll('.matrices-row > div');
      for (var j = 0; j < celdas.length; j++) ro.observe(celdas[j]);
    }}

    window.addEventListener('resize', sync);
  }})();
  </script>
</body>
</html>
"""

    if ruta_salida_html:
        with open(ruta_salida_html, "w", encoding="utf-8") as f:
            f.write(html_final)
        print(f"✅ Generado Style Box y tarjetas KPIs de factores en: {ruta_salida_html}")

    return html_final
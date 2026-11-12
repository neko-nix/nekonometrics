# Nekonometrics 🐱📈

![Python](https://img.shields.io/badge/python-3.12+-orange?logo=python&logoColor=white)
![NixOS](https://img.shields.io/badge/NixOS-blue?logo=nixos&logoColor=white&color=5277C3)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?logo=sqlite&logoColor=white)
![Version](https://img.shields.io/badge/version-0.1-brightgreen)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

![GitHub last commit](https://img.shields.io/github/last-commit/neko-nix/nekonometrics)
![GitHub Issues](https://img.shields.io/github/issues/neko-nix/nekonometrics)

**¿Vale la pena la inversión factorial en el mundo real, con todos los costos, comisiones y complejidad extra, frente a un fondo global cap-weighted como el FTAW?** Este repo intenta responder esa pregunta con números en vez de opiniones.

Experimento personal: tres ETFs UCITS domiciliados en Irlanda de Avantis contra el FTSE All-World (`FTAW`) como benchmark. Los cálculos son automáticos, las ejecuciones son manuales. Todo el código y los datos son públicos, incluidas las limitaciones.

📑 **Reporte diario:** [neko-nix.github.io/nekonometrics](https://neko-nix.github.io/nekonometrics/)

📚 **Documentación:** [documentacion](/docs/documentation.md), decisiones, limitaciones y cómo ejecutarlo

> **Esto no es asesoría financiera ni publicidad de ninguna administradora.** Es el registro público de un experimento propio, con fines educativos. Los números son reales, la estrategia es mía y las decisiones son tuyas. Invertir tiene riesgo real de perder capital.

---

## 💼 La cartera

Renta variable global con sesgo a factores documentados (Value, Size y Profitability), horizonte de largo plazo y sin renta fija.

| Ticker | Qué es | Rol |
| --- | --- | --- |
| [`AVGC`](https://www.avantisinvestors.com/ucitsetf/avantis-global-equity-ucits-etf/) | Avantis Global Equity (desarrollados, core blend) | 50% del bloque DM |
| [`AVGS`](https://www.avantisinvestors.com/ucitsetf/avantis-global-small-cap-value-ucits-etf/) | Avantis Global Small Cap Value (desarrollados) | 50% del bloque DM |
| [`AVEM`](https://www.avantisinvestors.com/ucitsetf/avantis-emerging-markets-equity-ucits-etf/) | Avantis Emerging Equity (emergentes, core blend) | 100% del bloque EM |

Los pesos no son fijos: la proporción desarrollados/emergentes se recalcula en cada ejecución a partir de los holdings del benchmark (`FTAW`), clasificando cada país como DM o EM con la metodología del MSCI ACWI, la misma que usa Avantis para definir sus fondos. Al 2026-11-10 los pesos aproximados son 44% / 44% / 12%: una foto, no un objetivo.

El 50/50 entre `AVGC` y `AVGS` **no** es una réplica del índice, es una decisión propia: es lo que duplica la exposición a Size y Value respecto de una cartera cap-weighted, y es la decisión activa central de la estrategia.

**Por qué Avantis:** sesgo explícito a valor, tamaño y rentabilidad, sin selección de acciones individuales.

**Por qué una sola administradora:** con un solo proveedor, si el tilt no rinde, la causa es el factor. Con dos, nunca se sabe si el problema fue el premio de factores o la implementación.

## 🛠️ Qué hace

**Cartera**
- Registra cada compra en SQLite: fecha, precio de ejecución, cantidad y comisión.
- Calcula la proporción objetivo y los montos necesarios para rebalancear, siempre con aportes nuevos (admite aportes en cero, para ver el estado actual).
- Descarga (scraping) los holdings de cada ETF y del benchmark, y los usa de base para el análisis de la cartera (geografía, sectores, Active Share, overlap).
- Mide exposición a divisas, asignación actual y su desviación del peso objetivo, distribución geográfica (mapa y tabla de países) y la lista completa de holdings.

**Análisis contra `FTAW`**
- Rentabilidad acumulada en USD, CLP y UF, y CAGR en USD.
- Retorno ponderado por dinero (MWR) de los aportes reales contra el fondo espejo, y la brecha activa acumulada.
- Costo ponderado, matriz de estilo de inversión, top 10 posiciones y concentración, sectores industriales, Active Share y overlap de capital y de posición.

**Infraestructura**
- Entorno reproducible con [Nix flakes](/flake.nix).
- SQLite con cache de indicadores y de precios macro.
- Los gráficos se recalculan desde la tabla de transacciones, así que una compra registrada retroactivamente también se refleja.

## 🚫 Qué no hace (a propósito)

- **No vende.** Nunca. El rebalanceo se hace únicamente con aportes nuevos.
- **No hace market timing** ni trading frecuente.
- **No selecciona acciones individuales** ni usa apalancamiento o derivados.
- **No proyecta ni backtestea retornos futuros,** y no predice si el premio de factores va a persistir.
- **No es automático:** las corridas son manuales y hay que respetar la ventana horaria, de 19:00 a 02:00 hora de Chile (ver [documentacion](/docs/documentation.md)).
- **No está pensado para que lo uses.** Es un pipeline personal.

> La comparación es de **retorno y TER**, no de retorno neto de spread, comisión de broker, impuestos y tiempo de mantenimiento. El benchmark es un fondo espejo, hay un solo camino de aportes, la ventana es corta y el Active Share es una estimación, no un valor exacto. Este repo mide la diferencia; **no mide si vas a aguantarla.** Las limitaciones están documentadas, no escondidas.

## ⏳ Todavía no

*Fuera de alcance hoy, pero podría entrar más adelante.*

- 🧾 Retornos después de impuestos.
- 💱 Descomposición del retorno entre variación de precio y efecto divisa.
- 📉 Retornos ajustados por riesgo (volatilidad, drawdown).
- 🔍 Rendimiento de cada ETF por separado (los holdings de cada uno sí se descargan, pero no se mide su retorno individual).
- 📈 CAGR en CLP y en UF (hoy sólo en USD).

## 🖥️ Cómo ejecutar

Ver [documentacion](/docs/documentation.md).

## ⚖️ Licencia

GNU AFFERO GENERAL PUBLIC LICENSE V3. Ver [LICENSE](LICENSE).
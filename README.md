# Neko-Money 🐱💸

![Python](https://img.shields.io/badge/python-3.12+-orange?logo=python&logoColor=white) 
![NixOS](https://img.shields.io/badge/NixOS-blue?logo=nixos&logoColor=white&color=5277C3)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?logo=sqlite&logoColor=white)
![Version](https://img.shields.io/badge/version-0.1-brightgreen)
[![License: AGPL v3](https://img.shields.io/badge/license-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/neko-nix/nekonometrics)
![GitHub last commit](https://img.shields.io/github/last-commit/neko-nix/nekonometrics)
![GitHub Issues](https://img.shields.io/github/issues/neko-nix/nekonometrics)



> **⚠️ Descargo de Responsabilidad:** Este proyecto es de carácter estrictamente educativo, personal y experimental. Ningún dato, gráfico o texto aquí expuesto constituye una recomendación de compra, asesoría financiera personalizada o invitación a operar en los mercados. El autor no asume ninguna responsabilidad ante posibles pérdidas financieras, decisiones de inversión de terceros o colocación de capital en cualquier tipo de activo. Invertir conlleva riesgos reales de pérdida de capital; realice siempre su propio análisis técnico y legal.

Sistema de gestión de inversiones automático, con fuertes sesgos a factores y eficiencia tributaria al usar ETFs UCITS domiciliados en Irlanda. Utilizando las APIs de [yfinance](https://ranaroussi.github.io/yfinance/index.html), [Mindicador.cl](https://mindicador.cl/) y SQLite, optimizado para el mercado chileno y desarrollado sobre NixOS.

📑 **Reporte diario:** [https://neko-nix.github.io/nekonometrics/](https://neko-nix.github.io/nekonometrics/)

---

## 🛠️ Funciones Actuales
- ✍️ **Gestión de Movimientos:** Registro en SQLite de compras, ventas y comisiones de cada transacción en USD, y cálculo automático de equivalentes en CLP y UF.
- 📈 **Eficiencia Tributaria:** Al usar ETFs UCITS de acumulación domiciliados en Irlanda, se evitan generar eventos tributarios por pago de dividendos, permitiendo que el interés compuesto siga trabajando ininterrumpido. 
- ❄️ **Entorno Nix:** Ambiente de desarrollo reproducible mediante [flake.nix](/flake.nix) sin tener que depender de documentos tipo `requierements.txt`.
- 💹 **Sesgo a Factores:** Con sólo 3 tickers de Avantis, se consiguen fuertes sesgos hacia factores de valor, tamaño y rentabilidad, capturando así una prima de riesgo extra manteniendo una estructura simple y fácil de implementar.
- ⚖️ **Rebalanceo Automático:** Calcula automáticamente la proporción óptima para cada activo, además de las transacciones necesarias para conseguir el estado de equilibrio.
- 💲 **Valor Actual de Inversión:** Cálculo de multiplicador de riqueza, tanto en USD, como en sus equivalentes de CLP y UF.
- 📊 **Análisis Visual:** Reporte visual con distintos gráficos actualizado todos los días.
- 🪞 **Comparación con Mercado General:** Diferencia entre el CAGR obtenido con la estrategia de factores vs lo que hubiera rentado invetir todo en el iShares FTSE All World UCITS ETF.
- 🔎 **Análisis de Componentes:** Scrapping de los componentes internos de cada ETF, y generar un análisis detallado de las posiciones y geografía del portafolio.
- 📈 **Históricos:** Guardar datos históricos del portafolio, para poder hacer análisis en el tiempo.


## ⏳ Funciones Planeadas
- 📚 **Documentación de Estrategia de Inversión**: Documentar y explicar la estrategia de inversión.
- 🔮 **Proyecciones:** Implementar distintos tipos de proyecciones para el portafolio.
- 🔔 **Notificaciones Telegram:** Enviar resúmenes diarios, semanales, mensuales y/o anuales del comportamiento del portafolio.



## ❄️ Entorno en Nix Flakes
Para activar el entorno de desarrollo, descargando e instalando todas sus dependencias, se requiere utilizar Nix Flakes, y ejecutar el siguiente comando estando en el directorio del proyecto:
```sh
nix develop
```


## ⚖️ Licencia
Este proyecto está bajo la licencia GNU AFFERO GENERAL PUBLIC LICENSE V3. Consulta el archivo [LICENSE](LICENSE) para más detalles.
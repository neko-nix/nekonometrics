# Nekonometrics

**¿Vale la pena la inversión factorial en el mundo real, con todos los costos, comisiones y complejidad extra, frente a un fondo global cap-weighted como el FTAW?**

Este repo intenta responder esa pregunta con números en vez de opiniones.

## La pregunta

Hoy un inversor minorista puede comprar un ETF global cap-weighted (tipo FTSE All-World) con un TER cercano a 0.1% y una sola orden.

La alternativa es armar una cartera multifactor: varios ETFs, rebalanceo periódico, más comisiones, más fricción, y un tracking error enorme durante años.

El premio de los factores Value, Size y Profitability está documentado en la literatura. **La pregunta es si ese premio sobrevive a la fricción real:** TER, spread, comisiones de broker, impuestos, rebalanceo, y sobre todo la capacidad psicológica de sostener la diferencia.

Este repo mide la diferencia. **No mide si vas a aguantarla.**

Tampoco mide todavía la fricción completa: la comparación es de **retorno y TER**, no de retorno neto de spread, comisión de broker, impuestos y tiempo de mantenimiento.



## La estrategia

Renta variable global con sesgo a factores documentados (Value, Size, Profitability), horizonte de largo plazo, sin renta fija.

| Ticker | Nombre | Región | Tipo | Pesos dinámicos | Pesos aproximados*|
| --- | --- | --- | --- | --- | --- |
| [AVGC](https://www.avantisinvestors.com/ucitsetf/avantis-global-equity-ucits-etf/) | Avantis Global Equity | Desarrollados | Core Blend | 50% de Desarrollados | 44% |
| [AVGS](https://www.avantisinvestors.com/ucitsetf/avantis-global-small-cap-value-ucits-etf/) | Avantis Global Small Cap Value | Desarrollados | Small Cap Value | 50% de Desarrollados | 44%
| [AVEM](https://www.avantisinvestors.com/ucitsetf/avantis-emerging-markets-equity-ucits-etf/) | Avantis Emerging Equity | Emergentes | Core Blend | 100% de Emergentes| 12% |

*Pesos al 2026-11-10. Cambian con cada rebalanceo: los porcentajes de esta tabla son una foto, no un objetivo fijo.*

### Condiciones para que funcione

1. **Horizonte de al menos 30 años.** El interés compuesto necesita espacio.
2. **Tolerancia al riesgo extrema.** La volatilidad se lee como oportunidad de compra.
3. **Broker con comisiones bajas.** Idealmente ≤0,5% por operación.
4. **Rebalanceo automatizado.** Con un script o una tabla: la fricción de mantener varios tickers balanceados a mano es real.



## Cómo se calculan los pesos dinámicos

Los pesos **no son fijos**. La proporción Desarrollados / Emergentes se recalcula tomando como referencia la composición del **MSCI ACWI**:

1. Se leen los holdings del FTAW (FTSE All-World).
2. Se clasifica cada país como DM o EM según la metodología **MSCI ACWI**.
3. Se suman los pesos de los países EM como `pesoEmergentes`.
4. Se calculan los pesos de países DM como `1 - pesoEmergentes`.



### Dos decisiones que hay que conocer

**1. Clasificación MSCI sobre un universo FTSE.** El universo de holdings es FTSE, pero la clasificación DM/EM usada es la de MSCI ACWI, porque Avantis define sus fondos con esa metodología y conviene alinearlas con el producto. La discrepancia principal es **Corea** (MSCI: Emergente, FTSE: Desarrollado) y en menor medida **Polonia**. En la práctica, Corea (~2% del ACWI) se cuenta como emergente acá.

**2. El 50/50 entre AVGC y AVGS es una decisión propia, no una réplica.** El índice no dice "mitad core, mitad small cap value". Ese 50/50 es lo que duplica la exposición a Size y Value respecto de una cartera cap-weighted. Es la decisión activa central de la estrategia.

## Qué mide el repo
Detalle completo en [la página del proyecto](https://neko-nix.github.io/nekonometrics/).
 
### De la cartera en sí:
- **Exposición a divisas** (moneda de los flujos, no de cotización).
- **Asignación actual de activos** y su desviación del peso objetivo.
- **Distribución geográfica** tanto en formato visual (mapa) como una tabla con todos los países a los que se tiene exposición.
- **Lista completa de holdings** de la cartera, desglosado por posición, y por peso ponderado dentro de la cartera y por peso relativo al país emisor.

### En comparación con FTAW:
- **Rentabilidad acumulada** en USD, CLP y UF.
- **Retorno ponderado por dinero (MWR)** de los aportes reales contra el fondo espejo,
  y la brecha activa acumulada.
- **CAGR en USD.**
- **Costo ponderado** de la cartera.
- **Matriz de estilo de inversión.**
- **Top 10 posiciones** y concentración.
- **Sectores industriales.**
- **Active Share**.
- **Overlap de capital**, a nivel de capital y de posición.

## Qué no hace todavía
*Fuera de alcance hoy, pero podría entrar más adelante.*

- No modela retornos después de impuestos.
- No descompone el retorno entre variación de precio y efecto divisa   (cuánto subió el activo en sí vs cuánto aportó o restó el tipo de cambio).
- No ajusta retornos por riesgo (volatilidad, drawdown).
- No analiza cada ETF por separado.
- No calcula CAGR en CLP ni en UF, sólo en USD.

## Qué no va a hacer nunca

- **No genera órdenes de venta.** El rebalanceo se hace únicamente con aportes nuevos.
- **No hace market timing** ni trading frecuente.
- **No selecciona acciones individuales.**
- **No usa apalancamiento ni derivados.**
- **No backtestea retornos esperados** ni proyecta rendimientos futuros.
- **No predice si el premio de factores va a persistir.**

*Y no es una recomendación de inversión ni publicidad de ninguna administradora, ver [Aviso](#aviso).*

## Limitaciones

### De los datos

- **Hay dos llaves de unión distintas, y no son igual de robustas.**
  - **Enriquecimiento de país y sector -> ISIN.** Sólido: elimina los problemas de formato (`BRK.B` vs `BRK/B`) y los sufijos de exchange.
  - **Comparación contra el benchmark -> TICKER.** El CSV de iShares no incluye ISIN, así que el cruce cae al ticker. Ahí vuelven los problemas de formato, los sufijos
    de exchange, las clases de acción distintas del mismo emisor y el más silencioso **tickers que existen en dos mercados para empresas distintas**: el ticker no es único globalmente, así que puede perder matches reales y generar matches falsos.
  - **Dirección del error:** un nombre compartido que no hace match aporta `0,5·(w+b)` en vez de `0,5·|w−b|`, o sea que **suma** puntos de Active Share inexistentes. El active share calculado actualmente es una estimación, no un valor exacto.
- **`COUNTRY` se usa como llave** en la clasificación DM/EM, así que variantes de nombre (`KOREA` vs `SOUTH KOREA` vs `KOREA (SOUTH)`) harían desaparecer un país del cálculo sin error. Ya ocurrió con Corea. El código ahora reporta cualquier país que no esté en el mapa de clasificación.
- **País de origen ≠ país de operación.** Hay holdings con país desconocido, o inscritos en paraísos fiscales sin operar ahí (el fallback por prefijo de ISIN devuelve  domicilio, no exposición económica).

### De los resultados


- **El benchmark es un fondo espejo:** sin spread, sin comisión, sin precio de ejecución.
- **Un solo camino:** una secuencia de aportes, sin intervalos de confianza ni escenarios alternativos de aportes.
- **La ventana es corta.** Los factores pueden pasar una década sin pagar. Un período favorable o desfavorable no cierra la pregunta.
- **El costo extra no está monetizado.** El mayor mantenimiento (tres ETFs, rebalanceos) se reconoce cualitativamente pero no se traduce a un número. La comparación es de retorno esperado, **no de retorno menos esfuerzo**.

## Protocolo para ETFs futuros

Tres reglas gobiernan cualquier cambio en la cartera:

1. **Los cambios se hacen con aportes, nunca con ventas.** El sistema no genera órdenes de venta.
2. **Una sola administradora y una sola metodología.** Menos variables que confundan el diagnóstico.
3. **Más ETFs no es más exposición factorial.** Cada fondo nuevo diluye el efecto de los demás.

### Emergentes

Hoy el bloque de Emergentes es **100% AVEM (core)**, porque Avantis no publica versión UCITS de EM value ni de EM small cap. En EE.UU. existen AVEE (EM value) y AVES (EM small blend), pero **no un EM small cap value específico**, así que es posible que esa versión nunca llegue a UCITS.

#### Orden de prioridad

Cuando haya más de un producto disponible, el orden es siempre el mismo:

1. **Mantener la proporción Desarrollados / Emergentes.** Esa es la regla que manda.
2. **Dentro de Emergentes, mantener el balance entre los dos bloques (core + factor)**.
3. **Sólo si sobra espacio en Emergentes**, aportar a los ETFs de factor adicionales.

#### Los dos bloques


El bloque de Emergentes aspira a **50% core / 50% small**, igual que Desarrollados. Pero el objetivo del bloque small **depende de la calidad del instrumento disponible**, no sólo de que exista:

| Instrumento del bloque small | Objetivo del bloque small | Por qué |
| --- | --- | --- |
| **EM SCV específico** | 50% | es el instrumento correcto: size + value |
| **Sólo EM small blend** | máximo 25% | aporta tamaño, pero arrastra small growth |
| **Ninguno** | 0% | 100% core |

**Por qué small blend no llega al 50% cuando hay alternativas.** El premio del segmento small se concentra en small **value**. Small blend incluye small growth, el peor cuadrante histórico de la matriz de estilo, empresas de baja rentabilidad y alta inversión, las llamadas "zombies". Los filtros de Avantis deberían excluir a buena parte de ellas, pero el filtro **mitiga, no elimina**. Por eso small blend se usa como complemento acotado y no como núcleo del bloque.

**La excepción.** Si small blend es el único factor de Emergentes disponible, va al 50%, no porque sea mejor, sino porque es lo único que hay. La asignación se adapta al instrumento, no al revés.

**Los bloques son el objetivo, los ETFs son los instrumentos disponibles para acercarse.**

#### Escenarios

| Escenario | Productos UCITS disponibles | Cómo se aporta |
| --- | --- | --- |
| Hoy | sólo core | 100% core |
| Un solo factor | core + value **o** core + small | 50% core + 50% factor |
| Value y small por separado | core + value + small | 50% core + 25% value + 25% small |
| SCV específico (llega después) | core + value + small + SCV | al bloque que esté bajo 50%, **sin pasarse** |

**Efecto del escenario intermedio:** con 50% core + 25% value + 25% small blend, el bloque small queda en 25% en vez de 50%, y el bloque core+value en 75%. O sea: durante ese período la cartera está **menos sesgada a tamaño** de lo que aspira, a cambio de no sobrecargar un proxy imperfecto. Es un compromiso deliberado, no un error de asignación. Además en este escenario, el bloque core+value queda sobreponderado respecto del 50% objetivo, y como EM value tiene sesgo a large, el bloque completo queda transitoriamente más inclinado hacia empresas grandes de lo que aspira la estructura final.

**Cómo funciona el último escenario.** Los aportes nuevos van a core y SCV, pero se cortan cuando el bloque correspondiente llega al 50%. Si small blend + SCV ya suma 50% del bloque de Emergentes, no entra más dinero a SCV aunque SCV esté "bajo" respecto del core: quien está bien posicionado es el bloque, no el producto.

**Nunca se vende.** Las posiciones de value y small blend dejan de recibir aportes y se diluyen con el tiempo.

*Consecuencias conocidas:* cuanto más tarde llegue un SCV específico, mayor será el legado de value y small blend y más lento su decaimiento. Y ante cualquier conflicto, **primero se respeta la proporción DM/EM**; el balance interno de Emergentes es secundario.

**El escenario ideal es el más simple:** que Avantis publique un EM SCV en UCITS sin pasar antes por value ni small blend. Evita todo el problema del legado diluido y permite que el bloque de Emergentes replique la estructura de Desarrollados desde el primer día. Pero eso depende de Avantis, no de nosotros.

### Otros factores

Avantis tiene en EE.UU. ETFs específicos de mid cap value, large cap value, mid core blend, entre otros. **No se van a usar**, por dos razones:

- **Redundancia.** Los ETFs Core ya cubren todo el espectro de tamaños. Sobreponderar mid o large no agrega exposición factorial: agrega concentración en un corte de
  capitalización que el core ya contiene.
- **Dilución.** Cada ETF adicional reduce el peso relativo de los demás dentro de la cartera.   El tilt total no crece, se reparte entre más productos.

La cartera queda entonces en dos piezas: **Core** (large, mid y small) y **Small Cap Value**.

**Única excepción:** un ETF que combine Desarrollados y Emergentes en un solo fondo. Simplificaría la cartera de tres ETFs a dos, a cambio de cederle a Avantis la decisión de cuánto peso darle a cada región.

### Otras administradoras

Existen alternativas dedicadas a factores, como Dimensional Fund Advisors (DFA). Aún así, la cartera se mantiene **íntegramente en Avantis**, por una razón de diagnóstico:

>Con un solo proveedor, si el tilt no rinde, la causa es el factor. Con dos, nunca se sabe si el problema fue el premio de factores o la implementación de una administradora.

La consistencia metodológica vale más que la diversificación de proveedores.



## Aviso

Nada en este repositorio ni la página web deben ser considerados como una recomendación de inversión ni asesoría financiera. No es publicidad de Avantis, BlackRock ni de ninguna otra administradora. Es el registro público de un experimento propio, con fines educativos.

## Cómo ejecutarlo

Mejor no lo hagas, confía. Este código está pensado para uso personal, no para que terceros lo prueben. Si aun así quieres intentarlo, es bajo tu propia responsabilidad.

### Requisitos

- `nix` con flakes habilitados
- `git`

### Primera vez, en este orden (el orden NO es opcional)

```bash
git clone https://github.com/neko-nix/nekonometrics
cd nekonometrics
nix develop
python -m src.database.crearDB
```

`crearDB` genera `nekoMoney.db` con las tres tablas necesarias (`cache_indicadores`, `cache_macro_precios`, `transacciones`). Se puede re-ejecutar sin riesgo: no borra nada.

Después registra tu primera transacción:

```bash
python -m scripts.registrarMovimiento
```

Es interactivo. El script te dará sugerencias entreparéntesis para cada valor, se aceptan presionando `enter`, o se puede ingresar manualmente si el dato no corresponde. Lo ideal es verificar directamente con tu broker el precio de ejecucción, la cantidad de acciones compradas y las comisiones pagadas. La base **rechaza** cualquier fecha que no esté en formato `YYYY-MM-DD`, así que si el script falla, corrige la fecha y vuelve a correrlo: no se guarda nada a medias.

### Actualizar datos

Ejecuta esto **fuera de horario de bolsa**. La ventana recomendada es de **19:00 a 02:00 (hora de Chile)**.

```bash
python -m src.utils.datosMercado
python -m src.utils.descargarHoldings
python -m src.core.rebalancear
python -m src.core.generarGraficos
```

El motivo de la ventana: los ETFs cotizan en Europa y el cierre europeo cae a media mañana en Chile. Si bajas datos durante la sesión podés traerte precios intradía, y no va a haber ninguna alerta que te avise. 

`rebalancear` acepta aportes en cero: sirve para calcular los valores actuales y ver cómo está el portafolio sin aportar nada.

### Publicar la página

La rama `pages` contiene el `index`, el CSS y los HTML que **no** se regeneran automáticamente. Descarga **todos** los archivos de esa rama y déjalos en un directorio aparte.

Después, aún dentro del directorio de `nekonometrics`:

```bash
python -m src.core.generarGraficos
```

Copia los HTML generados y reemplaza con ellos los que descargaste de `pages`.



### Notas

- `registrarMovimiento` funciona a cualquier hora; no depende de la bolsa.
- Los gráficos y análisis se recalculan desde la tabla `transacciones`, así que una transacción agregada retroactivamente (con fecha anterior a la última) también se   refleja.
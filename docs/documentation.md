# Estrategia de Inversión: Global Equity con Sesgo de Factores
La estrategia se basa en la acumulación agresiva de renta variable global con sesgo hacia factores de riesgo documentados (Value, Size, Profitability), con el objetivo de obtener el mayor crecimiento posible a largo plazo, para esto, se van a utilizar 6 ETFs administrados por [Avantis Investors](https://www.avantisinvestors.com/home/).

## Consideraciones:
Para que esta estrategia funcione, se deben cumplir las siguientes condiciones:

1. Horizonte temporal de al menos 30 años: Para que el interés compuesto tenga el espacio para crecer con fuerza.
2. Tolerancia al Riesgo Extrema: El inversionista debe percibir la volatilidad como una oportunidad de compra, no como riesgo de pérdida.
3. Broker con Comisiones Bajas: Se debe tener acceso a un broker, que además de ofrecer los ETFs necesarios, debe cobrar pocas comisiones, idealmente 0.5% del monto a operar o menos.
4. Cálculos de Rebalanceo Automático: Ya sea con un script en Python o una tabla en Excel, porque de otra forma, la fricción de operar y mantener balanceados varios tickers distintos se vuelve complejo.


## Composición del Portafolio:


| Ticker                                                                                       | Nombre                         | Región        | Tipo            | Proporción |
| -------------------------------------------------------------------------------------------- | ------------------------------ | ------------- | --------------- | ---------- |
| [AVWC](https://www.avantisinvestors.com/ucitsetf/avantis-global-equity-ucits-etf/)           | Avantis Global Equity          | Desarrollados | Core Blend      | 44%         |
| [AVWS](https://www.avantisinvestors.com/ucitsetf/avantis-global-small-cap-value-ucits-etf/)  | Avantis Global Small Cap Value | Desarrollados | Small Cap Value | 44%      |
| [AVEM](https://www.avantisinvestors.com/ucitsetf/avantis-emerging-markets-equity-ucits-etf/) | Avantis Emerging Equity        | Emergentes    | Core Blend      | 12%        |


# Este script es para agregar nuevas compras en la cartera de inversión

import sqlite3
from datetime import datetime, timedelta
import yfinance as yf
import requests
from src.utils.paths import DB_PATH
from src.utils import conversiones



def leer_dato(prompt, tipo_esperado=float, opciones=None, sugerencia=None):
    while True:

        entrada = input(prompt).strip()

        if entrada == "" and sugerencia is not None:
            return sugerencia
        
        if opciones:
            entrada = entrada.upper()
            if entrada in opciones:
                return entrada
            print(f"Error. Opciones válidas: {', '.join(opciones)}")
            continue

        try:
            valor = tipo_esperado(entrada.replace(",", "."))
            if valor < 0:
                print("El valor debe ser mayor a 0")
                continue
            return valor
        except ValueError:
            nombre_tipo = "entero" if tipo_esperado == int else "decimal"
            print(f"'{entrada}' no es un número {nombre_tipo} válido.")




TICKERS_VALIDOS = ["AVGC.L", "AVGS.L", "AVEM.L"]


OPCIONES_VALIDAS = ["COMPRA", "VENTA"]

print("AVGC.L = Global Equity")
print("AVGS.L = Global Small Cap Value")
print("AVEM.L = Emerging Markets Equity")



ticker   = leer_dato(f"Ticker ({', '.join(TICKERS_VALIDOS)}): ", opciones=TICKERS_VALIDOS)




tipo     = leer_dato("¿Compra o Venta?: ", opciones=OPCIONES_VALIDAS)
fecha    = input(f"Fecha AAAA-MM-DD ({datetime.now().date()}): ") or str(datetime.now().date())
cantidad = leer_dato("Cantidad de Acciones: ", tipo_esperado=float)
precioUSD   = leer_dato("Precio unitario (USD): ", tipo_esperado=float)
totalUSD = cantidad * precioUSD
if tipo == "VENTA":
    cantidad *= -1


print("Consultando precio de FTAW...")
ultimoVWCE = yf.Ticker("FTAW.AS")
dfVWCE = ultimoVWCE.history(start=fecha, period="5d")
valorFTAW = dfVWCE['Close'].iloc[0]



valorFTAW   = leer_dato(f"Precio FTAW (${valorFTAW:.2f}): ", tipo_esperado=float, sugerencia=valorFTAW)
cantidadFTAW = totalUSD / valorFTAW



# Obtener el valor del USDo mercado
valorUSD = None

print(f"Consultando Dólar Observado para la fecha {fecha}...")

dolarHistorico = yf.Ticker("CLP=X")

hist = dolarHistorico.history(start=fecha, period="5d")    
if not hist.empty:
    valorUSD = round(hist.iloc[0]['Close'], 2)
else:
    print(f"No hay datos disponibles para la fecha {fecha}. Ingrese el valor manualmente.")

#print(hist)

mensajeDolar = f"Valor Dólar ({valorUSD}): " if valorUSD else "Valor Dólar: "
dolarMercado = leer_dato(mensajeDolar, tipo_esperado=float, sugerencia=valorUSD)

# Obtener el valor de la UF
fechaUF = datetime.strptime(fecha, "%Y-%m-%d").strftime("%d-%m-%Y")
url = f"https://mindicador.cl/api/uf/{fechaUF}"
print(f"Consultado valor UF para la fecha {fecha}...")
response = requests.get(url, timeout=50)
data = response.json()
if "serie" in data and len(data["serie"]) > 0:
    valorUF = float(data["serie"][0]["valor"])
else:
    print(f"No hay datos disponibles para la fecha {fecha}. Ingrese el valor manualmente.")

mensajeUF = f"Valor UF ({valorUF})" if valorUF else "Valor UF: "
uf = leer_dato(f"{mensajeUF}: ", tipo_esperado=float, sugerencia=valorUF)


comisión_fx = 0.55/100

comisión_fx_usd = totalUSD/(1-comisión_fx) - totalUSD
comisión_fx_clp = comisión_fx_usd*dolarMercado
comisión_fx_uf  = comisión_fx_clp/uf

comisión_corretaje_usd = 1.7
comisión_viaje_usd = 1.13
comisión_corretaje_clp = comisión_corretaje_usd*dolarMercado
comisión_corretaje_uf = comisión_corretaje_clp/uf

comisión_total_usd = comisión_fx_usd + comisión_corretaje_usd + comisión_viaje_usd
comisión_total_clp = comisión_total_usd * dolarMercado
comisión_total_uf = comisión_total_clp/uf



print(f"Comisión estimada por cambio de divisa: ${comisión_fx_usd:.2f} USD, ${comisión_fx_clp:.2f} CLP")
print(f"Comisión estimada por corretaje: ${comisión_corretaje_usd:.2f} USD, ${comisión_corretaje_clp:.2f} CLP")
print(f"Comisión relativa al total: {comisión_total_usd/totalUSD:.2%}")

comisionUSD = leer_dato(f"Comisión total USD (${comisión_total_usd:,.2f}): ", tipo_esperado=float, sugerencia=comisión_total_usd)



# uf = 39716.32
# print(f"Valor Uf: {uf}")

# Valores equivalentes:

comisionCLP = comisionUSD*dolarMercado
comisionUF = comisionCLP/uf

precioCLP   = precioUSD*dolarMercado
precioUF   = precioCLP/uf

totalCLP = totalUSD*dolarMercado
totalUF  = totalCLP/uf




print(f"\n{'='*40}")
print("Se han registrado los siguientes datos:")
print(f"{'='*40}")
print(f"Ticker: {ticker}")
print(f"Tipo: {tipo}")
print(f"Fecha: {fecha}")
print(f"Cantidad: {cantidad:,.2f}")

print(f"Precio por acción (USD): ${precioUSD:,.2f}")
print(f"Comisión (USD): ${comisionUSD:,.2f}")
print(f"Total Invertido (USD): ${totalUSD:,.2f}")

print(f"{'-'*40}")
print("Equivalente en Pesos Chilenos")
print(f"{'-'*40}")

print(f"Valor USD: ${dolarMercado:,.2f}")
print(f"Precio por acción (CLP): ${precioCLP:,.0f}")
print(f"Comisión (CLP): ${comisionCLP:,.0f}")
print(f"Total Invertido (CLP): ${totalCLP:,.0f}")

print(f"{'-'*40}")
print("Equivalente en Unidad de Fomento")
print(f"{'-'*40}")

print(f"Valor UF: $ {uf:,.2f}")
print(f"Precio por acción: UF {precioUF:,.2f}")
print(f"Comisión: UF {comisionUF:,.2f}")
print(f"Total Invertido: UF {totalUF:,.2f}")



print(f"{'-'*40}")
print("Equivalente en iShares FTSE All World UCITS ETF (FTAW)")
print(f"{'-'*40}")

print(f"Precio por Acción: ${valorFTAW:,.2f}")
print(f"Cantidad Acciones: {cantidadFTAW:,.2f}")


print(f"{'='*40}")



# Guardar los datos en el .db

confirmar = input("\n¿Guardar este movimiento en la base de datos? (s/n): ").lower()

if confirmar == 's':
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        query = """
        INSERT INTO transacciones (
            ticker, tipo, fecha, cantidad,

            precio_ejecucion_usd, comision_usd, total_usd,

            valor_USD, precio_ejecucion_clp, comision_clp, total_clp,

            valor_uf, precio_ejecucion_uf, comision_uf, total_uf,

            valor_ftaw, cantidad_ftaw
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        datos = (
            ticker, tipo.lower(), fecha, cantidad,
            precioUSD, comisionUSD, totalUSD,
            dolarMercado, precioCLP, comisionCLP, totalCLP,
            uf, precioUF, comisionUF, totalUF,
            valorFTAW, cantidadFTAW
        )

        cursor.execute(query, datos)
        ultimoIngresado = cursor.lastrowid     
        conn.commit()        

        cursor.execute("SELECT * FROM transacciones WHERE id = ?", (ultimoIngresado,))
        f = cursor.fetchone()  
        columnas = [descripcion[0] for descripcion in cursor.description]
        conn.close()

        if f:
            print(f"\n{'='*40}")
            print(f"\nEl siguiente movimiento ha sido registrado en nekoMoney.db (ID: {f[0]})")
            print(f"{'='*40}")
            
            for i in range(len(columnas)):
                valor = f[i]
                if isinstance(valor, float):
                    valor_espaciado = f"{valor:,.2f}".replace(",", " ")
                    if "clp" in columnas[i]:                        
                        print(f"{columnas[i]:<25}: CLP {valor_espaciado:>13}")
                    elif "USD" in columnas[i]:
                        print(f"{columnas[i]:<25}: USD {valor_espaciado:>13}")
                    elif "valorFTAW" in columnas[i]:
                        print(f"{columnas[i]:<25}: USD {valor_espaciado:>13}")
                    elif "uf" in columnas[i]:
                        print(f"{columnas[i]:<25}: UF {valor_espaciado:>14}")
                    elif "cantidad" in columnas[i]:
                        print(f"{columnas[i]:<25}: {valor_espaciado:>17}")
                else:
                    print(f"{columnas[i]:<25}: {valor:>17}")            
            print(f"{'='*40}")
        

    except Exception as e:
        print(f"\nError al guardar en la base de datos: {e}")
else:
    print("\nRegistro cancelado.")
import requests


class FrankfurterProvider:

    BASE_URL = "https://api.frankfurter.dev/v2"
    MONEDAS_FINANCEOS = ("COP", "EUR", "GBP", "JPY", "BRL", "MXN", "CAD", "AUD")

    def obtener_tasas(self, base="USD"):

        try:

            cotizaciones = ",".join(moneda for moneda in self.MONEDAS_FINANCEOS if moneda != base.upper())
            respuesta = requests.get(
                f"{self.BASE_URL}/rates",
                params={"base": base.upper(), "quotes": cotizaciones},
                timeout=10,
            )

            respuesta.raise_for_status()

            datos = respuesta.json()
            if not isinstance(datos, list):
                return {}
            return {
                registro["quote"]: float(registro["rate"])
                for registro in datos
                if registro.get("quote") and registro.get("rate") is not None
            }

        except (requests.RequestException, ValueError, TypeError, KeyError):
            return {}

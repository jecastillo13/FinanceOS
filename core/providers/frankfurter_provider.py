import requests


class FrankfurterProvider:

    BASE_URL = "https://api.frankfurter.app"

    def obtener_tasas(self, base="USD"):

        try:

            respuesta = requests.get(
                f"{self.BASE_URL}/latest?from={base}",
                timeout=10
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

            return datos.get("rates", {})

        except Exception as e:

            print("Error Frankfurter:", e)

            return {}
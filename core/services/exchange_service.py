from datetime import datetime

from core.database import get_session
from core.models import TasaCambio
from core.providers import FrankfurterProvider


class ExchangeService:

    def __init__(self):

        self.db = get_session()

        self.provider = FrankfurterProvider()

    # =====================================================
    # ACTUALIZAR TASAS
    # =====================================================

    def actualizar_tasas(
        self,
        moneda_base="USD"
    ):

        tasas = self.provider.obtener_tasas(
            moneda_base
        )

        if not tasas:

            return False

        print("\n================================")
        print("Tasas descargadas")
        print("================================")
        print(tasas)
        print("================================\n")

        for moneda_destino, tasa in tasas.items():

            registro = (
                self.db.query(TasaCambio)
                .filter(
                    TasaCambio.moneda_origen == moneda_base,
                    TasaCambio.moneda_destino == moneda_destino
                )
                .first()
            )

            if registro:

                registro.tasa = tasa
                registro.fecha_actualizacion = datetime.now()

            else:

                registro = TasaCambio(

                    moneda_origen=moneda_base,

                    moneda_destino=moneda_destino,

                    tasa=tasa,

                    fuente="Frankfurter",

                    fecha_actualizacion=datetime.now()

                )

                self.db.add(registro)

        self.db.commit()

        return True

    # =====================================================
    # COMPATIBILIDAD
    # =====================================================

    def actualizar_usd_cop(self):

        ok = self.actualizar_tasas(
            "USD"
        )

        if not ok:

            return None

        return self.obtener_tasa(
            "USD",
            "COP"
        )

    # =====================================================
    # OBTENER TASA
    # =====================================================

    def obtener_tasa(
        self,
        origen,
        destino
    ):

        origen = origen.upper()
        destino = destino.upper()

        if origen == destino:

            return 1.0

        registro = (

            self.db.query(TasaCambio)

            .filter(

                TasaCambio.moneda_origen == origen,

                TasaCambio.moneda_destino == destino

            )

            .first()

        )

        if registro:

            return registro.tasa

        registro = (

            self.db.query(TasaCambio)

            .filter(

                TasaCambio.moneda_origen == destino,

                TasaCambio.moneda_destino == origen

            )

            .first()

        )

        if registro:

            return 1 / registro.tasa

        # Frankfurter guarda las tasas con USD como base. Con esas dos tasas
        # podemos convertir entre cualquier par de monedas disponible.
        tasa_usd_origen = self._tasa_desde_usd(origen)
        tasa_usd_destino = self._tasa_desde_usd(destino)

        if tasa_usd_origen is not None and tasa_usd_destino is not None:
            return tasa_usd_destino / tasa_usd_origen

        return None

    def _tasa_desde_usd(self, moneda):
        if moneda == "USD":
            return 1.0

        registro = (
            self.db.query(TasaCambio)
            .filter(
                TasaCambio.moneda_origen == "USD",
                TasaCambio.moneda_destino == moneda,
            )
            .first()
        )
        return registro.tasa if registro else None

    # =====================================================
    # CONVERTIR
    # =====================================================

    def convertir(
        self,
        valor,
        origen,
        destino
    ):

        tasa = self.obtener_tasa(
            origen,
            destino
        )

        if tasa is None:

            return None

        return round(
            valor * tasa,
            2
        )

    # =====================================================
    # TODAS LAS TASAS
    # =====================================================

    def obtener_tasas(self):

        return (

            self.db.query(TasaCambio)

            .order_by(

                TasaCambio.moneda_origen,

                TasaCambio.moneda_destino

            )

            .all()

        )

    # =====================================================
    # ÚLTIMA ACTUALIZACIÓN
    # =====================================================

    def ultima_actualizacion(self):

        registro = (

            self.db.query(TasaCambio)

            .order_by(

                TasaCambio.fecha_actualizacion.desc()

            )

            .first()

        )

        if registro:

            return registro.fecha_actualizacion

        return None

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.db.close()

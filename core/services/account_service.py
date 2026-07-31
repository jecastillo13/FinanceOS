from core.database import get_session
from core.models import Cuenta
from core.services.exchange_service import ExchangeService


class AccountService:

    def __init__(self):
        self.db = get_session()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def obtener_cuentas(self):
        return (
            self.db.query(Cuenta)
            .order_by(Cuenta.nombre)
            .all()
        )

    def obtener_cuenta(self, cuenta_id):
        return self.db.get(Cuenta, cuenta_id)

    def total_cuentas(self):
        return self.db.query(Cuenta).count()

    def saldo_total(self):

        cuentas = self.obtener_cuentas()

        exchange = ExchangeService()

        total = 0

        for cuenta in cuentas:

            # Si la cuenta ya está en COP
            if cuenta.moneda.upper() == "COP":
                total += cuenta.saldo

            else:

                convertido = exchange.convertir(
                    cuenta.saldo,
                    cuenta.moneda.upper(),
                    "COP"
                )

                # Si no existe una tasa, usa el saldo original
                if convertido is None:
                    convertido = cuenta.saldo

                total += convertido

        exchange.cerrar()

        return round(total, 2)

    # =====================================================
    # CRUD
    # =====================================================

    def crear_cuenta(
        self,
        nombre,
        tipo,
        saldo,
        moneda="COP",
        color="#2563EB",
        icono="🏦"
    ):

        cuenta = Cuenta(
            nombre=nombre,
            tipo=tipo,
            saldo=saldo,
            moneda=moneda.upper(),
            color=color,
            icono=icono
        )

        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)

        return cuenta

    def actualizar_cuenta(
        self,
        cuenta_id,
        nombre,
        tipo,
        saldo,
        moneda,
        color,
        icono
    ):

        cuenta = self.db.get(Cuenta, cuenta_id)

        if cuenta is None:
            return None

        cuenta.nombre = nombre
        cuenta.tipo = tipo
        cuenta.saldo = saldo
        cuenta.moneda = moneda.upper()
        cuenta.color = color
        cuenta.icono = icono

        self.db.commit()
        self.db.refresh(cuenta)

        return cuenta

    def eliminar_cuenta(self, cuenta_id):

        cuenta = self.db.get(Cuenta, cuenta_id)

        if cuenta is None:
            return False

        # Evita borrar accidentalmente el historial financiero asociado.
        if cuenta.movimientos:
            return False

        self.db.delete(cuenta)
        self.db.commit()
        return True

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.db.close()

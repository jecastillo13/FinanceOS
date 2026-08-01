from core.database import get_session
from core.models import Cuenta
from core.services.exchange_service import ExchangeService


class AccountService:
    def __init__(self):
        self.db = get_session()

    def obtener_cuentas(self):
        return self.db.query(Cuenta).order_by(Cuenta.nombre).all()

    def obtener_cuenta(self, cuenta_id):
        return self.db.get(Cuenta, cuenta_id)

    def total_cuentas(self):
        return self.db.query(Cuenta).count()

    def saldos_consolidados(self, moneda_base="COP"):
        """Devuelve saldos convertidos y cuentas que no tienen tasa disponible."""
        exchange = ExchangeService()
        datos, pendientes = [], []
        try:
            for cuenta in self.obtener_cuentas():
                convertido = exchange.convertir(cuenta.saldo, cuenta.moneda, moneda_base)
                if convertido is None:
                    pendientes.append(cuenta)
                    continue
                datos.append({"cuenta": cuenta, "saldo_base": convertido, "moneda_base": moneda_base})
        finally:
            exchange.cerrar()
        return datos, pendientes

    def saldo_total(self, moneda_base="COP"):
        datos, _ = self.saldos_consolidados(moneda_base)
        return round(sum(dato["saldo_base"] for dato in datos), 2)

    def crear_cuenta(self, nombre, tipo, saldo, moneda="COP", color="#2563EB", icono="🏦"):
        cuenta = Cuenta(nombre=nombre, tipo=tipo, saldo=saldo, moneda=moneda.upper(), color=color, icono=icono)
        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def actualizar_cuenta(self, cuenta_id, nombre, tipo, saldo, moneda, color, icono):
        cuenta = self.db.get(Cuenta, cuenta_id)
        if cuenta is None:
            return None
        if cuenta.movimientos and (saldo != cuenta.saldo or moneda.upper() != cuenta.moneda.upper()):
            raise ValueError("No puedes cambiar el saldo ni la moneda de una cuenta con movimientos. Registra un ajuste como movimiento.")
        cuenta.nombre, cuenta.tipo, cuenta.saldo = nombre, tipo, saldo
        cuenta.moneda, cuenta.color, cuenta.icono = moneda.upper(), color, icono
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def eliminar_cuenta(self, cuenta_id):
        cuenta = self.db.get(Cuenta, cuenta_id)
        if cuenta is None or cuenta.movimientos:
            return False
        self.db.delete(cuenta)
        self.db.commit()
        return True

    def cerrar(self):
        self.db.close()

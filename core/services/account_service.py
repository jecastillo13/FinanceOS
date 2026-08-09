from core.database import get_session
from core.models import Cuenta
from core.services.audit_service import registrar_auditoria
from core.services.validation import moneda_valida, texto_requerido
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

    def saldos_consolidados(self, moneda_base="COP", exchange=None):
        """Devuelve saldos convertidos y cuentas que no tienen tasa disponible."""
        servicio_tasas = exchange or ExchangeService()
        datos, pendientes = [], []
        try:
            for cuenta in self.obtener_cuentas():
                convertido = servicio_tasas.convertir(cuenta.saldo, cuenta.moneda, moneda_base)
                if convertido is None:
                    pendientes.append(cuenta)
                    continue
                datos.append({"cuenta": cuenta, "saldo_base": convertido, "moneda_base": moneda_base})
        finally:
            if exchange is None:
                servicio_tasas.cerrar()
        return datos, pendientes

    def saldo_total(self, moneda_base="COP", exchange=None):
        datos, _ = self.saldos_consolidados(moneda_base, exchange)
        return round(sum(dato["saldo_base"] for dato in datos), 2)

    def crear_cuenta(self, nombre, tipo, saldo, moneda="COP", color="#2563EB", icono="🏦"):
        nombre = texto_requerido(nombre, "El nombre de la cuenta", 100)
        tipo = texto_requerido(tipo, "El tipo de cuenta", 50)
        moneda = moneda_valida(moneda)
        cuenta = Cuenta(nombre=nombre, tipo=tipo, saldo=float(saldo), moneda=moneda, color=color, icono=icono)
        self.db.add(cuenta)
        registrar_auditoria(self.db, "CUENTA_CREADA", f"Cuenta creada: {nombre} ({moneda.upper()}).")
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def actualizar_cuenta(self, cuenta_id, nombre, tipo, saldo, moneda, color, icono):
        cuenta = self.db.get(Cuenta, cuenta_id)
        if cuenta is None:
            return None
        nombre = texto_requerido(nombre, "El nombre de la cuenta", 100)
        tipo = texto_requerido(tipo, "El tipo de cuenta", 50)
        moneda = moneda_valida(moneda)
        saldo = float(saldo)
        if cuenta.movimientos and (saldo != cuenta.saldo or moneda != cuenta.moneda.upper()):
            raise ValueError("No puedes cambiar el saldo ni la moneda de una cuenta con movimientos. Registra un ajuste como movimiento.")
        cuenta.nombre, cuenta.tipo, cuenta.saldo = nombre, tipo, saldo
        cuenta.moneda, cuenta.color, cuenta.icono = moneda, color, icono
        registrar_auditoria(self.db, "CUENTA_ACTUALIZADA", f"Cuenta #{cuenta.id} actualizada: {nombre} ({moneda}).")
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def eliminar_cuenta(self, cuenta_id):
        cuenta = self.db.get(Cuenta, cuenta_id)
        if cuenta is None or cuenta.movimientos or cuenta.tarjetas:
            return False
        registrar_auditoria(self.db, "CUENTA_ELIMINADA", f"Cuenta #{cuenta.id} eliminada: {cuenta.nombre}.")
        self.db.delete(cuenta)
        self.db.commit()
        return True

    def cerrar(self):
        self.db.close()

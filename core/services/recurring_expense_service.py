from calendar import monthrange
from datetime import date, timedelta

from core.database import get_session
from core.models import Categoria, Cuenta, GastoRecurrente, Movimiento


class RecurringExpenseService:
    def __init__(self):
        self.db = get_session()

    def obtener_gastos(self, incluir_inactivos=False):
        consulta = self.db.query(GastoRecurrente)
        if not incluir_inactivos:
            consulta = consulta.filter(GastoRecurrente.activo == 1)
        return consulta.order_by(GastoRecurrente.proxima_fecha_pago, GastoRecurrente.nombre).all()

    def crear_gasto(self, nombre, valor, frecuencia, proxima_fecha_pago, categoria_id):
        self._validar_categoria_gasto(categoria_id)
        gasto = GastoRecurrente(
            nombre=nombre.strip(),
            valor=abs(float(valor)),
            frecuencia=frecuencia,
            proxima_fecha_pago=proxima_fecha_pago,
            categoria_id=categoria_id,
        )
        self.db.add(gasto)
        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def actualizar_gasto(self, gasto_id, nombre, valor, frecuencia, proxima_fecha_pago, categoria_id, activo):
        gasto = self.db.get(GastoRecurrente, gasto_id)
        if gasto is None:
            return None

        self._validar_categoria_gasto(categoria_id)
        gasto.nombre = nombre.strip()
        gasto.valor = abs(float(valor))
        gasto.frecuencia = frecuencia
        gasto.proxima_fecha_pago = proxima_fecha_pago
        gasto.categoria_id = categoria_id
        gasto.activo = 1 if activo else 0
        self.db.commit()
        self.db.refresh(gasto)
        return gasto

    def eliminar_gasto(self, gasto_id):
        gasto = self.db.get(GastoRecurrente, gasto_id)
        if gasto is None:
            return False
        self.db.delete(gasto)
        self.db.commit()
        return True

    def pagar(self, gasto_id, cuenta_id, fecha_pago=None):
        gasto = self.db.get(GastoRecurrente, gasto_id)
        cuenta = self.db.get(Cuenta, cuenta_id)
        fecha_pago = fecha_pago or date.today()

        if gasto is None or not gasto.activo:
            raise ValueError("El gasto recurrente no está disponible.")
        if cuenta is None:
            raise ValueError("La cuenta seleccionada no existe.")
        if gasto.proxima_fecha_pago > fecha_pago:
            raise ValueError("Este gasto todavía no está pendiente de pago.")

        self._validar_categoria_gasto(gasto.categoria_id)
        valor = -abs(gasto.valor)
        movimiento = Movimiento(
            fecha=fecha_pago,
            descripcion=f"Pago recurrente: {gasto.nombre}",
            valor=valor,
            cuenta_id=cuenta_id,
            categoria_id=gasto.categoria_id,
            observaciones=f"Pago de gasto recurrente ({gasto.frecuencia.lower()}).",
        )
        self.db.add(movimiento)
        cuenta.saldo += valor
        gasto.ultima_fecha_pago = fecha_pago
        gasto.proxima_fecha_pago = self._siguiente_fecha(gasto.proxima_fecha_pago, gasto.frecuencia)
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def _validar_categoria_gasto(self, categoria_id):
        categoria = self.db.get(Categoria, categoria_id)
        if categoria is None or categoria.tipo != "Gasto":
            raise ValueError("Selecciona una categoría de tipo Gasto.")

    @staticmethod
    def _siguiente_fecha(fecha, frecuencia):
        if frecuencia == "Semanal":
            return fecha + timedelta(days=7)
        if frecuencia == "Quincenal":
            return fecha + timedelta(days=15)
        if frecuencia == "Anual":
            try:
                return fecha.replace(year=fecha.year + 1)
            except ValueError:
                return fecha.replace(year=fecha.year + 1, day=28)

        mes = fecha.month + 1
        anio = fecha.year + (1 if mes == 13 else 0)
        mes = 1 if mes == 13 else mes
        return fecha.replace(day=min(fecha.day, monthrange(anio, mes)[1]), year=anio, month=mes)

    def cerrar(self):
        self.db.close()

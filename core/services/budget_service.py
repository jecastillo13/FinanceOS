from sqlalchemy import func

from core.database import get_session
from core.models import Categoria, Movimiento, Presupuesto
from core.services.audit_service import registrar_auditoria
from core.services.validation import monto_positivo, periodo_valido
from core.services.exchange_service import ExchangeService


class BudgetService:
    def __init__(self):
        self.db = get_session()

    def obtener_presupuestos(self, anio, mes):
        return (
            self.db.query(Presupuesto)
            .filter(Presupuesto.anio == anio, Presupuesto.mes == mes)
            .order_by(Presupuesto.categoria_id)
            .all()
        )

    def guardar_presupuesto(self, anio, mes, categoria_id, valor):
        anio, mes = periodo_valido(anio, mes)
        categoria = self.db.get(Categoria, categoria_id)
        if categoria is None or categoria.tipo != "Gasto":
            raise ValueError("Solo puedes crear presupuestos para categorías de gasto.")

        presupuesto = (
            self.db.query(Presupuesto)
            .filter(Presupuesto.anio == anio, Presupuesto.mes == mes, Presupuesto.categoria_id == categoria_id)
            .first()
        )
        if presupuesto is None:
            presupuesto = Presupuesto(anio=anio, mes=mes, categoria_id=categoria_id, valor=monto_positivo(valor, "El presupuesto"))
            self.db.add(presupuesto)
        else:
            presupuesto.valor = monto_positivo(valor, "El presupuesto")
        registrar_auditoria(
            self.db,
            "PRESUPUESTO_GUARDADO",
            f"Presupuesto de {categoria.nombre} para {mes:02d}/{anio}: {presupuesto.valor:.2f} COP.",
        )
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def eliminar_presupuesto(self, presupuesto_id):
        presupuesto = self.db.get(Presupuesto, presupuesto_id)
        if presupuesto is None:
            return False
        registrar_auditoria(
            self.db,
            "PRESUPUESTO_ELIMINADO",
            f"Presupuesto #{presupuesto.id} eliminado ({presupuesto.mes:02d}/{presupuesto.anio}).",
        )
        self.db.delete(presupuesto)
        self.db.commit()
        return True

    def gastado(self, categoria_id, anio, mes):
        movimientos = (
            self.db.query(Movimiento)
            .join(Categoria)
            .filter(
                Movimiento.categoria_id == categoria_id,
                Categoria.tipo == "Gasto",
                func.extract("year", Movimiento.fecha) == anio,
                func.extract("month", Movimiento.fecha) == mes,
            )
            .all()
        )
        exchange = ExchangeService()
        try:
            total = sum(
                exchange.convertir(movimiento.valor, movimiento.cuenta.moneda, "COP") or 0
                for movimiento in movimientos
            )
        finally:
            exchange.cerrar()
        return abs(total)

    def resumen(self, anio, mes):
        return [
            {"presupuesto": presupuesto, "gastado": self.gastado(presupuesto.categoria_id, anio, mes)}
            for presupuesto in self.obtener_presupuestos(anio, mes)
        ]

    def cerrar(self):
        self.db.close()

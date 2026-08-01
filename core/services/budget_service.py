from core.database import get_session
from core.models import Categoria, Movimiento, Presupuesto
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
        categoria = self.db.get(Categoria, categoria_id)
        if categoria is None or categoria.tipo != "Gasto":
            raise ValueError("Solo puedes crear presupuestos para categorías de gasto.")

        presupuesto = (
            self.db.query(Presupuesto)
            .filter(Presupuesto.anio == anio, Presupuesto.mes == mes, Presupuesto.categoria_id == categoria_id)
            .first()
        )
        if presupuesto is None:
            presupuesto = Presupuesto(anio=anio, mes=mes, categoria_id=categoria_id, valor=abs(float(valor)))
            self.db.add(presupuesto)
        else:
            presupuesto.valor = abs(float(valor))
        self.db.commit()
        self.db.refresh(presupuesto)
        return presupuesto

    def eliminar_presupuesto(self, presupuesto_id):
        presupuesto = self.db.get(Presupuesto, presupuesto_id)
        if presupuesto is None:
            return False
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

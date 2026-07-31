from calendar import month_abbr
from datetime import date

from sqlalchemy import func

from core.database import get_session
from core.models import Categoria, Movimiento, Presupuesto
from core.services.account_service import AccountService
from core.services.movement_service import MovementService


class DashboardService:
    def __init__(self):
        self.account_service = AccountService()
        self.movement_service = MovementService()
        self.db = get_session()

    def patrimonio(self):
        return self.account_service.saldo_total()

    def cuentas(self):
        return self.account_service.total_cuentas()

    def ingresos(self):
        return self.movement_service.ingresos_totales()

    def gastos(self):
        return self.movement_service.gastos_totales()

    def inversiones(self):
        return 0

    def metas(self):
        return 0

    def resumen_mes(self, anio=None, mes=None):
        hoy = date.today()
        anio, mes = anio or hoy.year, mes or hoy.month
        ingresos = self._total_por_tipo("Ingreso", anio, mes)
        gastos = abs(self._total_por_tipo("Gasto", anio, mes))
        return {"ingresos": ingresos, "gastos": gastos, "balance": ingresos - gastos}

    def gastos_por_categoria(self, anio=None, mes=None):
        hoy = date.today()
        anio, mes = anio or hoy.year, mes or hoy.month
        filas = (
            self.db.query(Categoria.nombre, Categoria.icono, func.sum(Movimiento.valor).label("total"))
            .join(Movimiento)
            .filter(Categoria.tipo == "Gasto", func.extract("year", Movimiento.fecha) == anio, func.extract("month", Movimiento.fecha) == mes)
            .group_by(Categoria.id, Categoria.nombre, Categoria.icono)
            .order_by(func.sum(Movimiento.valor))
            .all()
        )
        return [{"categoría": f"{fila.icono or '🏷️'} {fila.nombre}", "valor": abs(fila.total)} for fila in filas]

    def flujo_seis_meses(self):
        hoy = date.today()
        periodos = []
        for desplazamiento in range(5, -1, -1):
            indice = hoy.year * 12 + hoy.month - 1 - desplazamiento
            anio, mes_cero = divmod(indice, 12)
            mes = mes_cero + 1
            resumen = self.resumen_mes(anio, mes)
            periodos.append({"mes": f"{month_abbr[mes]} {str(anio)[-2:]}", **resumen})
        return periodos

    def cuentas_por_saldo(self):
        return [
            {"cuenta": f"{cuenta.icono} {cuenta.nombre}", "saldo": cuenta.saldo, "moneda": cuenta.moneda}
            for cuenta in self.account_service.obtener_cuentas()
        ]

    def alertas_presupuesto(self, anio=None, mes=None):
        hoy = date.today()
        anio, mes = anio or hoy.year, mes or hoy.month
        presupuestos = self.db.query(Presupuesto).filter(Presupuesto.anio == anio, Presupuesto.mes == mes).all()
        alertas = []
        for presupuesto in presupuestos:
            gastado = abs(self._total_categoria(presupuesto.categoria_id, anio, mes))
            porcentaje = gastado / presupuesto.valor * 100 if presupuesto.valor else 0
            if porcentaje >= 80:
                alertas.append({"categoría": presupuesto.categoria.nombre, "porcentaje": porcentaje, "gastado": gastado, "límite": presupuesto.valor})
        return sorted(alertas, key=lambda alerta: alerta["porcentaje"], reverse=True)

    def resumen(self):
        return {"patrimonio": self.patrimonio(), "cuentas": self.cuentas(), "ingresos": self.ingresos(), "gastos": self.gastos(), "inversiones": self.inversiones(), "metas": self.metas()}

    def _total_por_tipo(self, tipo, anio, mes):
        return (
            self.db.query(func.sum(Movimiento.valor))
            .join(Categoria)
            .filter(Categoria.tipo == tipo, func.extract("year", Movimiento.fecha) == anio, func.extract("month", Movimiento.fecha) == mes)
            .scalar() or 0
        )

    def _total_categoria(self, categoria_id, anio, mes):
        return (
            self.db.query(func.sum(Movimiento.valor))
            .filter(Movimiento.categoria_id == categoria_id, func.extract("year", Movimiento.fecha) == anio, func.extract("month", Movimiento.fecha) == mes)
            .scalar() or 0
        )

    def cerrar(self):
        self.account_service.cerrar()
        self.movement_service.cerrar()
        self.db.close()

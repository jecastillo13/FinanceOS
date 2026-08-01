from calendar import month_abbr
from datetime import date

from sqlalchemy.orm import joinedload

from core.database import get_session
from core.models import Categoria, Movimiento, Presupuesto
from core.services.account_service import AccountService
from core.services.exchange_service import ExchangeService


class DashboardService:
    MONEDA_BASE = "COP"

    def __init__(self):
        self.account_service = AccountService()
        self.db = get_session()
        self.exchange = ExchangeService()
        self._movimientos_cache = {}

    def patrimonio(self):
        return self.account_service.saldo_total(self.MONEDA_BASE, self.exchange)

    def cuentas(self):
        return self.account_service.total_cuentas()

    def resumen_mes(self, anio=None, mes=None):
        movimientos, pendientes = self._movimientos_convertidos(anio, mes)
        ingresos = sum(m["valor_cop"] for m in movimientos if m["tipo"] == "Ingreso")
        gastos = abs(sum(m["valor_cop"] for m in movimientos if m["tipo"] == "Gasto"))
        return {"ingresos": ingresos, "gastos": gastos, "balance": ingresos - gastos, "pendientes": pendientes}

    def gastos_por_categoria(self, anio=None, mes=None):
        movimientos, pendientes = self._movimientos_convertidos(anio, mes)
        totales = {}
        for movimiento in movimientos:
            if movimiento["tipo"] != "Gasto":
                continue
            clave = movimiento["categoria"]
            totales[clave] = totales.get(clave, 0) + abs(movimiento["valor_cop"])
        return ([{"categoría": categoria, "valor": valor} for categoria, valor in sorted(totales.items(), key=lambda item: item[1], reverse=True)], pendientes)

    def flujo_seis_meses(self):
        hoy, periodos = date.today(), []
        for desplazamiento in range(5, -1, -1):
            indice = hoy.year * 12 + hoy.month - 1 - desplazamiento
            anio, mes_cero = divmod(indice, 12)
            mes = mes_cero + 1
            resumen = self.resumen_mes(anio, mes)
            periodos.append({"mes": f"{month_abbr[mes]} {str(anio)[-2:]}", **resumen})
        return periodos

    def cuentas_por_saldo(self):
        datos, pendientes = self.account_service.saldos_consolidados(self.MONEDA_BASE, self.exchange)
        cuentas = [
            {"cuenta": f"{dato['cuenta'].icono} {dato['cuenta'].nombre}", "saldo_cop": dato["saldo_base"], "moneda_original": dato["cuenta"].moneda}
            for dato in datos
        ]
        return cuentas, pendientes

    def alertas_presupuesto(self, anio=None, mes=None):
        hoy = date.today()
        anio, mes = anio or hoy.year, mes or hoy.month
        movimientos, pendientes = self._movimientos_convertidos(anio, mes)
        gasto_por_categoria = {}
        for movimiento in movimientos:
            if movimiento["tipo"] == "Gasto":
                gasto_por_categoria[movimiento["categoria_id"]] = gasto_por_categoria.get(movimiento["categoria_id"], 0) + abs(movimiento["valor_cop"])
        alertas = []
        presupuestos = self.db.query(Presupuesto).filter(Presupuesto.anio == anio, Presupuesto.mes == mes).all()
        for presupuesto in presupuestos:
            gastado = gasto_por_categoria.get(presupuesto.categoria_id, 0)
            porcentaje = gastado / presupuesto.valor * 100 if presupuesto.valor else 0
            if porcentaje >= 80:
                alertas.append({"categoría": presupuesto.categoria.nombre, "porcentaje": porcentaje, "gastado": gastado, "límite": presupuesto.valor})
        return sorted(alertas, key=lambda alerta: alerta["porcentaje"], reverse=True), pendientes

    def resumen(self):
        resumen_mes = self.resumen_mes()
        return {"patrimonio": self.patrimonio(), "cuentas": self.cuentas(), **resumen_mes}

    def cuentas_sin_tasa(self):
        _, pendientes = self.account_service.saldos_consolidados(self.MONEDA_BASE, self.exchange)
        return pendientes

    def _movimientos_convertidos(self, anio=None, mes=None):
        clave = (anio, mes)
        if clave in self._movimientos_cache:
            return self._movimientos_cache[clave]

        consulta = (
            self.db.query(Movimiento)
            .join(Categoria)
            .options(joinedload(Movimiento.cuenta), joinedload(Movimiento.categoria))
            .filter(Categoria.tipo.in_(["Ingreso", "Gasto"]))
        )
        if anio and mes:
            from sqlalchemy import func
            consulta = consulta.filter(func.extract("year", Movimiento.fecha) == anio, func.extract("month", Movimiento.fecha) == mes)

        convertidos, pendientes = [], {}
        for movimiento in consulta.all():
            valor_cop = self.exchange.convertir(movimiento.valor, movimiento.cuenta.moneda, self.MONEDA_BASE)
            if valor_cop is None:
                pendientes[movimiento.cuenta.id] = movimiento.cuenta
                continue
            convertidos.append({
                "valor_cop": valor_cop, "tipo": movimiento.categoria.tipo, "categoria": f"{movimiento.categoria.icono or '🏷️'} {movimiento.categoria.nombre}",
                "categoria_id": movimiento.categoria_id,
            })
        resultado = (convertidos, list(pendientes.values()))
        self._movimientos_cache[clave] = resultado
        return resultado

    def cerrar(self):
        self.account_service.cerrar()
        self.exchange.cerrar()
        self.db.close()

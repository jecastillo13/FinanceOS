from sqlalchemy import func

from core.database import get_session
from core.models import (
    Cuenta,
    Categoria,
    Movimiento,
    Inversion,
    Meta
)


class FinanceService:

    def __init__(self):
        self.db = get_session()

    # =====================================================
    # CUENTAS
    # =====================================================

    def obtener_cuentas(self):
        return (
            self.db.query(Cuenta)
            .order_by(Cuenta.nombre)
            .all()
        )

    def obtener_cuenta(self, cuenta_id):
        return self.db.get(Cuenta, cuenta_id)

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
            moneda=moneda,
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
        cuenta.moneda = moneda
        cuenta.color = color
        cuenta.icono = icono

        self.db.commit()
        self.db.refresh(cuenta)

        return cuenta

    def eliminar_cuenta(self, cuenta_id):

        cuenta = self.db.get(Cuenta, cuenta_id)

        if cuenta:

            self.db.delete(cuenta)
            self.db.commit()

    def total_cuentas(self):

        return self.db.query(Cuenta).count()

    def saldo_total(self):

        saldo = self.db.query(
            func.sum(Cuenta.saldo)
        ).scalar()

        return saldo or 0

    # =====================================================
    # CATEGORÍAS
    # =====================================================

    def obtener_categorias(self):

        return (
            self.db.query(Categoria)
            .order_by(Categoria.tipo, Categoria.nombre)
            .all()
        )

    # =====================================================
    # MOVIMIENTOS
    # =====================================================

    def total_ingresos(self):

        total = (
            self.db.query(
                func.sum(Movimiento.valor)
            )
            .filter(Movimiento.valor > 0)
            .scalar()
        )

        return total or 0

    def total_gastos(self):

        total = (
            self.db.query(
                func.sum(Movimiento.valor)
            )
            .filter(Movimiento.valor < 0)
            .scalar()
        )

        return abs(total or 0)

    # =====================================================
    # INVERSIONES
    # =====================================================

    def total_inversiones(self):

        total = 0

        inversiones = self.db.query(
            Inversion
        ).all()

        for inv in inversiones:

            if inv.precio_actual:

                total += (
                    inv.cantidad *
                    inv.precio_actual
                )

        return total

    # =====================================================
    # METAS
    # =====================================================

    def total_metas(self):

        return self.db.query(Meta).count()

    # =====================================================
    # DASHBOARD
    # =====================================================

    def patrimonio(self):

        return (
            self.saldo_total() +
            self.total_inversiones()
        )

    # =====================================================
    # CERRAR
    # =====================================================

    def cerrar(self):

        self.db.close()
from sqlalchemy import func

from core.database import get_session
from core.models import Movimiento, Cuenta


class MovementService:

    def __init__(self):
        self.db = get_session()

    # =====================================================
    # CRUD
    # =====================================================

    def registrar_movimiento(
        self,
        fecha,
        descripcion,
        valor,
        cuenta_id,
        categoria_id,
        observaciones=""
    ):

        movimiento = Movimiento(
            fecha=fecha,
            descripcion=descripcion,
            valor=valor,
            cuenta_id=cuenta_id,
            categoria_id=categoria_id,
            observaciones=observaciones
        )

        self.db.add(movimiento)

        self.actualizar_saldo(
            cuenta_id,
            valor
        )

        self.db.commit()
        self.db.refresh(movimiento)

        return movimiento

    def actualizar_movimiento(
        self,
        movimiento_id,
        fecha,
        descripcion,
        valor,
        categoria_id,
        observaciones=""
    ):

        movimiento = self.db.get(
            Movimiento,
            movimiento_id
        )

        if movimiento is None:
            return None

        diferencia = valor - movimiento.valor

        movimiento.fecha = fecha
        movimiento.descripcion = descripcion
        movimiento.valor = valor
        movimiento.categoria_id = categoria_id
        movimiento.observaciones = observaciones

        self.actualizar_saldo(
            movimiento.cuenta_id,
            diferencia
        )

        self.db.commit()
        self.db.refresh(movimiento)

        return movimiento

    def eliminar_movimiento(self, movimiento_id):

        movimiento = self.db.get(
            Movimiento,
            movimiento_id
        )

        if movimiento is None:
            return

        self.actualizar_saldo(
            movimiento.cuenta_id,
            -movimiento.valor
        )

        self.db.delete(movimiento)
        self.db.commit()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def obtener_movimientos(self):

        return (
            self.db.query(Movimiento)
            .order_by(Movimiento.fecha.desc())
            .all()
        )

    def obtener_movimiento(self, movimiento_id):

        return self.db.get(
            Movimiento,
            movimiento_id
        )

    def ultimos_movimientos(self, limite=10):

        return (
            self.db.query(Movimiento)
            .order_by(Movimiento.fecha.desc())
            .limit(limite)
            .all()
        )

    # =====================================================
    # SALDOS
    # =====================================================

    def actualizar_saldo(
        self,
        cuenta_id,
        valor
    ):

        cuenta = self.db.get(
            Cuenta,
            cuenta_id
        )

        if cuenta:

            cuenta.saldo += valor

    # =====================================================
    # REPORTES
    # =====================================================

    def movimientos_por_categoria(
        self,
        categoria_id
    ):

        return (
            self.db.query(Movimiento)
            .filter(
                Movimiento.categoria_id == categoria_id
            )
            .all()
        )

    def movimientos_por_mes(
        self,
        anio,
        mes
    ):

        return (
            self.db.query(Movimiento)
            .filter(
                func.extract("year", Movimiento.fecha) == anio,
                func.extract("month", Movimiento.fecha) == mes
            )
            .all()
        )

    def ingresos_totales(self):

        total = (
            self.db.query(
                func.sum(Movimiento.valor)
            )
            .filter(
                Movimiento.valor > 0
            )
            .scalar()
        )

        return total or 0

    def gastos_totales(self):

        total = (
            self.db.query(
                func.sum(Movimiento.valor)
            )
            .filter(
                Movimiento.valor < 0
            )
            .scalar()
        )

        return abs(total or 0)

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.db.close()
from sqlalchemy import func, or_

from core.database import get_session
from core.models import Categoria, Movimiento, Cuenta
from core.services.audit_service import registrar_auditoria
from core.services.attachment_service import eliminar_archivos_adjuntos
from core.services.validation import monto_positivo, texto_requerido


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
        observaciones="",
        huella=None,
    ):

        descripcion = texto_requerido(descripcion, "La descripcion", 250)
        valor_firmado = self._valor_firmado(valor, categoria_id)
        if self.db.get(Cuenta, cuenta_id) is None:
            raise ValueError("La cuenta seleccionada no existe.")

        huella = (huella or "").strip().lower() or None
        if huella:
            existente = self.db.query(Movimiento).filter(Movimiento.huella == huella).first()
            if existente:
                return existente

        movimiento = Movimiento(
            fecha=fecha,
            descripcion=descripcion,
            valor=valor_firmado,
            cuenta_id=cuenta_id,
            categoria_id=categoria_id,
            observaciones=observaciones,
            huella=huella,
        )

        self.db.add(movimiento)

        self.actualizar_saldo(
            cuenta_id,
            valor_firmado
        )
        registrar_auditoria(
            self.db,
            "MOVIMIENTO_CREADO",
            f"Movimiento #{movimiento.id or 'nuevo'}: {descripcion} ({valor_firmado:.2f}) en cuenta #{cuenta_id}.",
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
        cuenta_id,
        categoria_id,
        observaciones="",
        huella=None,
    ):

        movimiento = self.db.get(
            Movimiento,
            movimiento_id
        )

        if movimiento is None:
            return None

        descripcion = texto_requerido(descripcion, "La descripcion", 250)
        valor_firmado = self._valor_firmado(valor, categoria_id)
        if self.db.get(Cuenta, cuenta_id) is None:
            raise ValueError("La cuenta seleccionada no existe.")
        cuenta_anterior_id = movimiento.cuenta_id
        valor_anterior = movimiento.valor

        movimiento.fecha = fecha
        movimiento.descripcion = descripcion
        movimiento.valor = valor_firmado
        movimiento.cuenta_id = cuenta_id
        movimiento.categoria_id = categoria_id
        movimiento.observaciones = observaciones
        if huella and huella != movimiento.huella:
            repetido = self.db.query(Movimiento).filter(
                Movimiento.huella == huella,
                Movimiento.id != movimiento.id,
            ).first()
            if repetido:
                raise ValueError("Este comprobante ya esta asociado a otro movimiento.")
            movimiento.huella = huella

        if cuenta_anterior_id == cuenta_id:
            self.actualizar_saldo(cuenta_id, valor_firmado - valor_anterior)
        else:
            self.actualizar_saldo(cuenta_anterior_id, -valor_anterior)
            self.actualizar_saldo(cuenta_id, valor_firmado)

        registrar_auditoria(
            self.db,
            "MOVIMIENTO_ACTUALIZADO",
            f"Movimiento #{movimiento.id} actualizado: {descripcion} ({valor_firmado:.2f}) en cuenta #{cuenta_id}.",
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

        registrar_auditoria(
            self.db,
            "MOVIMIENTO_ELIMINADO",
            f"Movimiento #{movimiento.id} eliminado: {movimiento.descripcion} ({movimiento.valor:.2f}).",
        )
        eliminar_archivos_adjuntos(movimiento)
        self.db.delete(movimiento)
        self.db.commit()

    # =====================================================
    # CONSULTAS
    # =====================================================

    def obtener_movimientos(self, limite=None, desplazamiento=0, busqueda=""):
        consulta = (
            self.db.query(Movimiento)
            .join(Categoria)
            .join(Cuenta, Movimiento.cuenta_id == Cuenta.id)
            .filter(Categoria.tipo.in_(["Ingreso", "Gasto"]))
            .order_by(Movimiento.fecha.desc())
        )
        if busqueda:
            termino = f"%{busqueda.strip()}%"
            consulta = consulta.filter(
                or_(
                    Movimiento.descripcion.ilike(termino),
                    Categoria.nombre.ilike(termino),
                    Cuenta.nombre.ilike(termino),
                )
            )
        if desplazamiento:
            consulta = consulta.offset(desplazamiento)
        if limite:
            consulta = consulta.limit(limite)
        return consulta.all()

    def contar_movimientos(self, busqueda=""):
        consulta = (
            self.db.query(Movimiento)
            .join(Categoria)
            .join(Cuenta, Movimiento.cuenta_id == Cuenta.id)
            .filter(Categoria.tipo.in_(["Ingreso", "Gasto"]))
        )
        if busqueda:
            termino = f"%{busqueda.strip()}%"
            consulta = consulta.filter(
                or_(
                    Movimiento.descripcion.ilike(termino),
                    Categoria.nombre.ilike(termino),
                    Cuenta.nombre.ilike(termino),
                )
            )
        return consulta.count()

    def obtener_movimiento(self, movimiento_id):

        return self.db.get(
            Movimiento,
            movimiento_id
        )

    def ultimos_movimientos(self, limite=10):

        return (
            self.db.query(Movimiento)
            .join(Categoria)
            .filter(Categoria.tipo.in_(["Ingreso", "Gasto"]))
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

    def _valor_firmado(self, valor, categoria_id):
        """Deriva el signo del movimiento desde la categoría seleccionada."""
        categoria = self.db.get(Categoria, categoria_id)

        if categoria is None:
            raise ValueError("La categoría seleccionada no existe.")

        monto = monto_positivo(valor)

        if categoria.tipo == "Ingreso":
            return monto

        if categoria.tipo == "Gasto":
            return -monto

        raise ValueError("La categoría debe ser de tipo Ingreso o Gasto.")

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
            .join(Categoria)
            .filter(
                Categoria.tipo == "Ingreso"
            )
            .scalar()
        )

        return total or 0

    def gastos_totales(self):

        total = (
            self.db.query(
                func.sum(Movimiento.valor)
            )
            .join(Categoria)
            .filter(
                Categoria.tipo == "Gasto"
            )
            .scalar()
        )

        return abs(total or 0)

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.db.close()

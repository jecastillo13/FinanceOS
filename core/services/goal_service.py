from sqlalchemy.orm import joinedload

from core.database import get_session
from core.models import Categoria, Cuenta, Meta, MetaOperacion, Movimiento
from core.services.audit_service import registrar_auditoria
from core.services.attachment_service import eliminar_archivos_adjuntos
from core.services.exchange_service import ExchangeService
from core.services.validation import moneda_valida, monto_positivo, texto_requerido


class GoalService:
    """Gestiona objetivos sin duplicar los gastos reales de la contabilidad."""

    def __init__(self):
        self.db = get_session()
        self.exchange = ExchangeService()

    def obtener_metas(self, incluir_inactivas=False):
        consulta = self.db.query(Meta)
        if not incluir_inactivas:
            consulta = consulta.filter(Meta.activa == 1)
        return consulta.order_by(Meta.fecha_limite.is_(None), Meta.fecha_limite, Meta.nombre).all()

    def obtener_meta(self, meta_id):
        return self.db.get(Meta, meta_id)

    def crear_meta(self, nombre, objetivo, moneda="COP", fecha_limite=None, descripcion=""):
        meta = Meta(
            nombre=texto_requerido(nombre, "El nombre de la meta", 100),
            objetivo=monto_positivo(objetivo, "El objetivo"),
            moneda=moneda_valida(moneda),
            fecha_limite=fecha_limite,
            descripcion=str(descripcion or "").strip(),
        )
        self.db.add(meta)
        registrar_auditoria(self.db, "META_CREADA", f"Meta creada: {meta.nombre} ({meta.objetivo:.2f} {meta.moneda}).")
        self.db.commit()
        self.db.refresh(meta)
        return meta

    def resumen(self, meta):
        operaciones = (
            self.db.query(MetaOperacion)
            .options(joinedload(MetaOperacion.movimiento))
            .filter(MetaOperacion.meta_id == meta.id)
            .order_by(MetaOperacion.fecha.desc(), MetaOperacion.id.desc())
            .all()
        )
        aportado = sum(operacion.valor_meta for operacion in operaciones if operacion.tipo == "Aporte")
        pagado = sum(operacion.valor_meta for operacion in operaciones if operacion.tipo == "Pago")
        return {
            "meta": meta,
            "aportado": aportado,
            "pagado": pagado,
            "pendiente": max(meta.objetivo - pagado, 0),
            "porcentaje": min(pagado / meta.objetivo * 100, 100) if meta.objetivo else 0,
            "operaciones": operaciones,
        }

    def aportar(self, meta_id, valor, fecha, descripcion=""):
        meta = self._meta_activa(meta_id)
        operacion = MetaOperacion(
            meta_id=meta.id,
            tipo="Aporte",
            valor_meta=monto_positivo(valor, "El aporte"),
            fecha=fecha,
            descripcion=str(descripcion or "").strip(),
        )
        self.db.add(operacion)
        registrar_auditoria(
            self.db,
            "APORTE_META_REGISTRADO",
            f"Aporte de {operacion.valor_meta:.2f} {meta.moneda} a la meta {meta.nombre}.",
        )
        self.db.commit()
        self.db.refresh(operacion)
        return operacion

    def registrar_pago(self, meta_id, fecha, cuenta_id, categoria_id, valor, descripcion="", observaciones=""):
        meta = self._meta_activa(meta_id)
        cuenta = self.db.get(Cuenta, cuenta_id)
        categoria = self.db.get(Categoria, categoria_id)
        if cuenta is None:
            raise ValueError("La cuenta seleccionada no existe.")
        if categoria is None or categoria.tipo != "Gasto":
            raise ValueError("Selecciona una categoria de gasto para registrar el pago.")

        valor_movimiento = monto_positivo(valor, "El pago")
        descripcion = texto_requerido(descripcion, "La descripcion del pago", 250)
        valor_meta = self.exchange.convertir(valor_movimiento, cuenta.moneda, meta.moneda)
        if valor_meta is None:
            raise ValueError(f"Falta una tasa para convertir {cuenta.moneda} a {meta.moneda}. Actualizala en Monedas.")

        movimiento = Movimiento(
            fecha=fecha,
            descripcion=descripcion,
            valor=-valor_movimiento,
            cuenta_id=cuenta.id,
            categoria_id=categoria.id,
            observaciones=str(observaciones or "").strip(),
        )
        self.db.add(movimiento)
        self.db.flush()
        cuenta.saldo -= valor_movimiento
        operacion = MetaOperacion(
            meta_id=meta.id,
            movimiento_id=movimiento.id,
            tipo="Pago",
            valor_meta=valor_meta,
            fecha=fecha,
            descripcion=descripcion,
        )
        self.db.add(operacion)
        registrar_auditoria(
            self.db,
            "PAGO_META_REGISTRADO",
            f"Pago de {valor_meta:.2f} {meta.moneda} para la meta {meta.nombre}; movimiento #{movimiento.id}.",
        )
        self.db.commit()
        self.db.refresh(operacion)
        return operacion

    def eliminar_operacion(self, operacion_id):
        operacion = self.db.get(MetaOperacion, operacion_id)
        if operacion is None:
            return False
        meta = self.db.get(Meta, operacion.meta_id)
        movimiento = self.db.get(Movimiento, operacion.movimiento_id) if operacion.movimiento_id else None
        if movimiento:
            cuenta = self.db.get(Cuenta, movimiento.cuenta_id)
            if cuenta:
                cuenta.saldo -= movimiento.valor
            eliminar_archivos_adjuntos(movimiento)
            self.db.delete(movimiento)
        registrar_auditoria(
            self.db,
            "OPERACION_META_ELIMINADA",
            f"{operacion.tipo} eliminado de la meta {meta.nombre if meta else operacion.meta_id}.",
        )
        self.db.delete(operacion)
        self.db.commit()
        return True

    def desactivar_meta(self, meta_id):
        meta = self.db.get(Meta, meta_id)
        if meta is None:
            return False
        meta.activa = 0
        registrar_auditoria(self.db, "META_ARCHIVADA", f"Meta archivada: {meta.nombre}.")
        self.db.commit()
        return True

    def eliminar_meta(self, meta_id):
        meta = self.db.get(Meta, meta_id)
        if meta is None:
            return False
        operaciones = list(meta.operaciones)
        pagos_eliminados = 0
        for operacion in operaciones:
            movimiento = self.db.get(Movimiento, operacion.movimiento_id) if operacion.movimiento_id else None
            if movimiento:
                cuenta = self.db.get(Cuenta, movimiento.cuenta_id)
                if cuenta:
                    cuenta.saldo -= movimiento.valor
                eliminar_archivos_adjuntos(movimiento)
                self.db.delete(operacion)
                self.db.delete(movimiento)
                pagos_eliminados += 1
            else:
                self.db.delete(operacion)
        registrar_auditoria(
            self.db,
            "META_ELIMINADA",
            f"Meta eliminada: {meta.nombre}; se eliminaron {len(operaciones)} operaciones y {pagos_eliminados} pagos vinculados.",
        )
        self.db.delete(meta)
        self.db.commit()
        return True

    def _meta_activa(self, meta_id):
        meta = self.db.get(Meta, meta_id)
        if meta is None or not meta.activa:
            raise ValueError("La meta seleccionada no esta disponible.")
        return meta

    def cerrar(self):
        self.exchange.cerrar()
        self.db.close()

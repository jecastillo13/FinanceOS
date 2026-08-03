from core.database import get_session
from core.models import Categoria, Cuenta, Movimiento, Transferencia
from core.services.audit_service import registrar_auditoria
from core.services.attachment_service import eliminar_archivos_adjuntos
from core.services.validation import monto_positivo


class TransferService:
    def __init__(self):
        self.db = get_session()

    def obtener_transferencias(self):
        return self.db.query(Transferencia).order_by(Transferencia.fecha.desc(), Transferencia.id.desc()).all()

    def crear_transferencia(self, fecha, cuenta_origen_id, cuenta_destino_id, valor, descripcion=""):
        if cuenta_origen_id == cuenta_destino_id:
            raise ValueError("La cuenta de origen y destino deben ser diferentes.")

        origen = self.db.get(Cuenta, cuenta_origen_id)
        destino = self.db.get(Cuenta, cuenta_destino_id)
        if origen is None or destino is None:
            raise ValueError("Selecciona cuentas válidas.")
        if origen.moneda.upper() != destino.moneda.upper():
            raise ValueError("Por ahora las transferencias solo se permiten entre cuentas de la misma moneda.")

        monto = monto_positivo(valor)

        categoria = self._categoria_transferencia()
        detalle = descripcion.strip() or "Transferencia entre cuentas"
        salida = Movimiento(
            fecha=fecha,
            descripcion=f"Transferencia a {destino.nombre}: {detalle}",
            valor=-monto,
            cuenta_id=origen.id,
            categoria_id=categoria.id,
            observaciones="Movimiento interno entre cuentas.",
        )
        entrada = Movimiento(
            fecha=fecha,
            descripcion=f"Transferencia desde {origen.nombre}: {detalle}",
            valor=monto,
            cuenta_id=destino.id,
            categoria_id=categoria.id,
            observaciones="Movimiento interno entre cuentas.",
        )
        self.db.add_all([salida, entrada])
        self.db.flush()
        origen.saldo -= monto
        destino.saldo += monto

        transferencia = Transferencia(
            fecha=fecha,
            valor=monto,
            descripcion=descripcion.strip(),
            cuenta_origen_id=origen.id,
            cuenta_destino_id=destino.id,
            movimiento_salida_id=salida.id,
            movimiento_entrada_id=entrada.id,
        )
        self.db.add(transferencia)
        registrar_auditoria(
            self.db,
            "TRANSFERENCIA_CREADA",
            f"Transferencia #{transferencia.id or 'nueva'}: {origen.nombre} → {destino.nombre} ({monto:.2f} {origen.moneda}).",
        )
        self.db.commit()
        self.db.refresh(transferencia)
        return transferencia

    def eliminar_transferencia(self, transferencia_id):
        transferencia = self.db.get(Transferencia, transferencia_id)
        if transferencia is None:
            return False

        origen = self.db.get(Cuenta, transferencia.cuenta_origen_id)
        destino = self.db.get(Cuenta, transferencia.cuenta_destino_id)
        salida = self.db.get(Movimiento, transferencia.movimiento_salida_id)
        entrada = self.db.get(Movimiento, transferencia.movimiento_entrada_id)
        if origen and destino:
            origen.saldo += transferencia.valor
            destino.saldo -= transferencia.valor
        if salida:
            eliminar_archivos_adjuntos(salida)
            self.db.delete(salida)
        if entrada:
            eliminar_archivos_adjuntos(entrada)
            self.db.delete(entrada)
        registrar_auditoria(
            self.db,
            "TRANSFERENCIA_REVERTIDA",
            f"Transferencia #{transferencia.id} revertida ({transferencia.valor:.2f}).",
        )
        self.db.delete(transferencia)
        self.db.commit()
        return True

    def _categoria_transferencia(self):
        categoria = (
            self.db.query(Categoria)
            .filter(Categoria.nombre == "Transferencia entre cuentas", Categoria.tipo == "Transferencia")
            .first()
        )
        if categoria is None:
            categoria = Categoria(
                nombre="Transferencia entre cuentas", tipo="Transferencia", grupo="Transferencias",
                icono="🔄", color="#2563EB", es_sistema=1, editable=1, activa=1,
            )
            self.db.add(categoria)
            self.db.flush()
        return categoria

    def cerrar(self):
        self.db.close()

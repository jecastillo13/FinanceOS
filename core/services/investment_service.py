from datetime import date

from core.database import get_session
from core.models import Categoria, Cuenta, Inversion, Movimiento
from core.services.audit_service import registrar_auditoria
from core.services.attachment_service import eliminar_archivos_adjuntos
from core.services.exchange_service import ExchangeService
from core.services.validation import moneda_valida, monto_positivo, texto_requerido


class InvestmentService:
    """Gestiona posiciones y convierte efectivo en activos sin duplicar patrimonio."""

    def __init__(self, db=None):
        self.db = db or get_session()
        self._sesion_propia = db is None
        self.exchange = ExchangeService()

    def obtener_inversiones(self):
        return self.db.query(Inversion).order_by(Inversion.tipo, Inversion.activo).all()

    def obtener_inversion(self, inversion_id):
        return self.db.get(Inversion, inversion_id)

    def crear_inversion(
        self, activo, tipo, cantidad, precio_compra, precio_actual, broker="",
        moneda="USD", valores_totales=False, fecha_apertura=None,
        es_posicion_inicial=True, cuenta_origen_id=None,
    ):
        cantidad, precio_compra, precio_actual = self._normalizar_valores(
            cantidad, precio_compra, precio_actual, valores_totales
        )
        moneda = moneda_valida(moneda)
        fecha_apertura = fecha_apertura or date.today()
        cuenta = None
        movimiento = None
        costo = cantidad * precio_compra
        if not es_posicion_inicial:
            cuenta = self._validar_cuenta_financiadora(cuenta_origen_id, moneda, costo)
            categoria = self._categoria_inversion()
            movimiento = Movimiento(
                fecha=fecha_apertura,
                descripcion=f"Compra de {str(activo).strip()} en {str(broker or '').strip() or 'broker'}",
                valor=-costo,
                cuenta_id=cuenta.id,
                categoria_id=categoria.id,
                observaciones="Conversión de efectivo en activo de inversión; no es un gasto.",
            )
            self.db.add(movimiento)
            self.db.flush()
            cuenta.saldo -= costo
        elif cuenta_origen_id is not None:
            raise ValueError("Una posición inicial no debe seleccionar una cuenta de origen.")

        inversion = Inversion(
            activo=texto_requerido(activo, "El nombre del activo", 100),
            tipo=texto_requerido(tipo, "El tipo de inversión", 50),
            cantidad=cantidad,
            precio_compra=precio_compra,
            precio_actual=precio_actual,
            broker=str(broker or "").strip(),
            moneda=moneda,
            fecha_apertura=fecha_apertura,
            es_posicion_inicial=bool(es_posicion_inicial),
            valores_totales=False,
            cuenta_origen_id=cuenta.id if cuenta else None,
            movimiento_aporte_id=movimiento.id if movimiento else None,
        )
        self.db.add(inversion)
        registrar_auditoria(self.db, "INVERSION_CREADA", f"Inversión creada: {inversion.activo} ({inversion.cantidad}).")
        self.db.commit()
        self.db.refresh(inversion)
        return inversion

    def actualizar_inversion(self, inversion_id, **datos):
        inversion = self.obtener_inversion(inversion_id)
        if inversion is None:
            return None
        cantidad, precio_compra, precio_actual = self._normalizar_valores(
            datos["cantidad"],
            datos["precio_compra"],
            datos["precio_actual"],
            datos.get("valores_totales", False),
        )
        nuevo_inicial = bool(datos.get("es_posicion_inicial", inversion.es_posicion_inicial))
        nueva_cuenta_id = datos.get("cuenta_origen_id")
        if nuevo_inicial != bool(inversion.es_posicion_inicial):
            raise ValueError("La procedencia no se puede cambiar al editar; elimina y registra la posición de nuevo.")
        nueva_moneda = moneda_valida(datos.get("moneda", "USD"))
        costo_anterior = inversion.cantidad * inversion.precio_compra
        costo_nuevo = cantidad * precio_compra
        movimiento = None
        if not inversion.es_posicion_inicial:
            if nueva_cuenta_id != inversion.cuenta_origen_id:
                raise ValueError("La cuenta financiadora no se puede cambiar al editar.")
            if nueva_moneda != inversion.moneda:
                raise ValueError("La moneda de una compra financiada no se puede cambiar.")
            cuenta = self.db.get(Cuenta, inversion.cuenta_origen_id)
            if cuenta is None:
                raise ValueError("La cuenta financiadora ya no existe.")
            diferencia = costo_nuevo - costo_anterior
            if diferencia > 0 and cuenta.saldo < diferencia:
                raise ValueError(f"Saldo insuficiente en {cuenta.nombre} para aumentar la inversión.")
            cuenta.saldo -= diferencia
            movimiento = self.db.get(Movimiento, inversion.movimiento_aporte_id)
            if movimiento is None:
                raise ValueError("La compra perdió su movimiento contable asociado.")
            movimiento.valor = -costo_nuevo
            movimiento.fecha = datos.get("fecha_apertura") or inversion.fecha_apertura

        inversion.activo = texto_requerido(datos["activo"], "El nombre del activo", 100)
        inversion.tipo = texto_requerido(datos["tipo"], "El tipo de inversión", 50)
        inversion.cantidad = cantidad
        inversion.precio_compra = precio_compra
        inversion.precio_actual = precio_actual
        inversion.broker = str(datos.get("broker") or "").strip()
        inversion.moneda = nueva_moneda
        inversion.fecha_apertura = datos.get("fecha_apertura") or inversion.fecha_apertura
        inversion.valores_totales = False
        if movimiento:
            movimiento.descripcion = f"Compra de {inversion.activo} en {inversion.broker or 'broker'}"
        registrar_auditoria(self.db, "INVERSION_ACTUALIZADA", f"Inversión #{inversion.id} actualizada: {inversion.activo}.")
        self.db.commit()
        self.db.refresh(inversion)
        return inversion

    def eliminar_inversion(self, inversion_id):
        inversion = self.obtener_inversion(inversion_id)
        if inversion is None:
            return False
        if not inversion.es_posicion_inicial:
            cuenta = self.db.get(Cuenta, inversion.cuenta_origen_id)
            movimiento = self.db.get(Movimiento, inversion.movimiento_aporte_id)
            if cuenta is None or movimiento is None:
                raise ValueError("No se puede revertir: falta la cuenta o el movimiento de compra.")
            cuenta.saldo += -movimiento.valor
            eliminar_archivos_adjuntos(movimiento)
            inversion.movimiento_aporte_id = None
            self.db.flush()
            self.db.delete(movimiento)
        registrar_auditoria(self.db, "INVERSION_ELIMINADA", f"Inversión eliminada y compra revertida: {inversion.activo}.")
        self.db.delete(inversion)
        self.db.commit()
        return True

    def resumen_posicion(self, inversion, moneda_base="COP"):
        costo = inversion.cantidad * inversion.precio_compra
        valor = inversion.cantidad * inversion.precio_actual
        ganancia = valor - costo
        rentabilidad = (ganancia / costo * 100) if costo else 0
        costo_base = self.exchange.convertir(costo, inversion.moneda, moneda_base)
        valor_base = self.exchange.convertir(valor, inversion.moneda, moneda_base)
        return {
            "inversion": inversion,
            "costo": float(round(costo, 2)),
            "valor": float(round(valor, 2)),
            "ganancia": float(round(ganancia, 2)),
            "rentabilidad": float(round(rentabilidad, 2)),
            "costo_base": costo_base,
            "valor_base": valor_base,
            "moneda_base": moneda_base,
        }

    @staticmethod
    def _normalizar_valores(cantidad, precio_compra, precio_actual, valores_totales):
        cantidad = monto_positivo(cantidad, "La cantidad")
        precio_compra = monto_positivo(precio_compra, "El monto invertido" if valores_totales else "El precio de compra")
        precio_actual = monto_positivo(precio_actual, "El valor de mercado" if valores_totales else "El precio actual")
        if valores_totales:
            precio_compra /= cantidad
            precio_actual /= cantidad
        return cantidad, precio_compra, precio_actual

    def resumen(self, moneda_base="COP"):
        posiciones = [self.resumen_posicion(inversion, moneda_base) for inversion in self.obtener_inversiones()]
        validas = [item for item in posiciones if item["costo_base"] is not None and item["valor_base"] is not None]
        costo_total = round(sum(item["costo_base"] for item in validas), 2)
        valor_total = round(sum(item["valor_base"] for item in validas), 2)
        ganancia_total = round(valor_total - costo_total, 2)
        rentabilidad = round((ganancia_total / costo_total * 100) if costo_total else 0, 2)
        return {
            "posiciones": posiciones,
            "costo_total": costo_total,
            "valor_total": valor_total,
            "ganancia_total": ganancia_total,
            "rentabilidad": rentabilidad,
            "moneda_base": moneda_base,
            "sin_tasa": [item["inversion"] for item in posiciones if item["valor_base"] is None],
        }

    def _validar_cuenta_financiadora(self, cuenta_id, moneda, costo):
        if cuenta_id is None:
            raise ValueError("Selecciona la cuenta desde la que se pagó la inversión.")
        cuenta = self.db.get(Cuenta, cuenta_id)
        if cuenta is None:
            raise ValueError("La cuenta seleccionada no existe.")
        if not cuenta.activa:
            raise ValueError("La cuenta seleccionada está desactivada y no admite movimientos nuevos.")
        if cuenta.moneda.upper() != moneda.upper():
            raise ValueError("La cuenta y la inversión deben usar la misma moneda.")
        if cuenta.saldo < costo:
            raise ValueError(f"Saldo insuficiente en {cuenta.nombre} para realizar la compra.")
        return cuenta

    def _categoria_inversion(self):
        categoria = (
            self.db.query(Categoria)
            .filter(Categoria.nombre == "Compra de inversiones", Categoria.tipo == "Inversion")
            .first()
        )
        if categoria is None:
            categoria = Categoria(
                nombre="Compra de inversiones", tipo="Inversion", grupo="Patrimonio",
                icono="📈", color="#7C3AED", es_sistema=1, editable=0, activa=1,
            )
            self.db.add(categoria)
            self.db.flush()
        return categoria

    def cerrar(self):
        self.exchange.cerrar()
        if self._sesion_propia:
            self.db.close()

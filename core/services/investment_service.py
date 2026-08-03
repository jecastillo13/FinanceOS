from core.database import get_session
from core.models import Inversion
from core.services.audit_service import registrar_auditoria
from core.services.exchange_service import ExchangeService
from core.services.validation import moneda_valida, monto_positivo, texto_requerido


class InvestmentService:
    """Gestiona posiciones y su valoración sin alterar los saldos bancarios."""

    def __init__(self):
        self.db = get_session()
        self.exchange = ExchangeService()

    def obtener_inversiones(self):
        return self.db.query(Inversion).order_by(Inversion.tipo, Inversion.activo).all()

    def obtener_inversion(self, inversion_id):
        return self.db.get(Inversion, inversion_id)

    def crear_inversion(self, activo, tipo, cantidad, precio_compra, precio_actual, broker="", moneda="USD", valores_totales=False):
        cantidad, precio_compra, precio_actual = self._normalizar_valores(
            cantidad, precio_compra, precio_actual, valores_totales
        )
        inversion = Inversion(
            activo=texto_requerido(activo, "El nombre del activo", 100),
            tipo=texto_requerido(tipo, "El tipo de inversión", 50),
            cantidad=cantidad,
            precio_compra=precio_compra,
            precio_actual=precio_actual,
            broker=str(broker or "").strip(),
            moneda=moneda_valida(moneda),
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
        inversion.activo = texto_requerido(datos["activo"], "El nombre del activo", 100)
        inversion.tipo = texto_requerido(datos["tipo"], "El tipo de inversión", 50)
        inversion.cantidad = cantidad
        inversion.precio_compra = precio_compra
        inversion.precio_actual = precio_actual
        inversion.broker = str(datos.get("broker") or "").strip()
        inversion.moneda = moneda_valida(datos.get("moneda", "USD"))
        registrar_auditoria(self.db, "INVERSION_ACTUALIZADA", f"Inversión #{inversion.id} actualizada: {inversion.activo}.")
        self.db.commit()
        self.db.refresh(inversion)
        return inversion

    def eliminar_inversion(self, inversion_id):
        inversion = self.obtener_inversion(inversion_id)
        if inversion is None:
            return False
        registrar_auditoria(self.db, "INVERSION_ELIMINADA", f"Inversión eliminada: {inversion.activo}.")
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
            "costo": round(costo, 2),
            "valor": round(valor, 2),
            "ganancia": round(ganancia, 2),
            "rentabilidad": round(rentabilidad, 2),
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

    def cerrar(self):
        self.exchange.cerrar()
        self.db.close()

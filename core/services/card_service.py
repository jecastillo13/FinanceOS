import hashlib
import re
import unicodedata
from datetime import datetime

from core.database import get_session
from core.models import Categoria, Cuenta, Movimiento, OperacionDetectada, Tarjeta
from core.services.audit_service import registrar_auditoria
from core.services.validation import monto_positivo, texto_requerido
from core.services.transfer_service import TransferService


class CardService:
    def __init__(self):
        self.db = get_session()

    def listar_tarjetas(self, incluir_inactivas=False):
        consulta = self.db.query(Tarjeta).order_by(Tarjeta.nombre)
        if not incluir_inactivas:
            consulta = consulta.filter(Tarjeta.activa == 1)
        return consulta.all()

    def crear_tarjeta(self, nombre, banco, ultimos_cuatro, tipo, moneda, cuenta_id=None):
        nombre = texto_requerido(nombre, "El nombre", 100)
        ultimos = re.sub(r"\D", "", ultimos_cuatro)[-4:]
        if len(ultimos) != 4:
            raise ValueError("Debes indicar los ultimos cuatro digitos de la tarjeta.")
        tipo = tipo.capitalize()
        if tipo not in {"Credito", "Debito"}:
            raise ValueError("El tipo debe ser Credito o Debito.")
        moneda = moneda.upper()
        cuenta = self.db.get(Cuenta, cuenta_id) if cuenta_id else None
        if tipo == "Debito" and cuenta is None:
            raise ValueError("Una tarjeta debito debe vincularse a una cuenta bancaria.")
        if cuenta is not None and not cuenta.activa:
            raise ValueError("La cuenta vinculada está desactivada.")
        if tipo == "Credito" and cuenta is None:
            cuenta = Cuenta(nombre=f"Deuda {nombre}", tipo="Tarjeta de credito", saldo=0,
                            moneda=moneda, color="#6D5DFB", icono="💳")
            self.db.add(cuenta)
            self.db.flush()
        if tipo == "Credito" and self._normalizar(cuenta.tipo) != "tarjeta de credito":
            raise ValueError("Una tarjeta credito debe usar una cuenta de tipo Tarjeta de credito.")
        if cuenta.moneda.upper() != moneda:
            raise ValueError("La tarjeta y su cuenta vinculada deben usar la misma moneda.")
        repetida = self.db.query(Tarjeta).filter(
            Tarjeta.banco == (banco or "").strip(), Tarjeta.ultimos_cuatro == ultimos,
            Tarjeta.tipo == tipo, Tarjeta.activa == 1,
        ).first()
        if repetida:
            raise ValueError("Esta tarjeta ya esta registrada.")
        tarjeta = Tarjeta(nombre=nombre, banco=(banco or "").strip(), ultimos_cuatro=ultimos,
                          tipo=tipo, moneda=moneda, cuenta_id=cuenta.id)
        self.db.add(tarjeta)
        self.db.commit()
        self.db.refresh(tarjeta)
        return tarjeta

    def eliminar_tarjeta(self, tarjeta_id):
        tarjeta = self.db.get(Tarjeta, tarjeta_id)
        if tarjeta is None:
            return False
        tarjeta.activa = 0
        self.db.commit()
        return True

    def detectar(self, texto, origen="Manual"):
        texto = texto_requerido(texto, "El mensaje", 4000)
        datos = self._extraer(texto)
        huella = self._huella(datos)
        existente = self.db.query(OperacionDetectada).filter_by(huella=huella).first()
        if existente:
            return existente, True
        tarjeta = None
        if datos["ultimos_cuatro"]:
            coincidencias = self.db.query(Tarjeta).filter(
                Tarjeta.ultimos_cuatro == datos["ultimos_cuatro"], Tarjeta.activa == 1
            ).all()
            if datos["banco"]:
                por_banco = [item for item in coincidencias if self._normalizar(item.banco) == self._normalizar(datos["banco"])]
                coincidencias = por_banco or coincidencias
            if datos["tipo"]:
                por_tipo = [item for item in coincidencias if item.tipo == datos["tipo"]]
                coincidencias = por_tipo or coincidencias
            tarjeta = coincidencias[0] if len(coincidencias) == 1 else None
        operacion = OperacionDetectada(
            origen=origen, texto_original=texto, comercio=datos["comercio"], valor=datos["valor"],
            moneda=datos["moneda"], fecha=datos["fecha"], banco=datos["banco"],
            ultimos_cuatro=datos["ultimos_cuatro"], tipo_sugerido=tarjeta.tipo if tarjeta else datos["tipo"],
            tarjeta_id=tarjeta.id if tarjeta else None, huella=huella,
        )
        self.db.add(operacion)
        self.db.commit()
        self.db.refresh(operacion)
        return operacion, False

    def listar_detecciones(self, estado="Pendiente"):
        consulta = self.db.query(OperacionDetectada).order_by(OperacionDetectada.fecha.desc())
        if estado:
            consulta = consulta.filter(OperacionDetectada.estado == estado)
        return consulta.all()

    def descartar(self, operacion_id):
        operacion = self.db.get(OperacionDetectada, operacion_id)
        if operacion is None:
            return None
        if operacion.estado != "Pendiente":
            raise ValueError("La operacion ya fue procesada.")
        operacion.estado = "Descartada"
        self.db.commit()
        return operacion

    def confirmar(self, operacion_id, categoria_id, tarjeta_id=None, cuenta_id=None, descripcion=None):
        operacion = self.db.get(OperacionDetectada, operacion_id)
        if operacion is None:
            return None
        if operacion.estado != "Pendiente":
            raise ValueError("La operacion ya fue procesada.")
        tarjeta = self.db.get(Tarjeta, tarjeta_id or operacion.tarjeta_id) if (tarjeta_id or operacion.tarjeta_id) else None
        cuenta_id = tarjeta.cuenta_id if tarjeta else cuenta_id
        cuenta = self.db.get(Cuenta, cuenta_id) if cuenta_id else None
        categoria = self.db.get(Categoria, categoria_id)
        if cuenta is None:
            raise ValueError("Selecciona la cuenta o tarjeta utilizada.")
        if not cuenta.activa:
            raise ValueError("La cuenta seleccionada está desactivada y no admite movimientos nuevos.")
        if categoria is None or categoria.tipo != "Gasto":
            raise ValueError("Selecciona una categoria de gasto.")
        if tarjeta and tarjeta.moneda.upper() != operacion.moneda.upper():
            raise ValueError(f"El aviso esta en {operacion.moneda} y la tarjeta seleccionada usa {tarjeta.moneda}.")
        if tarjeta and operacion.ultimos_cuatro and tarjeta.ultimos_cuatro != operacion.ultimos_cuatro:
            raise ValueError("Los ultimos cuatro digitos no coinciden con la tarjeta seleccionada.")
        valor = -monto_positivo(operacion.valor)
        movimiento = Movimiento(
            fecha=operacion.fecha.date(), descripcion=(descripcion or operacion.comercio)[:250], valor=valor,
            cuenta_id=cuenta.id, categoria_id=categoria.id,
            observaciones=f"Detectado desde {operacion.origen}. {operacion.texto_original[:500]}",
        )
        cuenta.saldo += valor
        self.db.add(movimiento)
        self.db.flush()
        operacion.estado = "Confirmada"
        operacion.tarjeta_id = tarjeta.id if tarjeta else None
        operacion.movimiento_id = movimiento.id
        registrar_auditoria(self.db, "OPERACION_DETECTADA_CONFIRMADA", f"Deteccion #{operacion.id} convertida en movimiento #{movimiento.id}.")
        self.db.commit()
        self.db.refresh(operacion)
        return operacion

    def pagar_tarjeta(self, tarjeta_id, cuenta_origen_id, valor, fecha, descripcion=""):
        tarjeta = self.db.get(Tarjeta, tarjeta_id)
        if tarjeta is None or not tarjeta.activa:
            raise ValueError("La tarjeta no existe o esta inactiva.")
        if tarjeta.tipo != "Credito":
            raise ValueError("Solo las tarjetas de credito generan una deuda por pagar.")
        deuda = tarjeta.cuenta
        origen = self.db.get(Cuenta, cuenta_origen_id)
        if origen is None:
            raise ValueError("La cuenta de pago no existe.")
        if not origen.activa or not deuda.activa:
            raise ValueError("La cuenta de pago o la cuenta de deuda está desactivada.")
        if origen.id == deuda.id:
            raise ValueError("Selecciona una cuenta bancaria distinta a la cuenta de deuda.")
        if origen.moneda.upper() != deuda.moneda.upper():
            raise ValueError("La cuenta de pago y la tarjeta deben usar la misma moneda.")
        monto = monto_positivo(valor)
        saldo_pendiente = abs(min(deuda.saldo, 0))
        if saldo_pendiente <= 0:
            raise ValueError("Esta tarjeta no tiene deuda pendiente.")
        if monto > saldo_pendiente:
            raise ValueError(f"El pago supera la deuda pendiente de {saldo_pendiente:.2f} {deuda.moneda}.")
        return TransferService(self.db).crear_transferencia(
            fecha, origen.id, deuda.id, monto, descripcion or f"Pago de {tarjeta.nombre}"
        )

    def _extraer(self, texto):
        normal = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
        tipo = "Credito" if re.search(r"credito|t\.c\.?", normal) else "Debito" if re.search(r"debito|t\.d\.?", normal) else None
        ultimos = re.findall(r"(?:terminada|finalizada|tarjeta|\*{2,}|x{2,})\D{0,12}(\d{4})", normal)
        moneda = "USD" if re.search(r"\busd\b|us\$|dolares?", normal) else "COP"
        patrones = [r"(?:cop|\$)\s*([\d.,]+)", r"(?:valor|compra|monto|por)\D{0,12}([\d][\d.,]+)"]
        candidatos = []
        for patron in patrones:
            for valor in re.findall(patron, normal):
                numero = self._numero(valor)
                if numero > 0:
                    candidatos.append(numero)
        if not candidatos:
            raise ValueError("No pude identificar el valor. Incluye el monto con $ o COP.")
        comercio = "Compra detectada"
        match = re.search(r"(?:en|comercio|establecimiento)\s+([\w .&-]{3,50}?)(?:\s+(?:por|el|con|tarjeta|a las)|[,.]|$)", normal)
        if match:
            comercio = match.group(1).strip().title()
        banco = next((n for n in ("Bancolombia", "Davivienda", "Nu", "Nequi", "DaviPlata", "Banco de Bogota", "AV Villas") if n.lower() in normal), "")
        return {"valor": candidatos[0], "moneda": moneda, "tipo": tipo, "ultimos_cuatro": ultimos[-1] if ultimos else None,
                "comercio": comercio, "banco": banco, "fecha": datetime.now()}

    @staticmethod
    def _numero(valor):
        limpio = valor.replace(" ", "")
        if "," in limpio and "." in limpio:
            decimal = "," if limpio.rfind(",") > limpio.rfind(".") else "."
            miles = "." if decimal == "," else ","
            limpio = limpio.replace(miles, "").replace(decimal, ".")
        elif "," in limpio:
            partes = limpio.split(",")
            limpio = "".join(partes) if len(partes[-1]) == 3 else ".".join(partes)
        elif "." in limpio and len(limpio.split(".")[-1]) == 3:
            limpio = limpio.replace(".", "")
        return float(limpio)

    @staticmethod
    def _huella(datos):
        base = "|".join([datos["banco"], datos["ultimos_cuatro"] or "", f'{datos["valor"]:.2f}', datos["moneda"], datos["comercio"].lower(), datos["fecha"].date().isoformat()])
        return hashlib.sha256(base.encode()).hexdigest()

    @staticmethod
    def _normalizar(valor):
        return unicodedata.normalize("NFKD", valor or "").encode("ascii", "ignore").decode().lower().strip()

    def cerrar(self):
        self.db.close()

"""Reglas de validacion compartidas por los servicios de FinanceOS."""

from decimal import Decimal, InvalidOperation


TIPOS_CATEGORIA = {"Ingreso", "Gasto", "Transferencia", "Ahorro", "Inversion"}
FRECUENCIAS_RECURRENCIA = {"Semanal", "Quincenal", "Mensual", "Anual"}


def texto_requerido(valor, campo, maximo):
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(f"{campo} es obligatorio.")
    if len(texto) > maximo:
        raise ValueError(f"{campo} no puede superar {maximo} caracteres.")
    return texto


LIMITE_MONETARIO = Decimal("1000000000000")


def monto_decimal(valor, campo="El valor", *, permitir_cero=False, permitir_negativo=False):
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(f"{campo} debe ser un numero valido.") from error
    if not monto.is_finite():
        raise ValueError(f"{campo} debe ser un numero finito.")
    if abs(monto) > LIMITE_MONETARIO:
        raise ValueError(f"{campo} supera el limite permitido.")
    if not permitir_negativo and monto < 0:
        raise ValueError(f"{campo} no puede ser negativo.")
    if not permitir_cero and monto == 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return monto


def monto_positivo(valor, campo="El valor"):
    return monto_decimal(valor, campo)


def moneda_valida(moneda):
    codigo = str(moneda or "").strip().upper()
    if len(codigo) != 3 or not codigo.isalpha():
        raise ValueError("La moneda debe usar un codigo ISO de tres letras, por ejemplo COP o USD.")
    return codigo


def periodo_valido(anio, mes):
    try:
        anio, mes = int(anio), int(mes)
    except (TypeError, ValueError) as error:
        raise ValueError("El periodo del presupuesto no es valido.") from error
    if not 2000 <= anio <= 2100 or not 1 <= mes <= 12:
        raise ValueError("El periodo del presupuesto no es valido.")
    return anio, mes

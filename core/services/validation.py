"""Reglas de validacion compartidas por los servicios de FinanceOS."""


TIPOS_CATEGORIA = {"Ingreso", "Gasto", "Transferencia", "Ahorro", "Inversion"}
FRECUENCIAS_RECURRENCIA = {"Semanal", "Quincenal", "Mensual", "Anual"}


def texto_requerido(valor, campo, maximo):
    texto = str(valor or "").strip()
    if not texto:
        raise ValueError(f"{campo} es obligatorio.")
    if len(texto) > maximo:
        raise ValueError(f"{campo} no puede superar {maximo} caracteres.")
    return texto


def monto_positivo(valor, campo="El valor"):
    try:
        monto = abs(float(valor))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{campo} debe ser un numero valido.") from error
    if monto <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    return monto


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

"""Utilidad de auditoría para registrar acciones dentro de la misma transacción."""

from core.models import Auditoria


def registrar_auditoria(db, accion, descripcion):
    """Agrega un evento de auditoría sin confirmar la transacción.

    El servicio que realiza la operación conserva el control del ``commit``;
    así el cambio y su registro se guardan o se revierten juntos.
    """
    db.add(Auditoria(accion=accion, descripcion=descripcion))

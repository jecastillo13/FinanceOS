"""Aislamiento transparente de registros por el usuario autenticado."""

from contextvars import ContextVar

from sqlalchemy import Column, ForeignKey, Integer, event
from sqlalchemy.orm import Session, declared_attr, with_loader_criteria


usuario_actual_id: ContextVar[int | None] = ContextVar("financeos_usuario_id", default=None)

TABLAS_CON_PROPIETARIO = (
    "cuentas", "categorias", "movimientos", "tarjetas", "operaciones_detectadas",
    "adjuntos_movimiento", "gastos_recurrentes", "transferencias", "presupuestos",
    "metas", "meta_operaciones", "inversiones", "auditoria",
)


class PropiedadUsuario:
    """Mixin para entidades financieras que pertenecen a un usuario."""

    @declared_attr
    def usuario_id(cls):
        # El valor 1 mantiene compatibles las herramientas locales y pruebas
        # que se ejecutan sin una petición HTTP; la API siempre impone el
        # usuario autenticado mediante ContextVar antes de crear registros.
        return Column(
            Integer, ForeignKey("usuarios.id"), nullable=False, index=True,
            default=lambda: usuario_actual_id.get() or 1,
        )


@event.listens_for(Session, "do_orm_execute")
def _filtrar_consultas_por_usuario(execute_state):
    propietario = usuario_actual_id.get()
    if propietario is None or not execute_state.is_select:
        return
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            PropiedadUsuario,
            lambda entidad: entidad.usuario_id == propietario,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def _asignar_propietario(_session, _flush_context, _instances):
    propietario = usuario_actual_id.get()
    if propietario is None:
        return
    for objeto in _session.new:
        if isinstance(objeto, PropiedadUsuario) and objeto.usuario_id is None:
            objeto.usuario_id = propietario

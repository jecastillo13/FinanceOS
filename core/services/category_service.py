from core.database import get_session
from core.models import Categoria
from core.default_categories import CATEGORIAS_PREDETERMINADAS, COLORES_POR_TIPO
from core.services.audit_service import registrar_auditoria
from core.services.validation import TIPOS_CATEGORIA, texto_requerido


class CategoryService:

    def __init__(self):
        self.db = get_session()

    # =====================================================
    # CRUD
    # =====================================================

    def obtener_categorias(self):

        return (
            self.db.query(Categoria)
            .order_by(
                Categoria.tipo,
                Categoria.grupo,
                Categoria.orden,
                Categoria.nombre
            )
            .all()
        )

    def obtener_categoria(self, categoria_id):

        return self.db.get(
            Categoria,
            categoria_id
        )

    def crear_categoria(
        self,
        nombre,
        tipo,
        color="#4CAF50",
        icono="🏷️",
        grupo="Otros",
        es_sistema=False,
        orden=0,
    ):

        nombre = texto_requerido(nombre, "El nombre de la categoria", 80)
        if tipo not in TIPOS_CATEGORIA:
            raise ValueError("El tipo de categoria no es valido.")
        if self.db.query(Categoria).filter(Categoria.nombre.ilike(nombre), Categoria.tipo == tipo).first():
            raise ValueError("Ya existe una categoria con ese nombre y tipo.")

        categoria = Categoria(
            nombre=nombre,
            tipo=tipo,
            color=color,
            icono=icono,
            grupo=grupo,
            es_sistema=1 if es_sistema else 0,
            orden=orden,
        )

        self.db.add(categoria)
        registrar_auditoria(self.db, "CATEGORIA_CREADA", f"Categoria creada: {nombre} ({tipo}).")
        self.db.commit()
        self.db.refresh(categoria)

        return categoria

    def instalar_categorias_predeterminadas(self):
        """Instala el catálogo sin duplicar categorías ya existentes."""
        existentes = {
            (categoria.nombre.lower(), categoria.tipo)
            for categoria in self.db.query(Categoria).all()
        }
        creadas = 0

        for orden, (tipo, grupo, icono, nombre) in enumerate(CATEGORIAS_PREDETERMINADAS, start=1):
            clave = (nombre.lower(), tipo)
            if clave in existentes:
                continue

            self.db.add(Categoria(
                nombre=nombre,
                tipo=tipo,
                color=COLORES_POR_TIPO[tipo],
                icono=icono,
                grupo=grupo,
                es_sistema=1,
                editable=1,
                activa=1,
                orden=orden,
            ))
            creadas += 1

        if creadas:
            registrar_auditoria(self.db, "CATALOGO_INSTALADO", f"Se instalaron {creadas} categorias predeterminadas.")
        self.db.commit()
        return creadas

    def actualizar_categoria(
        self,
        categoria_id,
        nombre,
        tipo,
        color,
        icono="🏷️",
        grupo="Otros",
        activa=True,
        orden=0,
    ):

        categoria = self.db.get(
            Categoria,
            categoria_id
        )

        if categoria is None:
            return None

        nombre = texto_requerido(nombre, "El nombre de la categoria", 80)
        if tipo not in TIPOS_CATEGORIA:
            raise ValueError("El tipo de categoria no es valido.")
        duplicada = (
            self.db.query(Categoria)
            .filter(Categoria.nombre.ilike(nombre), Categoria.tipo == tipo, Categoria.id != categoria_id)
            .first()
        )
        if duplicada:
            raise ValueError("Ya existe una categoria con ese nombre y tipo.")

        if categoria.movimientos and categoria.tipo != tipo:
            raise ValueError("No puedes cambiar el tipo de una categoría que ya tiene movimientos.")

        categoria.nombre = nombre
        categoria.tipo = tipo
        categoria.color = color
        categoria.icono = icono
        categoria.grupo = grupo
        categoria.activa = 1 if activa else 0
        categoria.orden = orden

        registrar_auditoria(self.db, "CATEGORIA_ACTUALIZADA", f"Categoria #{categoria.id} actualizada: {nombre} ({tipo}).")
        self.db.commit()
        self.db.refresh(categoria)

        return categoria

    def eliminar_categoria(
        self,
        categoria_id
    ):

        categoria = self.db.get(
            Categoria,
            categoria_id
        )

        if categoria is None:
            return False

        if categoria.movimientos:
            return False

        registrar_auditoria(self.db, "CATEGORIA_ELIMINADA", f"Categoria #{categoria.id} eliminada: {categoria.nombre}.")
        self.db.delete(categoria)
        self.db.commit()

        return True

    # =====================================================
    # MÉTRICAS
    # =====================================================

    def total_categorias(self):

        return (
            self.db.query(Categoria)
            .count()
        )

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.db.close()

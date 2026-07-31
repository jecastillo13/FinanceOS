from core.database import get_session
from core.models import Categoria
from core.default_categories import CATEGORIAS_PREDETERMINADAS, COLORES_POR_TIPO


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

        if categoria.movimientos and categoria.tipo != tipo:
            raise ValueError("No puedes cambiar el tipo de una categoría que ya tiene movimientos.")

        categoria.nombre = nombre
        categoria.tipo = tipo
        categoria.color = color
        categoria.icono = icono
        categoria.grupo = grupo
        categoria.activa = 1 if activa else 0
        categoria.orden = orden

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

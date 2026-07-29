from core.database import get_session
from core.models import Categoria


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
        color="#4CAF50"
    ):

        categoria = Categoria(
            nombre=nombre,
            tipo=tipo,
            color=color
        )

        self.db.add(categoria)
        self.db.commit()
        self.db.refresh(categoria)

        return categoria

    def actualizar_categoria(
        self,
        categoria_id,
        nombre,
        tipo,
        color
    ):

        categoria = self.db.get(
            Categoria,
            categoria_id
        )

        if categoria is None:
            return None

        categoria.nombre = nombre
        categoria.tipo = tipo
        categoria.color = color

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
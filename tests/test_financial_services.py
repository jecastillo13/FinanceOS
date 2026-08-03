import os
import tempfile
import unittest
from datetime import date
from pathlib import Path


_TEST_DIR = tempfile.TemporaryDirectory(prefix="financeos_tests_")
_TEST_DATABASE = Path(_TEST_DIR.name) / "financeos_test.db"
os.environ["FINANCEOS_DATABASE_URL"] = f"sqlite:///{_TEST_DATABASE.as_posix()}"

from sqlalchemy import text  # noqa: E402

from core.database import Base, create_database, engine, get_session  # noqa: E402
from core.models import Categoria  # noqa: E402
from core.services import (  # noqa: E402
    AccountService,
    MovementService,
    RecurringExpenseService,
    TransferService,
)


class FinancialServicesTest(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        _TEST_DIR.cleanup()

    def setUp(self):
        Base.metadata.drop_all(bind=engine)
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS schema_migrations"))
        create_database()
        self.ingreso_id, self.gasto_id = self._crear_categorias()

    @staticmethod
    def _crear_categorias():
        session = get_session()
        try:
            ingreso = Categoria(nombre="Salario prueba", tipo="Ingreso", grupo="Pruebas")
            gasto = Categoria(nombre="Mercado prueba", tipo="Gasto", grupo="Pruebas")
            session.add_all([ingreso, gasto])
            session.commit()
            return ingreso.id, gasto.id
        finally:
            session.close()

    def _crear_cuenta(self, nombre="Cuenta prueba", saldo=1000):
        service = AccountService()
        try:
            return service.crear_cuenta(nombre, "Ahorros", saldo, "COP").id
        finally:
            service.cerrar()

    def _saldo(self, cuenta_id):
        service = AccountService()
        try:
            return service.obtener_cuenta(cuenta_id).saldo
        finally:
            service.cerrar()

    def test_ingreso_y_gasto_actualizan_el_saldo(self):
        cuenta_id = self._crear_cuenta()
        service = MovementService()
        try:
            service.registrar_movimiento(date.today(), "Ingreso prueba", 500, cuenta_id, self.ingreso_id)
            service.registrar_movimiento(date.today(), "Gasto prueba", 125, cuenta_id, self.gasto_id)
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(cuenta_id), 1375)

    def test_eliminar_movimiento_restaura_el_saldo(self):
        cuenta_id = self._crear_cuenta()
        service = MovementService()
        try:
            movimiento = service.registrar_movimiento(date.today(), "Gasto reversible", 250, cuenta_id, self.gasto_id)
            service.eliminar_movimiento(movimiento.id)
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(cuenta_id), 1000)

    def test_transferencia_conserva_el_saldo_total(self):
        origen_id = self._crear_cuenta("Origen", 1000)
        destino_id = self._crear_cuenta("Destino", 200)
        service = TransferService()
        try:
            service.crear_transferencia(date.today(), origen_id, destino_id, 300, "Prueba")
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(origen_id), 700)
        self.assertEqual(self._saldo(destino_id), 500)
        self.assertEqual(self._saldo(origen_id) + self._saldo(destino_id), 1200)

    def test_pago_recurrente_crea_gasto_y_avanza_fecha(self):
        cuenta_id = self._crear_cuenta(saldo=1000)
        service = RecurringExpenseService()
        try:
            gasto = service.crear_gasto("Internet prueba", 100, "Mensual", date.today(), self.gasto_id)
            movimiento = service.pagar(gasto.id, cuenta_id, date.today())
            siguiente_fecha = gasto.proxima_fecha_pago
        finally:
            service.cerrar()

        self.assertEqual(movimiento.valor, -100)
        self.assertEqual(self._saldo(cuenta_id), 900)
        self.assertGreater(siguiente_fecha, date.today())


if __name__ == "__main__":
    unittest.main()

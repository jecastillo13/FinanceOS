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
    BackupService,
    DashboardService,
    GoalService,
    InvestmentService,
    MovementService,
    RecurringExpenseService,
    ReportService,
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
            transferencia = service.crear_transferencia(date.today(), origen_id, destino_id, 300, "Prueba")
            transferencia_id = transferencia.id
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(origen_id), 700)
        self.assertEqual(self._saldo(destino_id), 500)
        self.assertEqual(self._saldo(origen_id) + self._saldo(destino_id), 1200)

        service = TransferService()
        try:
            self.assertTrue(service.eliminar_transferencia(transferencia_id))
        finally:
            service.cerrar()
        self.assertEqual(self._saldo(origen_id), 1000)
        self.assertEqual(self._saldo(destino_id), 200)

    def test_editar_movimiento_entre_cuentas_recalcula_ambos_saldos(self):
        origen_id = self._crear_cuenta("Cuenta anterior", 1000)
        destino_id = self._crear_cuenta("Cuenta nueva", 500)
        service = MovementService()
        try:
            movimiento = service.registrar_movimiento(date.today(), "Compra inicial", 100, origen_id, self.gasto_id)
            service.actualizar_movimiento(
                movimiento.id,
                date.today(),
                "Compra corregida",
                250,
                destino_id,
                self.gasto_id,
            )
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(origen_id), 1000)
        self.assertEqual(self._saldo(destino_id), 250)

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

    def test_eliminar_meta_restaura_pagos_vinculados(self):
        cuenta_id = self._crear_cuenta(saldo=1000)
        service = GoalService()
        try:
            meta = service.crear_meta("Viaje prueba", 500, "COP")
            service.aportar(meta.id, 100, date.today(), "Reserva")
            service.registrar_pago(meta.id, date.today(), cuenta_id, self.gasto_id, 200, "Pago del viaje")
            self.assertEqual(self._saldo(cuenta_id), 800)
            self.assertTrue(service.eliminar_meta(meta.id))
            self.assertIsNone(service.obtener_meta(meta.id))
        finally:
            service.cerrar()

        self.assertEqual(self._saldo(cuenta_id), 1000)

    def test_inversion_calcula_valor_y_rentabilidad(self):
        service = InvestmentService()
        try:
            inversion = service.crear_inversion("ETF prueba", "ETF", 10, 100, 120, "Broker", "COP")
            resumen = service.resumen("COP")
            self.assertEqual(resumen["costo_total"], 1000)
            self.assertEqual(resumen["valor_total"], 1200)
            self.assertEqual(resumen["ganancia_total"], 200)
            self.assertEqual(resumen["rentabilidad"], 20)
            self.assertTrue(service.eliminar_inversion(inversion.id))
        finally:
            service.cerrar()

    def test_inversion_acepta_montos_totales_del_broker(self):
        service = InvestmentService()
        try:
            inversion = service.crear_inversion(
                "SCHD prueba",
                "ETF",
                15.47671,
                452.89,
                518.77,
                "Broker",
                "USD",
                valores_totales=True,
            )
            posicion = service.resumen_posicion(inversion, "USD")
        finally:
            service.cerrar()

        self.assertAlmostEqual(posicion["costo"], 452.89, places=2)
        self.assertAlmostEqual(posicion["valor"], 518.77, places=2)
        self.assertAlmostEqual(posicion["ganancia"], 65.88, places=2)

    def test_dashboard_suma_cuentas_e_inversiones_al_patrimonio(self):
        self._crear_cuenta(saldo=1000)
        inversiones = InvestmentService()
        try:
            inversiones.crear_inversion("ETF patrimonio", "ETF", 2, 100, 150, "Broker", "COP")
        finally:
            inversiones.cerrar()

        dashboard = DashboardService()
        try:
            resumen = dashboard.resumen()
        finally:
            dashboard.cerrar()

        self.assertEqual(resumen["cuentas_cop"], 1000)
        self.assertEqual(resumen["inversiones_cop"], 300)
        self.assertEqual(resumen["patrimonio"], 1300)

    def test_reporte_mensual_resume_y_exporta_movimientos(self):
        cuenta_id = self._crear_cuenta()
        movimientos = MovementService()
        try:
            movimientos.registrar_movimiento(date.today(), "Nómina reporte", 500, cuenta_id, self.ingreso_id)
            movimientos.registrar_movimiento(date.today(), "Mercado reporte", 125, cuenta_id, self.gasto_id)
        finally:
            movimientos.cerrar()

        reportes = ReportService()
        try:
            reporte = reportes.obtener_reporte(date.today().year, date.today().month)
            csv = reportes.generar_csv(reporte).decode("utf-8-sig")
        finally:
            reportes.cerrar()

        self.assertEqual(reporte["ingresos_cop"], 500)
        self.assertEqual(reporte["gastos_cop"], 125)
        self.assertEqual(reporte["balance_cop"], 375)
        self.assertIn("Nómina reporte", csv)
        self.assertIn("Mercado reporte", csv)

    def test_respaldo_incluye_base_y_manifiesto(self):
        from io import BytesIO
        from zipfile import ZipFile

        self._crear_cuenta()
        contenido = BackupService().crear_respaldo()
        with ZipFile(BytesIO(contenido)) as archivo:
            self.assertIn("database/finance.db", archivo.namelist())
            self.assertIn("manifest.json", archivo.namelist())

    def test_restaurar_respaldo_recupera_datos(self):
        cuenta_id = self._crear_cuenta("Cuenta para restaurar", 4321)
        respaldos = BackupService()
        contenido = respaldos.crear_respaldo()

        cuentas = AccountService()
        try:
            self.assertTrue(cuentas.eliminar_cuenta(cuenta_id))
        finally:
            cuentas.cerrar()

        respaldo_previo = respaldos.restaurar(contenido)
        cuentas = AccountService()
        try:
            restaurada = cuentas.obtener_cuentas()
        finally:
            cuentas.cerrar()

        self.assertTrue(respaldo_previo.is_file())
        self.assertIn("Cuenta para restaurar", [cuenta.nombre for cuenta in restaurada])


if __name__ == "__main__":
    unittest.main()

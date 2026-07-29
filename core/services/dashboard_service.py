from core.services.account_service import AccountService
from core.services.movement_service import MovementService


class DashboardService:

    def __init__(self):

        self.account_service = AccountService()
        self.movement_service = MovementService()

    # =====================================================
    # KPIs
    # =====================================================

    def patrimonio(self):

        return self.account_service.saldo_total()

    def cuentas(self):

        return self.account_service.total_cuentas()

    def ingresos(self):

        return self.movement_service.ingresos_totales()

    def gastos(self):

        return self.movement_service.gastos_totales()

    def inversiones(self):

        # Próximamente
        return 0

    def metas(self):

        # Próximamente
        return 0

    # =====================================================
    # RESUMEN
    # =====================================================

    def resumen(self):

        return {
            "patrimonio": self.patrimonio(),
            "cuentas": self.cuentas(),
            "ingresos": self.ingresos(),
            "gastos": self.gastos(),
            "inversiones": self.inversiones(),
            "metas": self.metas()
        }

    # =====================================================
    # UTILIDADES
    # =====================================================

    def cerrar(self):

        self.account_service.cerrar()
        self.movement_service.cerrar()
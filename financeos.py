import streamlit as st

from core.database import create_database

from components.sidebar import mostrar

from components.ui.css import load_css
from components.ui.topbar import topbar

from modules import dashboard
from modules import cuentas
from modules import categorias
from modules import movimientos
from modules import monedas
from modules import gastos_recurrentes
from modules import transferencias
from modules import presupuestos
from modules import metas
from modules import inversiones


# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="FinanceOS",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# ESTILOS
# =====================================================

load_css()

# =====================================================
# BASE DE DATOS
# =====================================================

@st.cache_resource
def inicializar_base_datos():
    """Evita revisar el esquema de SQLite en cada interacción de Streamlit."""
    create_database()
    return True


inicializar_base_datos()

# =====================================================
# SIDEBAR
# =====================================================

pagina = mostrar()

# =====================================================
# TOPBAR
# =====================================================

topbar()

# =====================================================
# PÁGINAS
# =====================================================

if pagina == "🏠 Dashboard":

    dashboard.mostrar()

elif pagina == "🏦 Cuentas":

    cuentas.mostrar()

elif pagina == "🏷️ Categorías":

    categorias.mostrar()

elif pagina == "💸 Movimientos":

    movimientos.mostrar()

elif pagina == "🔁 Gastos recurrentes":

    gastos_recurrentes.mostrar()

elif pagina == "🔄 Transferencias":

    transferencias.mostrar()

elif pagina == "📊 Presupuestos":

    presupuestos.mostrar()

elif pagina == "🌎 Monedas":

    monedas.mostrar()

elif pagina == "🎯 Metas":

    metas.mostrar()

elif pagina == "📈 Inversiones":

    inversiones.mostrar()

elif pagina == "📑 Reportes":

    st.title("📊 Reportes")
    st.info("Próximamente")

elif pagina == "⚙️ Configuración":

    st.title("⚙ Configuración")
    st.info("Próximamente")

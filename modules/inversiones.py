import streamlit as st

from components.dialogs.delete_confirmation import confirm_delete
from components.ui.page import page_header
from core.services import InvestmentService


TIPOS = ["ETF", "Acción", "Criptomoneda", "CDT", "Fondo", "Bono", "Otro"]
MONEDAS = ["COP", "USD", "EUR"]


def _dinero(valor, moneda):
    return f"{moneda} {valor:,.2f}"


@st.dialog("✏️ Editar inversión")
def editar_inversion(inversion_id):
    service = InvestmentService()
    try:
        inversion = service.obtener_inversion(inversion_id)
        if inversion is None:
            st.error("La inversión ya no existe.")
            return
        modo = st.radio(
            "¿Cómo quieres ingresar los valores?",
            ["Valores totales", "Precios por unidad"],
            horizontal=True,
            help="Usa valores totales si tu broker muestra monto invertido y valor de mercado.",
            key=f"modo_editar_inversion_{inversion_id}",
        )
        valores_totales = modo == "Valores totales"
        with st.form(f"editar_inversion_{inversion_id}"):
            activo = st.text_input("Activo", value=inversion.activo)
            tipo = st.selectbox("Tipo", TIPOS, index=TIPOS.index(inversion.tipo) if inversion.tipo in TIPOS else len(TIPOS) - 1)
            columna_1, columna_2 = st.columns(2)
            with columna_1:
                cantidad = st.number_input("Cantidad", min_value=0.00000001, value=float(inversion.cantidad), format="%.8f")
                compra_inicial = inversion.cantidad * inversion.precio_compra if valores_totales else inversion.precio_compra
                precio_compra = st.number_input("Monto invertido total" if valores_totales else "Precio promedio por unidad", min_value=0.00000001, value=float(compra_inicial), format="%.8f")
            with columna_2:
                actual_inicial = inversion.cantidad * inversion.precio_actual if valores_totales else inversion.precio_actual
                precio_actual = st.number_input("Valor de mercado total" if valores_totales else "Precio actual por unidad", min_value=0.00000001, value=float(actual_inicial), format="%.8f")
                moneda = st.selectbox("Moneda", MONEDAS, index=MONEDAS.index(inversion.moneda) if inversion.moneda in MONEDAS else 0)
            broker = st.text_input("Broker o plataforma", value=inversion.broker or "")
            if st.form_submit_button("Guardar cambios", use_container_width=True):
                try:
                    service.actualizar_inversion(inversion_id, activo=activo, tipo=tipo, cantidad=cantidad, precio_compra=precio_compra, precio_actual=precio_actual, broker=broker, moneda=moneda, valores_totales=valores_totales)
                    st.success("Inversión actualizada.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
    finally:
        service.cerrar()


def mostrar():
    page_header("📈", "Inversiones", "Controla tus posiciones, valoración y rentabilidad consolidada en pesos.", "PATRIMONIO")
    service = InvestmentService()
    try:
        inversiones = service.obtener_inversiones()
        with st.expander("➕ Nueva inversión", expanded=not bool(inversiones)):
            modo = st.radio(
                "¿Qué valores muestra tu broker?",
                ["Valores totales", "Precios por unidad"],
                horizontal=True,
                help="Ejemplo total: invertido USD 452.89 y valor de mercado USD 518.77.",
                key="modo_crear_inversion",
            )
            valores_totales = modo == "Valores totales"
            with st.form("crear_inversion", clear_on_submit=True):
                columna_1, columna_2 = st.columns(2)
                with columna_1:
                    activo = st.text_input("Activo", placeholder="Ej: VOO, AAPL, Bitcoin o CDT")
                    tipo = st.selectbox("Tipo", TIPOS)
                    cantidad = st.number_input("Cantidad", min_value=0.00000001, value=1.0, format="%.8f")
                with columna_2:
                    precio_compra = st.number_input("Monto invertido total" if valores_totales else "Precio promedio por unidad", min_value=0.00000001, value=1.0, format="%.8f")
                    precio_actual = st.number_input("Valor de mercado total" if valores_totales else "Precio actual por unidad", min_value=0.00000001, value=1.0, format="%.8f")
                    moneda = st.selectbox("Moneda", MONEDAS, index=1)
                broker = st.text_input("Broker o plataforma", placeholder="Ej: Hapi, Trii, Binance o banco")
                if st.form_submit_button("Guardar inversión", use_container_width=True):
                    try:
                        service.crear_inversion(activo, tipo, cantidad, precio_compra, precio_actual, broker, moneda, valores_totales=valores_totales)
                        st.success("Inversión registrada.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        resumen = service.resumen("COP")
        st.divider()
        columna_1, columna_2, columna_3, columna_4 = st.columns(4)
        columna_1.metric("Valor actual", _dinero(resumen["valor_total"], "COP"))
        columna_2.metric("Capital invertido", _dinero(resumen["costo_total"], "COP"))
        columna_3.metric("Ganancia / pérdida", _dinero(resumen["ganancia_total"], "COP"))
        columna_4.metric("Rentabilidad", f"{resumen['rentabilidad']:.2f}%")

        if resumen["sin_tasa"]:
            monedas = sorted({inversion.moneda for inversion in resumen["sin_tasa"]})
            st.warning(f"Faltan tasas para consolidar: {', '.join(monedas)}. Actualízalas en Monedas.")

        if not resumen["posiciones"]:
            st.info("Registra tu primera inversión para comenzar a medir tu portafolio.")
            return

        st.subheader("Portafolio")
        for item in resumen["posiciones"]:
            inversion = item["inversion"]
            estado = "🟢" if item["ganancia"] >= 0 else "🔴"
            with st.expander(f"{estado} {inversion.activo} · {inversion.tipo} · {item['rentabilidad']:.2f}%"):
                col_1, col_2, col_3 = st.columns(3)
                col_1.metric("Valor actual", _dinero(item["valor"], inversion.moneda))
                col_2.metric("Costo", _dinero(item["costo"], inversion.moneda))
                col_3.metric("Ganancia / pérdida", _dinero(item["ganancia"], inversion.moneda))
                st.caption(f"Cantidad: {inversion.cantidad:,.8f} · Broker: {inversion.broker or 'Sin especificar'} · Moneda: {inversion.moneda}")
                editar, eliminar = st.columns(2)
                if editar.button("Editar", key=f"editar_inversion_{inversion.id}", use_container_width=True):
                    editar_inversion(inversion.id)
                if eliminar.button("Eliminar", key=f"eliminar_inversion_{inversion.id}", use_container_width=True):
                    confirm_delete("¿Eliminar inversión?", f"{inversion.activo} · {inversion.tipo}", "Se eliminará la posición del portafolio. Los movimientos financieros permanecerán intactos.", lambda inversion_id=inversion.id: service.eliminar_inversion(inversion_id), "Inversión eliminada.")
    finally:
        service.cerrar()

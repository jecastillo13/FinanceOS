import streamlit as st

from core.services import ExchangeService


def mostrar():

    st.title("🌎 Monedas y Tasas de Cambio")

    service = ExchangeService()

    # ==========================================
    # ACTUALIZAR
    # ==========================================

    col1, col2 = st.columns([1, 3])

    with col1:

        if st.button("🔄 Actualizar tasas"):

            with st.spinner("Consultando tasas..."):

                ok = service.actualizar_tasas()

                if ok:
                    st.success("Tasas actualizadas correctamente.")
                else:
                    st.error("No fue posible actualizar las tasas.")

    with col2:

        fecha = service.ultima_actualizacion()

        if fecha:
            st.info(f"Última actualización: {fecha.strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            st.warning("Aún no existen tasas almacenadas.")

    st.divider()

    # ==========================================
    # TASA USD -> COP
    # ==========================================

    tasa = service.obtener_tasa("USD", "COP")

    if tasa:

        st.metric(
            "USD → COP",
            f"${tasa:,.2f}"
        )

    st.divider()

    # ==========================================
    # CONVERSOR
    # ==========================================

    st.subheader("Conversor")

    col1, col2, col3 = st.columns(3)

    with col1:

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=100.0
        )

    monedas = [
        "COP",
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "BRL",
        "MXN",
        "CAD",
        "AUD"
    ]

    with col2:

        origen = st.selectbox(
            "Origen",
            monedas,
            index=1
        )

    with col3:

        destino = st.selectbox(
            "Destino",
            monedas,
            index=0
        )

    if st.button("Convertir"):

        resultado = service.convertir(
            valor,
            origen,
            destino
        )

        if resultado is None:

            st.error("No existe una tasa para esa conversión.")

        else:

            st.success(
                f"{valor:,.2f} {origen} = {resultado:,.2f} {destino}"
            )

    st.divider()

    # ==========================================
    # TABLA
    # ==========================================

    st.subheader("Tasas almacenadas")

    tasas = service.obtener_tasas()

    if tasas:

        datos = []

        for t in tasas:

            datos.append(
                {
                    "Origen": t.moneda_origen,
                    "Destino": t.moneda_destino,
                    "Tasa": t.tasa,
                    "Fuente": t.fuente,
                    "Actualizada": t.fecha_actualizacion
                }
            )

        st.dataframe(
            datos,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No existen tasas almacenadas.")

    service.cerrar()
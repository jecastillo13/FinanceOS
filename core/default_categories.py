COLORES_POR_TIPO = {
    "Ingreso": "#16A34A",
    "Gasto": "#DC2626",
    "Transferencia": "#2563EB",
    "Ahorro": "#7C3AED",
    "Inversion": "#D97706",
}


# tipo, grupo, icono, nombre
CATEGORIAS_PREDETERMINADAS = [
    ("Ingreso", "Trabajo", "💼", "Salario"), ("Ingreso", "Trabajo", "💵", "Bonificaciones"),
    ("Ingreso", "Trabajo", "🕒", "Horas extra"), ("Ingreso", "Trabajo", "🎁", "Primas"), ("Ingreso", "Trabajo", "💰", "Comisiones"),
    ("Ingreso", "Inversiones", "📈", "Dividendos"), ("Ingreso", "Inversiones", "💲", "Intereses"), ("Ingreso", "Inversiones", "🪙", "Criptomonedas"),
    ("Ingreso", "Inversiones", "📊", "Venta de acciones"), ("Ingreso", "Inversiones", "💹", "Ganancias por inversiones"),
    ("Ingreso", "Negocios", "🏪", "Ventas"), ("Ingreso", "Negocios", "🧾", "Servicios profesionales"), ("Ingreso", "Negocios", "💻", "Freelance"), ("Ingreso", "Negocios", "🛍", "Emprendimiento"),
    ("Ingreso", "Otros ingresos", "🎁", "Regalos recibidos"), ("Ingreso", "Otros ingresos", "💸", "Reembolsos"), ("Ingreso", "Otros ingresos", "🏦", "Devoluciones bancarias"),
    ("Ingreso", "Otros ingresos", "💵", "Préstamos recibidos"), ("Ingreso", "Otros ingresos", "❓", "Otros ingresos"),
    ("Gasto", "Vivienda", "🏠", "Arriendo"), ("Gasto", "Vivienda", "🛠", "Administración"), ("Gasto", "Vivienda", "⚡", "Energía"), ("Gasto", "Vivienda", "💧", "Agua"), ("Gasto", "Vivienda", "🔥", "Gas"), ("Gasto", "Vivienda", "🌐", "Internet"), ("Gasto", "Vivienda", "📺", "TV"), ("Gasto", "Vivienda", "📱", "Celular"),
    ("Gasto", "Alimentación", "🛒", "Mercado"), ("Gasto", "Alimentación", "🍔", "Restaurantes"), ("Gasto", "Alimentación", "☕", "Cafeterías"), ("Gasto", "Alimentación", "🥤", "Snacks"),
    ("Gasto", "Transporte", "⛽", "Combustible"), ("Gasto", "Transporte", "🚗", "Parqueaderos"), ("Gasto", "Transporte", "🛣", "Peajes"), ("Gasto", "Transporte", "🚕", "Taxi"), ("Gasto", "Transporte", "🚍", "Transporte público"), ("Gasto", "Transporte", "🚲", "Bicicleta"), ("Gasto", "Transporte", "🔧", "Mantenimiento vehículo"),
    ("Gasto", "Salud", "🏥", "Medicina"), ("Gasto", "Salud", "💊", "Medicamentos"), ("Gasto", "Salud", "🦷", "Odontología"), ("Gasto", "Salud", "🩺", "Exámenes médicos"), ("Gasto", "Salud", "❤️", "Seguro médico"),
    ("Gasto", "Educación", "📚", "Libros"), ("Gasto", "Educación", "🎓", "Universidad"), ("Gasto", "Educación", "💻", "Cursos"), ("Gasto", "Educación", "📖", "Certificaciones"),
    ("Gasto", "Finanzas", "💳", "Tarjetas de crédito"), ("Gasto", "Finanzas", "🏦", "Créditos"), ("Gasto", "Finanzas", "💸", "Intereses pagados"), ("Gasto", "Finanzas", "🏛", "Impuestos"), ("Gasto", "Finanzas", "💰", "Comisiones bancarias"),
    ("Gasto", "Compras", "👕", "Ropa"), ("Gasto", "Compras", "👟", "Calzado"), ("Gasto", "Compras", "💄", "Cuidado personal"), ("Gasto", "Compras", "📱", "Tecnología"), ("Gasto", "Compras", "🛋", "Hogar"),
    ("Gasto", "Entretenimiento", "🎬", "Cine"), ("Gasto", "Entretenimiento", "🍺", "Salidas"), ("Gasto", "Entretenimiento", "🎮", "Videojuegos"), ("Gasto", "Entretenimiento", "🎵", "Música"), ("Gasto", "Entretenimiento", "🎟", "Eventos"),
    ("Gasto", "Deportes", "🚴", "Ciclismo"), ("Gasto", "Deportes", "🏋️", "Gimnasio"), ("Gasto", "Deportes", "👕", "Ropa deportiva"), ("Gasto", "Deportes", "🥤", "Nutrición deportiva"), ("Gasto", "Deportes", "🛠", "Mantenimiento bicicleta"), ("Gasto", "Deportes", "🚵", "Competencias"), ("Gasto", "Deportes", "🎽", "Inscripciones"), ("Gasto", "Deportes", "🛞", "Repuestos bicicleta"),
    ("Gasto", "Mascotas", "🐶", "Alimentación"), ("Gasto", "Mascotas", "🩺", "Veterinario"), ("Gasto", "Mascotas", "🎾", "Accesorios"),
    ("Gasto", "Viajes", "✈️", "Vuelos"), ("Gasto", "Viajes", "🏨", "Hoteles"), ("Gasto", "Viajes", "🚗", "Transporte"), ("Gasto", "Viajes", "🍽", "Alimentación"), ("Gasto", "Viajes", "🎟", "Turismo"),
    ("Gasto", "Familia", "👨‍👩‍👧", "Ayuda familiar"), ("Gasto", "Familia", "🎁", "Regalos"), ("Gasto", "Familia", "🎉", "Celebraciones"),
    ("Gasto", "Seguros", "🚗", "Seguro vehículo"), ("Gasto", "Seguros", "❤️", "Seguro de vida"), ("Gasto", "Seguros", "🏥", "Seguro salud"), ("Gasto", "Seguros", "🏠", "Seguro hogar"),
    ("Gasto", "Suscripciones", "🎬", "Netflix"), ("Gasto", "Suscripciones", "🎵", "Spotify"), ("Gasto", "Suscripciones", "☁️", "Google"), ("Gasto", "Suscripciones", "💻", "Microsoft"), ("Gasto", "Suscripciones", "🤖", "ChatGPT"), ("Gasto", "Suscripciones", "📦", "Amazon Prime"), ("Gasto", "Suscripciones", "📱", "Otras suscripciones"),
    ("Gasto", "Donaciones", "❤️", "Donaciones"), ("Gasto", "Donaciones", "⛪", "Aportes"), ("Gasto", "Donaciones", "🎗", "Fundaciones"),
    ("Gasto", "Otros gastos", "❓", "Varios"), ("Gasto", "Otros gastos", "🧾", "No clasificado"),
    ("Transferencia", "Transferencias", "🔄", "Transferencia entre cuentas"),
    ("Ahorro", "Ahorro", "🏦", "Fondo de emergencia"), ("Ahorro", "Ahorro", "🎯", "Ahorro para metas"),
    ("Inversion", "Inversiones", "📈", "Compra de acciones"), ("Inversion", "Inversiones", "📉", "Venta de acciones"), ("Inversion", "Inversiones", "₿", "Compra de criptomonedas"), ("Inversion", "Inversiones", "💰", "Aporte a ETF"), ("Inversion", "Inversiones", "💵", "Retiro de inversiones"),
]

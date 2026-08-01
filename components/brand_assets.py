import unicodedata


MARCAS = {
    "bancolombia": ("bancolombia.com", "#FFD400", "B"),
    "caja social": ("bancocajasocial.com", "#009A44", "C"),
    "banco caja social": ("bancocajasocial.com", "#009A44", "C"),
    "av villas": ("avvillas.com.co", "#6B4CD8", "A"),
    "avvillas": ("avvillas.com.co", "#6B4CD8", "A"),
    "nequi": ("nequi.com.co", "#7E22CE", "N"),
    "dolarapp": ("dolarapp.com", "#18B67B", "D"),
    "dolar app": ("dolarapp.com", "#18B67B", "D"),
    "plenti": ("plenti.co", "#5B5CEB", "P"),
    "davivienda": ("davivienda.com", "#E1261C", "D"),
    "banco de bogota": ("bancodebogota.com", "#FFCB05", "B"),
    "bbva": ("bbva.com.co", "#004481", "B"),
    "scotiabank": ("scotiabankcolpatria.com", "#EC111A", "S"),
    "colpatria": ("scotiabankcolpatria.com", "#EC111A", "S"),
    "itau": ("itau.co", "#EC7000", "I"),
    "falabella": ("bancofalabella.com.co", "#5AAF2D", "F"),
    "nu": ("nu.com.co", "#820AD1", "N"),
    "lulo": ("lulo.bank", "#D9FF00", "L"),
    "rappipay": ("rappipay.co", "#FF441F", "R"),
    "rappi pay": ("rappipay.co", "#FF441F", "R"),
    "uala": ("uala.com.co", "#6133FF", "U"),
    "movii": ("movii.com.co", "#FF4F9A", "M"),
    "dale": ("dale.com.co", "#F74279", "D"),
    "paypal": ("paypal.com", "#0070E0", "P"),
    "wise": ("wise.com", "#9FE870", "W"),
    "revolut": ("revolut.com", "#FFFFFF", "R"),
    "binance": ("binance.com", "#F3BA2F", "B"),
    "coinbase": ("coinbase.com", "#1652F0", "C"),
}


def marca_para(nombre):
    normalizado = unicodedata.normalize("NFKD", nombre.lower())
    normalizado = "".join(caracter for caracter in normalizado if not unicodedata.combining(caracter))
    for clave, marca in MARCAS.items():
        if clave in normalizado:
            dominio, color, inicial = marca
            return {
                "color": color,
                "inicial": inicial,
                "nombre": nombre.upper()[:11],
            }
    return {"color": "#5B5CEB", "inicial": "🏦", "nombre": "CUENTA"}

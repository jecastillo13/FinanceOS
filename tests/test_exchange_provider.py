from unittest.mock import Mock, patch

import requests

from core.providers import FrankfurterProvider


def test_frankfurter_v2_convierte_lista_en_tasas():
    respuesta = Mock()
    respuesta.raise_for_status.return_value = None
    respuesta.json.return_value = [
        {"date": "2026-08-07", "base": "USD", "quote": "COP", "rate": 3162.57},
        {"date": "2026-08-09", "base": "USD", "quote": "EUR", "rate": 0.86616},
    ]
    with patch("core.providers.frankfurter_provider.requests.get", return_value=respuesta) as get:
        tasas = FrankfurterProvider().obtener_tasas("USD")
    assert tasas == {"COP": 3162.57, "EUR": 0.86616}
    assert get.call_args.kwargs["params"]["base"] == "USD"


def test_frankfurter_devuelve_vacio_si_falla_la_red():
    with patch("core.providers.frankfurter_provider.requests.get", side_effect=requests.Timeout("sin red")):
        assert FrankfurterProvider().obtener_tasas("USD") == {}

# FinanceOS Mobile

Este frontend Flutter consume la API local de `../api` sin duplicar cálculos financieros.

Cuando Flutter esté instalado:

```powershell
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://IP-DE-TU-PC:8000
```

Para un teléfono físico, ambos dispositivos deben estar en la misma red Wi-Fi. Reemplaza `IP-DE-TU-PC` por la IP privada del computador; para el emulador Android se usa por defecto `http://10.0.2.2:8000`.

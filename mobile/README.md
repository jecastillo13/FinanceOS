# FinanceOS Mobile

Este frontend Flutter consume la API local de `../api` sin duplicar cálculos financieros.

Cuando Flutter esté instalado:

```powershell
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://IP-DE-TU-PC:8000
```

## Generar el proyecto nativo

Esta carpeta contiene el codigo Flutter compartido. En un equipo con Flutter instalado ejecuta una sola vez:

```powershell
cd mobile
flutter create --platforms=android,ios .
flutter pub get
flutter run --dart-define=API_URL=http://IP-DE-TU-PC:8000
```

El boton de escaner abre la camara, procesa la imagen con OCR en el dispositivo y obliga a confirmar total, cuenta y categoria antes de crear el movimiento. Android e iOS solicitaran el permiso de camara durante el primer uso.

Para un teléfono físico, ambos dispositivos deben estar en la misma red Wi-Fi. Reemplaza `IP-DE-TU-PC` por la IP privada del computador; para el emulador Android se usa por defecto `http://10.0.2.2:8000`.

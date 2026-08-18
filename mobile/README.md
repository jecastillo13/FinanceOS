# FinanceOS Mobile

Este cliente es completamente nativo en Flutter y consume la API de `../api` sin duplicar cálculos financieros. Incluye sesión Bearer guardada en Android Keystore/iOS Keychain, dashboard, módulos financieros, formularios de creación, eliminación confirmada, reportes, usuarios, MFA, cámara y OCR local.

Cuando Flutter esté instalado:

```powershell
cd mobile
flutter pub get
flutter run --dart-define=API_URL=http://IP-DE-TU-PC:8000
```

Para generar el APK instalable:

```powershell
flutter build apk --debug --dart-define=API_URL=http://IP-DE-TU-PC:8000
```

El resultado queda en `build/app/outputs/flutter-apk/app-debug.apk`.

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

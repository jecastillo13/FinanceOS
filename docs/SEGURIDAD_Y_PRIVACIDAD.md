# Seguridad y privacidad de FinanceOS

## Estado actual: uso local privado

FinanceOS guarda la información financiera en la base de datos configurada en
`FINANCEOS_DATABASE_URL`. En el modo predeterminado usa SQLite dentro del equipo.
Los comprobantes se guardan localmente en `uploads/`, con nombres aleatorios, y
no se incluyen en Git.

La API incorpora estas defensas:

- acceso limitado a direcciones privadas y locales;
- lista de nombres de host permitidos;
- CORS limitado a los frontends autorizados;
- cabeceras contra interpretación de contenido, marcos y filtración de origen;
- documentación de la API desactivada en producción;
- comprobantes limitados a 10 MB, con tipo y firma real JPG, PNG, WEBP o PDF;
- nombres aleatorios para los archivos y auditoría de operaciones sensibles.
- usuarios con contraseña Argon2id, bloqueo temporal por intentos fallidos,
  sesiones opacas revocables en cookie `HttpOnly` y roles superadmin/usuario;
- filtrado automático por propietario en todas las entidades financieras;
- pruebas que verifican que cambiar un ID no permite consultar datos ajenos.
- límites por IP en registro, inicio de sesión y recuperación;
- verificación de correo y recuperación con tokens de un solo uso y vencimiento;
- MFA TOTP compatible con aplicaciones autenticadoras, con secreto cifrado;
- configuración de producción que falla cerrada si falta HTTPS, PostgreSQL,
  SMTP, hosts explícitos o la clave de cifrado MFA;
- Android de producción sin tráfico HTTP, sin copias de seguridad del sistema y
  con bloqueo de capturas de pantalla.

Esto reduce la superficie de ataque, pero ningún sistema puede prometer que es
imposible de vulnerar. Mantén Windows, Python, Node, Flutter y sus dependencias
actualizados, usa una contraseña de inicio de sesión fuerte y activa BitLocker.

## Configuración privada recomendada

1. Copia `.env.example` como `.env` sin subirlo a Git. La API carga ese archivo
   automáticamente al iniciar.
2. Conserva `FINANCEOS_PRIVATE_NETWORK_ONLY=true` mientras la API viva en tu PC.
3. Ajusta `FINANCEOS_ALLOWED_HOSTS` a los hosts realmente utilizados.
4. Permite el puerto de la API en el firewall solo para la red privada.
5. Guarda copias de seguridad cifradas fuera del computador.

Web y móvil usan sesiones individuales servidas por la API; no contienen una
clave maestra compartida. La captura de facturas se abre desde
Movimientos para que cámara, PDF y OCR respeten la misma autenticación.

En modo privado (`FINANCEOS_PUBLIC_SIGNUP=false`), solo el primer registro puede
configurar la instalación y recibe el rol `superadmin`; después se cierra el
registro. En modo público (`FINANCEOS_PUBLIC_SIGNUP=true`), todos los registros
crean usuarios normales. El superadministrador se provisiona exclusivamente
desde una terminal privada del servidor con `scripts/create_superadmin.py`.

El rol nunca se elige desde React, Flutter ni una solicitud pública. El
superadministrador puede crear o desactivar accesos desde Configuración, pero no
ascender usuarios desde la interfaz. Cada usuario recibe su catálogo y espacio
independiente. Los respaldos completos son exclusivos del superadministrador
porque contienen información de toda la instalación.

## Controles incluidos para producción

`compose.production.yml` levanta PostgreSQL, la API y Caddy. Caddy gestiona TLS,
la API valida la configuración antes de arrancar y el contenedor se ejecuta como
usuario sin privilegios, con sistema de archivos de solo lectura. El frontend
muestra en Configuración un Centro de Seguridad sin revelar secretos.

GitHub Actions ejecuta pruebas, compilación y auditorías de dependencias.
Dependabot vigila Python, npm, Flutter y las propias acciones.

## Requisitos operativos antes de publicar en Internet

Antes de ofrecer FinanceOS a varios usuarios se debe implementar:

- contratar y configurar dominio, servidor, PostgreSQL administrado y SMTP;
- activar MFA en las cuentas administrativas y recomendarlo a todas las personas;
- probar restauraciones de copias de seguridad cifradas;
- secretos únicamente en el servidor, nunca dentro de React o Flutter;
- almacenamiento privado de comprobantes y enlaces firmados de corta duración;
- usar Redis o limitación en el proxy al ejecutar varias instancias de la API;
- política de retención, exportación y eliminación completa de datos personales;
- análisis de dependencias y pruebas de autorización antes de cada versión.

FinanceOS no se debe publicar directamente desde el computador personal. El
archivo de despliegue es una base reproducible; la contratación del dominio,
correo y servicios administrados requiere una decisión del propietario.

## Modelo de sincronización

Web y móvil consumen la misma API y por eso no duplican cálculos ni patrimonio.
En producción, cada operación debe incluir el usuario autenticado y la API debe
filtrar siempre por ese propietario. La interfaz nunca será la barrera de acceso:
la autorización debe ocurrir en el servidor y en cada consulta.

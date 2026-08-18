# Seguridad y privacidad de FinanceOS

## Estado actual: uso local privado

FinanceOS guarda la información financiera en la base de datos configurada en
`FINANCEOS_DATABASE_URL`. En el modo predeterminado usa SQLite dentro del equipo.
Los comprobantes se guardan localmente en `uploads/`, con nombres aleatorios, y
no se incluyen en Git.

La API incorpora estas defensas:

- acceso limitado a direcciones privadas y locales;
- lista de nombres de host permitidos;
- token opcional en las rutas financieras;
- CORS limitado a los frontends autorizados;
- cabeceras contra interpretación de contenido, marcos y filtración de origen;
- documentación de la API desactivada en producción;
- comprobantes limitados a 10 MB, con tipo y firma real JPG, PNG, WEBP o PDF;
- nombres aleatorios para los archivos y auditoría de operaciones sensibles.

Esto reduce la superficie de ataque, pero ningún sistema puede prometer que es
imposible de vulnerar. Mantén Windows, Python, Node, Flutter y sus dependencias
actualizados, usa una contraseña de inicio de sesión fuerte y activa BitLocker.

## Configuración privada recomendada

1. Copia `.env.example` como `.env` sin subirlo a Git. La API carga ese archivo
   automáticamente al iniciar.
2. Genera un token largo y aleatorio para `FINANCEOS_API_TOKEN`.
3. Conserva `FINANCEOS_PRIVATE_NETWORK_ONLY=true` mientras la API viva en tu PC.
4. Ajusta `FINANCEOS_ALLOWED_HOSTS` a los hosts realmente utilizados.
5. Permite el puerto de la API en el firewall solo para la red privada.
6. Guarda copias de seguridad cifradas fuera del computador.

El token compartido de desarrollo no reemplaza un inicio de sesión. Tampoco debe
considerarse secreto si está compilado dentro del frontend o del APK.

## Requisitos antes de publicar en Internet

Antes de ofrecer FinanceOS a varios usuarios se debe implementar:

- autenticación individual con contraseñas cifradas (Argon2id) o un proveedor OIDC;
- sesiones cortas, renovación segura y revocación;
- `usuario_id` y autorización por propietario en cada cuenta, movimiento, meta,
  tarjeta, inversión y comprobante;
- PostgreSQL administrado con cifrado, copias de seguridad y migraciones;
- HTTPS obligatorio detrás de un proxy o plataforma confiable;
- secretos únicamente en el servidor, nunca dentro de React o Flutter;
- almacenamiento privado de comprobantes y enlaces firmados de corta duración;
- límites de solicitudes, bloqueo ante intentos repetidos y registro de auditoría;
- política de retención, exportación y eliminación completa de datos personales;
- análisis de dependencias y pruebas de autorización antes de cada versión.

## Modelo de sincronización

Web y móvil consumen la misma API y por eso no duplican cálculos ni patrimonio.
En producción, cada operación debe incluir el usuario autenticado y la API debe
filtrar siempre por ese propietario. La interfaz nunca será la barrera de acceso:
la autorización debe ocurrir en el servidor y en cada consulta.

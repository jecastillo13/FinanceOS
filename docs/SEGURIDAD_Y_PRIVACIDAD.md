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
- usuarios con contraseña Argon2id, bloqueo temporal por intentos fallidos,
  sesiones opacas revocables en cookie `HttpOnly` y roles administrador/usuario;
- filtrado automático por propietario en todas las entidades financieras;
- pruebas que verifican que cambiar un ID no permite consultar datos ajenos.

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

El token compartido de desarrollo no reemplaza el inicio de sesión y tampoco debe
considerarse secreto si está compilado dentro del frontend o del APK. Web y móvil
usan la sesión servida por la API; la captura de facturas se abre desde
Movimientos para que cámara, PDF y OCR respeten la misma autenticación.

El primer usuario es el administrador de la instalación. Solo él puede crear o
desactivar accesos desde Configuración. Cada usuario nuevo recibe su catálogo de
categorías y comienza con un espacio independiente. Los respaldos completos son
una operación administrativa porque contienen información de toda la instalación.

## Requisitos antes de publicar en Internet

Antes de ofrecer FinanceOS a varios usuarios se debe implementar:

- MFA o un proveedor OIDC para una publicación multiusuario en Internet;
- renovación segura de sesiones y recuperación de contraseña;
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

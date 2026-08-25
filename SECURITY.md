# Política de seguridad de FinanceOS

## Superficie soportada

La publicación soportada utiliza `compose.production.yml`: Caddy es el único
servicio expuesto, la API permanece en la red privada y PostgreSQL almacena los
datos. No se admite publicar directamente el puerto 8000 ni ejecutar producción
sin HTTPS, autenticación o aislamiento por usuario.

## Invariantes

- Toda entidad financiera pertenece a un usuario y nunca debe cruzar ese límite.
- Las mutaciones web requieren cookie segura y origen autorizado; móvil usa Bearer.
- Los importes son finitos, acotados y se persisten como decimales.
- Texto exportado a hojas de cálculo nunca se interpreta como fórmula.
- Adjuntos se decodifican o validan estructuralmente antes de persistirse.
- Los respaldos y la administración de usuarios son exclusivos del superadministrador.
- Los fallos de contraseña y MFA tienen límites compartidos y bloqueo por cuenta.
- Una sesión expira por tiempo absoluto y por inactividad y puede revocarse.
- Secretos, claves MFA, bases, respaldos y comprobantes no se almacenan en Git.

## Archivos y límites

Se aceptan JPEG, PNG, WEBP y PDF de hasta 10 MB. Imágenes: máximo 24 millones
de píxeles. PDF: máximo 25 páginas, 10.000 objetos y sin JavaScript, acciones
automáticas, archivos incrustados, XFA ni contenido activo.

## Reporte responsable

No publiques datos financieros, credenciales ni pruebas con información real.
Reporta de forma privada la versión, ruta afectada, impacto y pasos mínimos de
reproducción. No realices denegación de servicio, ingeniería social, extracción
de datos ajenos ni pruebas destructivas.

## Validación antes de publicar

Ejecuta `pytest -q`, `npm ci && npm run build`, `flutter test`, auditorías de
dependencias y una restauración de respaldo en un ambiente de pruebas separado.

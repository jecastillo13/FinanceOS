# Implementation Plan: Perímetro central y arranque fail-closed

## Selected Design And Constraints

Aplicar política central sin nuevos servicios y conservar Caddy y validación de
archivos como capas independientes.

## Source Revision And Drift Check

Base inspeccionada: `c89366360075b526296630d15df041e870d05efc`. Los cambios de
esta implementación constituyen deriva intencional y revisada.

## Affected Components

`api/main.py`, `core/config.py`, `compose.production.yml`, `.env.example`, pruebas
y documentación de seguridad.

## Ordered Work Packages

- Cabeceras e ID uniforme.
- Límite general declarado.
- Validación fail-closed.
- Recursos de contenedor y guía operativa.

## Compatibility And Migration

El valor predeterminado conserva 12 MB. Producción debe aportar secretos y
orígenes válidos; desarrollo conserva su flujo local.

## Tactical Protections During Migration

Mantener Caddy, límites de adjuntos, CORS, hosts, CSRF por origen y rate limiting.

## Tests And Security Validation

Pruebas para 2xx, rechazo de origen, 413, IDs maliciosos y configuración válida e
inválida, además de la suite completa y auditorías existentes.

## Performance And Resource Benchmarks

Si existe tráfico real, comparar p95 y memoria con requests de 1 KB, 1 MB y 10 MB.
No se establece una cifra sin medición.

## Rollout And Rollback

Desplegar primero en pruebas, comprobar health y cabeceras, luego producción. Un
revert restaura la versión previa; el proxy continúa protegiendo el límite.

## Acceptance Criteria

Toda respuesta contiene política e ID, cuerpos declarados mayores a 12 MB se
rechazan, configuración insegura no inicia y todas las pruebas pasan.

## Open Decisions

Infraestructura de secretos, observabilidad, respaldos, WAF y pentest.


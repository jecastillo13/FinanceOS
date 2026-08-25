# Security Hardening Proposal: Perímetro HTTP seguro y verificable

## Decision

Decidir si FinanceOS conserva defensas repartidas entre proxy, middleware y
respuestas, o si la API posee un único límite que las aplica también al fallar.

## Executive Recommendation

Consideramos dos opciones: **Opción 1, reforzar guardas locales**, mantiene la
estructura anterior; **Opción 2, perímetro central y arranque fail-closed**,
concentra tamaño, correlación y cabeceras. Recomiendo la Opción 2 porque no añade
infraestructura y reduce deriva futura.

## Evidence

| Evidence | Finding or document | What it establishes |
| --- | --- | --- |
| `E001` | Requisitos de defensa en profundidad | Solicita límites, cabeceras, disponibilidad, trazabilidad y configuración segura. |

Inspeccioné `api/main.py`, `core/config.py`, `compose.production.yml`,
`deploy/Caddyfile` y las pruebas de seguridad. Observamos cabeceras sólidas en el
camino normal, pero los rechazos tempranos retornaban antes de aplicarlas. También
observamos límites en Caddy y archivos, no un límite general en la API.

## Current Design And Failure Mode

El proxy limitaba 12 MB y el servicio de adjuntos validaba 10 MB, mientras el
middleware resolvía origen, abuso y sesión. Una respuesta creada dentro de una de
esas guardas escapaba antes de la fase común de cabeceras. Esto no convierte por
sí mismo el error en una intrusión, pero hace que una política importante dependa
del camino tomado y facilita regresiones.

## Desired Invariants

- Toda respuesta, incluidas 401, 403, 413 y 429, lleva la misma política HTTP.
- Toda solicitud con tamaño declarado excesivo se rechaza antes del endpoint.
- Todo request tiene un identificador de correlación sintácticamente seguro.
- Producción no inicia con origen ambiguo, clave MFA inválida o bootstrap débil.

## Constraints And Non-Goals

No sustituimos WAF, DDoS, antivirus, SIEM, KMS ni pentest. La aplicación local
debe seguir funcionando sin servicios adicionales. Caddy continúa imponiendo el
límite real a cuerpos transferidos por streaming en producción.

## Before Architecture

[Diagrama anterior](../diagrams/perimetro-seguro-before.mmd). El control quedaba
repartido y algunas respuestas cortaban el flujo antes de la política común.

## Options

### Option 1: Reforzar guardas locales

Esta opción añade cabeceras y límites a cada retorno y endpoint. Preserva al
máximo el código existente y su costo de ejecución es despreciable. Su debilidad
es humana: cada ruta futura debe recordar el contrato, por lo que el riesgo de
deriva permanece. El despliegue y rollback son simples, pero la cobertura exige
enumerar continuamente todos los caminos.

[Diagrama](../diagrams/perimetro-seguro-local-after.mmd)

| Change | Before | After | Security consequence | Cost |
| --- | --- | --- | --- | --- |
| Guardas | Respuestas heterogéneas | Cada sitio se corrige | Cierra caminos actuales | Mantenimiento repetido |

### Option 2: Perímetro central y arranque fail-closed

Esta opción convierte el middleware en propietario de la política HTTP. Genera o
valida un ID acotado, rechaza tamaños declarados excesivos y aplica cabeceras a
las respuestas normales y tempranas. `core/config.py` valida coherencia de URL,
CORS, Fernet, token inicial y tamaño antes de aceptar producción. La ventaja más
atractiva es que un endpoint nuevo hereda la política. El costo es que el
middleware se vuelve crítico y debe tener pruebas enfocadas; por eso mantenemos
Caddy como defensa independiente y límites específicos de archivos.

[Diagrama](../diagrams/perimetro-seguro-central-after.mmd)

| Change | Before | After | Security consequence | Cost |
| --- | --- | --- | --- | --- |
| Propiedad | Distribuida | Middleware central | Menos omisiones | Mayor criticidad del middleware |
| Producción | Validación parcial | Configuración coherente o no inicia | Falla cerrada | Configuración más estricta |
| Recursos | Proxy y archivos | Proxy, API y archivos | Defensa en profundidad | Comparación entera por request |

## Comparison

| Dimension | Option 1 | Option 2 |
| --- | --- | --- |
| Security | Mejora caminos conocidos; deriva residual | Mejora todos los caminos heredados |
| Performance | Neutral, fuente revisada | Neutral esperado; operación acotada no medida |
| Memory | Neutral | Neutral; un ID corto por request |
| Reliability | Menos cambio central | Arranque falla ante configuración insegura |
| Operability | Más sitios que auditar | Una política y un ID correlacionable |
| Migration | Mínima | Incremental y reversible |

La diferencia decisiva no es una cifra de rendimiento —no la medimos— sino la
propiedad del control. La Opción 2 hace más difícil omitirlo accidentalmente.

## Recommendation

Recomiendo la Opción 2 bajo las restricciones actuales. La Opción 1 sería
preferible solo si un framework externo impidiera un middleware fiable o si una
medición demostrara un impacto relevante, algo que hoy no observamos ni podemos
afirmar.

## Evidence Coverage And Residual Risk

| Evidence | Effect | Tactical fix | Residual risk |
| --- | --- | --- | --- |
| `E001` — Defensa en profundidad | Mitiga controles HTTP y operativos | Conservar Caddy y validación de archivos | WAF, SIEM, DDoS, KMS y pentest externos |

## Migration And Rollout

Se introduce con pruebas de respuestas normales y rechazadas. El rollback es un
revert del middleware/configuración; Caddy y validaciones de archivos permanecen.

## Validation Plan

Ejecutar pruebas Python completas, build web, Flutter, auditorías de dependencias,
pruebas de cabeceras 2xx/4xx/413 y un despliegue temporal detrás de Caddy. Medir
p95 antes/después con tráfico representativo si se publica a escala.

## Implementation Work Packages

- Centralizar cabeceras e identificadores.
- Rechazar tamaño declarado excesivo.
- Validar producción de forma estricta.
- Añadir límites de recursos y documentación operativa.

## Open Questions

Proveedor de secretos, logs, alertas, respaldos, WAF/DDoS y alcance del pentest.


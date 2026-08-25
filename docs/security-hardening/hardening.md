# Security Hardening Review: FinanceOS

## Evidence Basis

Revisamos `E001 — Requisitos de seguridad y defensa en profundidad` contra el
backend, despliegue, pruebas y documentación existentes. La política describe
un objetivo amplio; solo tratamos como implementado aquello que pudimos ubicar
en código o verificar con pruebas.

## Constraints

Usamos un perfil equilibrado: conservar una aplicación local rápida, preparar
un despliegue web/móvil y no fingir controles que pertenecen al proveedor de
infraestructura. No se suministró un presupuesto medido de latencia o memoria.

## Opportunity Portfolio

| Opportunity | Evidence | Options | Recommendation | Proposal |
| --- | --- | --- | --- | --- |
| Unificar el perímetro HTTP y la preparación de producción | Requisitos de API, navegador, disponibilidad y operación (`E001`) | 1. Guardas distribuidas; 2. Perímetro central y fail-closed | Opción 2, complementada con controles operativos | [Propuesta](proposals/perimetro-seguro.md) |

## Recommendation Summary

Recomendamos centralizar límites, cabeceras y correlación en el middleware y
hacer que la configuración de producción falle cerrada. Esta opción reduce la
posibilidad de que un endpoint nuevo omita defensas sin introducir otro servicio
ni otro salto de red. Los controles de nube, monitoreo y recuperación se dejan
como condiciones explícitas de lanzamiento.

## Next Decisions

Antes de producción se debe elegir proveedor de secretos, observabilidad,
respaldos inmutables, WAF/DDoS y pentest. Esas decisiones no pueden resolverse de
forma honesta solo con cambios en este repositorio.


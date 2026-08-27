# Trazabilidad del Backlog Maestro de FinanceOS

Fuente funcional: `Backlog_Maestro_Plataforma_Financiera_Inteligente.docx`, versión 1.0 (agosto de 2026).

## Regla de implementación

Una historia solo se marca como terminada cuando su cálculo y autorización existen en backend, el flujo está disponible en web y móvil, tiene estados de carga/vacío/error y cuenta con pruebas proporcionales al riesgo. La interfaz puede adaptarse al dispositivo, pero el resultado financiero y los datos deben ser los mismos.

No se reemplazarán los flujos contables existentes. Las capacidades nuevas se integrarán sobre cuentas, movimientos, categorías, transferencias, metas, inversiones y auditoría actuales. Las simulaciones permanecerán separadas de los datos reales y ninguna sugerencia de IA ejecutará cambios sin confirmación.

## Estado inicial auditado

| HU | Capacidad | Estado al iniciar | Brecha principal |
|---|---|---|---|
| 001 | Cuentas y productos | Parcial avanzada | Faltaba desactivar conservando histórico, institución y bloqueo transversal de operaciones. |
| 002 | Dashboard consolidado | Parcial avanzada | Faltan ocultar saldos, filtros y comparación de período completa. |
| 003 | Movimientos y transferencias | Parcial avanzada | Faltan anulación auditable, división por categorías y filtros equivalentes en móvil. |
| 004 | Categorización automática | Parcial | Hay detecciones confirmables; faltan reglas, confianza y aprendizaje de correcciones. |
| 005 | Consulta en lenguaje natural | Pendiente | No existe un asistente conversacional financiero trazable. |
| 006 | Capacidad de compra | Pendiente | Falta simulador determinístico antes/después. |
| 007 | Presupuestos | Parcial | Existe creación y consumo; faltan edición histórica y umbrales configurables. |
| 008 | Presupuesto adaptativo | Pendiente | Falta recomendación cuantitativa aceptable/descartable. |
| 009 | Predicción de saldo | Pendiente | Falta motor de proyección con supuestos. |
| 010 | Alertas predictivas | Pendiente | Falta generación y gestión de alertas. |
| 011 | Gastos hormiga | Pendiente | Falta clasificación agregada e impacto. |
| 012 | Cambios inusuales de gasto | Pendiente | Falta línea base y explicación de anomalías. |
| 013 | Recurrentes y suscripciones | Parcial avanzada | Hay pagos recurrentes; falta detección automática desde historial. |
| 014 | Impacto de suscripciones | Pendiente | Falta consolidado mensual/anual y simulación de cancelación. |
| 015 | Metas inteligentes | Parcial avanzada | Existen metas, aportes y pagos; faltan aportes periódicos y factibilidad completa. |
| 016 | Recalcular metas | Pendiente | Falta propuesta ante desviaciones, sin aplicación automática. |
| 017 | Portafolio | Parcial avanzada | Existe portafolio trazable; falta ampliar tipos y estados históricos. |
| 018 | Rentabilidad | Parcial avanzada | Existe rentabilidad básica; faltan flujos, dividendos y comparación temporal. |
| 019 | Escanear comprobante | Parcial avanzada | OCR web/móvil existe; falta robustecer calidad y extracción estructurada. |
| 020 | Movimiento desde comprobante | Parcial avanzada | Existe confirmación y deduplicación; falta ampliar edición previa y cobertura documental. |
| 021 | Espacio compartido | Pendiente | Falta modelo de grupos, invitaciones y permisos. |
| 022 | Dividir gasto | Pendiente | Falta reparto, estados y liquidación. |
| 023 | Eventos financieros | Parcial | Recurrentes aportan fechas; falta entidad unificada de eventos. |
| 024 | Calendario inteligente | Pendiente | Falta vista mensual/semanal y reprogramación. |
| 025 | Documentos financieros | Parcial | Hay comprobantes ligados a movimientos; falta repositorio documental general. |
| 026 | Vencimientos documentales | Pendiente | Falta extracción/registro y alertas. |
| 027 | Transacciones inusuales | Pendiente | Las detecciones actuales importan avisos, no calculan anomalías. |
| 028 | Confirmar/desconocer sospechoso | Parcial conceptual | Existe confirmar/descartar detección, no flujo antifraude ni reporte. |
| 029 | Retos financieros | Pendiente | Falta entidad y seguimiento. |
| 030 | Logros | Pendiente | Falta motor auditable de logros. |
| 031 | Patrimonio neto | Parcial avanzada | El consolidado existe; falta clasificación explícita y trazabilidad detallada. |
| 032 | Histórico de patrimonio | Parcial | Hay tendencias, pero faltan snapshots y variación explicada. |
| 033 | Compra financiada/contado | Pendiente | Falta simulador de costo total. |
| 034 | Comparar escenarios | Pendiente | Falta persistencia temporal de escenarios y comparación. |
| 035 | Créditos y obligaciones | Pendiente | Tarjetas de crédito cubren solo una parte del modelo de deuda. |
| 036 | Estrategia de pago | Pendiente | Falta motor avalancha/bola de nieve y comparación. |
| 037 | Reporte mensual | Parcial avanzada | Resumen y exportación existen; faltan comparativos y narrativa estructurada. |
| 038 | Recomendaciones mensuales | Pendiente | Falta priorización basada en evidencia calculada. |
| 039 | Gemelo financiero | Pendiente | Falta snapshot versionado con procedencia y supuestos. |
| 040 | Escenarios complejos | Pendiente | Depende del gemelo y simulador. |
| 041 | Salud financiera | Pendiente | Falta score transparente, dimensiones, versión y confianza. |
| 042 | Acciones de mejora | Pendiente | Depende del score y de recomendaciones determinísticas. |

## Orden de entrega

1. Cerrar el MVP confiable: HU-001, 002, 003, 004, 007, 015, 023 y 031.
2. Automatización: HU-009 a 014, HU-024, HU-032 y HU-037.
3. Inteligencia explicable: HU-005, 006, 008, 016, 038, 041 y 042.
4. Deuda y simulación: HU-033 a 036.
5. Colaboración, documentos y antifraude: HU-021, 022, 025 a 030.
6. Gemelo financiero: HU-039 y 040, únicamente cuando la calidad del dato base sea estable.

## Primer bloque completado

HU-001 incorpora institución, estado activo/histórico, exclusión de cuentas inactivas en consolidados y rechazo de movimientos, transferencias, pagos, compras e inversiones nuevas sobre cuentas desactivadas. Web y móvil permiten cambiar el estado sin borrar el historial.

# Guía de funcionalidades de FinanceOS

## Primer ingreso

1. La primera cuenta creada es el **superadministrador** de una instalación privada.
2. Al iniciar sesión aparece la guía de primeros pasos.
3. El botón `?` de la barra superior y del menú vuelve a abrir la guía.
4. El administrador puede crear usuarios desde **Configuración → Personas con acceso**.
5. Cada usuario tiene cuentas, movimientos y demás información financiera aislada.

## Seguridad

- **MFA:** Configuración → Autenticación multifactor → Activar MFA.
- La clave generada se registra en Google Authenticator, Microsoft Authenticator u otra aplicación TOTP.
- El código de seis dígitos confirma la activación y será solicitado en próximos inicios de sesión.
- Solo el superadministrador puede crear o desactivar usuarios.

## Facturas y comprobantes

- **Celular:** Movimientos → Tomar foto. Android abre la cámara tras conceder permiso.
- **Web:** Movimientos → Subir PDF o imagen.
- FinanceOS propone fecha, comercio, total, categoría y coincidencia con pagos recurrentes.
- Nada afecta los saldos hasta que el usuario revise y confirme los datos.
- El comprobante se adjunta al movimiento y una huella evita registrar dos veces la misma factura.

## Módulos disponibles

| Módulo | Funciones principales |
|---|---|
| Centro | Patrimonio consolidado en COP, flujo de caja, distribución y cuentas |
| Cuentas | Crear, editar y eliminar cuentas con moneda original |
| Tarjetas | Registrar medios, analizar avisos bancarios y confirmar compras |
| Categorías | Catálogo agrupado y categorías personalizadas |
| Movimientos | Crear, editar, eliminar, fotografiar y adjuntar comprobantes |
| Recurrentes | Crear, editar, eliminar y registrar pagos desde una cuenta |
| Transferencias | Mover dinero entre cuentas sin duplicar ingresos o gastos |
| Presupuestos | Presupuesto mensual, consumo y alertas |
| Metas | Aportes, pagos, historial y eliminación controlada |
| Inversiones | Posiciones, costo, valor y rentabilidad multimoneda |
| Monedas | Tasas, conversión y consolidación en COP |
| Reportes | Exportaciones y resumen financiero |
| Configuración | Usuarios, MFA, respaldo, seguridad y estado técnico |

## Regla de consistencia

La API es la única fuente de verdad para la aplicación web y móvil. Las interfaces no recalculan saldos por separado. Transferencias, pagos recurrentes, metas y movimientos usan servicios transaccionales para evitar duplicaciones.

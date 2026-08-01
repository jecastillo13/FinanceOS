# FinanceOS

Aplicación personal de finanzas construida con Streamlit y SQLite. Permite administrar cuentas, categorías, movimientos y tasas de cambio en una interfaz local.

## Estado actual

La versión actual es una base funcional para:

- Crear, editar y eliminar cuentas sin movimientos asociados.
- Crear y consultar categorías de ingreso y gasto.
- Instalar un catálogo profesional de categorías, con grupos, iconos, estado y categorías especiales preparadas para transferencias, ahorro e inversiones.
- Registrar, editar y eliminar movimientos. El tipo de categoría determina automáticamente si el movimiento suma o resta del saldo de la cuenta.
- Programar gastos recurrentes y marcarlos como pagados desde una cuenta; cada pago crea su movimiento automáticamente.
- Transferir dinero entre cuentas sin alterar los totales de ingresos y gastos.
- Crear presupuestos mensuales por categoría, con alertas al alcanzar el límite.
- Consultar un Centro Financiero con flujo de caja, distribución de gastos y alertas de presupuesto.
- Consultar un dashboard con patrimonio, cuentas, ingresos y gastos acumulados.
- Actualizar y consultar tasas de cambio mediante Frankfurter.

Metas, inversiones, reportes y configuración están visibles como secciones futuras; todavía no están implementadas.

## Requisitos

- Python 3.11 o superior.
- Un entorno virtual funcional.

## Instalación y ejecución

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run financeos.py
```

La base de datos SQLite se crea localmente en `database/finance.db` y no se versiona.

## Convenciones financieras

- Una categoría de tipo **Ingreso** guarda el valor como positivo.
- Una categoría de tipo **Gasto** guarda el valor como negativo.
- El saldo de una cuenta se actualiza al crear, editar o eliminar un movimiento.
- Un movimiento conserva siempre la moneda de su cuenta. Por ejemplo, un gasto de USD 20 se guarda como USD 20.
- El patrimonio, los presupuestos, las alertas y los gráficos del Dashboard se expresan en COP usando las tasas almacenadas.
- Si falta una tasa de cambio, FinanceOS excluye ese valor del total consolidado y muestra una alerta; actualiza las tasas desde Monedas.
- No se puede cambiar el saldo ni la moneda de una cuenta que ya tiene movimientos, para conservar la trazabilidad contable.

## Estructura

```text
financeos.py          Punto de entrada de Streamlit
modules/              Pantallas de la aplicación
core/models.py        Modelo de datos SQLAlchemy
core/services/        Lógica de cuentas, categorías, movimientos y monedas
core/providers/       Integraciones externas, como Frankfurter
components/           Componentes reutilizables de interfaz
database/             Base de datos local (ignorada por Git)
```

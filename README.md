# FinanceOS

## API local para móvil y web

La primera API vive en `api/main.py` y reutiliza los servicios financieros existentes. Streamlit continúa funcionando sobre la misma base local durante la transición.

```powershell
uvicorn api.main:app --reload --port 8000
```

Consulta la documentación interactiva en `http://localhost:8000/docs`. Los endpoints iniciales viven bajo `/api/v1` e incluyen cuentas, categorías, movimientos, metas y el resumen del Dashboard.

> La API exige inicio de sesión y aísla los registros por usuario. Para publicarla en Internet aún se requieren HTTPS, PostgreSQL administrado, almacenamiento privado y operación supervisada.

## Pruebas de integridad financiera

Las pruebas usan automáticamente una base SQLite temporal y nunca modifican `database/finance.db`:

```powershell
python -m unittest discover -s tests -v
```

La conexión puede configurarse con `FINANCEOS_DATABASE_URL`. Esto permite ejecutar pruebas aisladas y prepara la migración futura a PostgreSQL.

## Validaciones automáticas de Git

FinanceOS incluye validaciones locales versionadas para detectar errores antes de consumir tiempo en una revisión remota:

```powershell
# Ejecutar una sola vez después de clonar el repositorio
powershell -ExecutionPolicy Bypass -File scripts/install_hooks.ps1

# Ejecución manual
powershell -ExecutionPolicy Bypass -File scripts/verificar_commit.ps1
powershell -ExecutionPolicy Bypass -File scripts/verificar_push.ps1
powershell -ExecutionPolicy Bypass -File scripts/verificar_completo.ps1
```

- `pre-commit` revisa solo los cambios preparados: archivos locales prohibidos, posibles secretos y sintaxis Python.
- `pre-push` valida únicamente las áreas modificadas: backend, React o Flutter, sin iniciar un emulador.
- La validación `full` añade auditorías de dependencias de Python y npm.
- GitHub Actions repite las pruebas de backend, frontend y móvil en un entorno limpio.

Si Flutter no está en `PATH`, el verificador reconoce la instalación estable de Puro en Windows o permite indicar su ejecutable mediante `FLUTTER_BIN`.

La estrategia completa de hooks, CI y análisis estructural opcional con Codebase Memory MCP está documentada en [`docs/OPTIMIZACION_DESARROLLO.md`](docs/OPTIMIZACION_DESARROLLO.md).

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
- Consultar un dashboard moderno con patrimonio consolidado en COP, flujo de caja, distribución por categorías y composición de cuentas.
- Actualizar y consultar tasas de cambio mediante Frankfurter.
- Administrar metas con aportes, pagos vinculados a movimientos e historial.
- Registrar inversiones y consultar costo, valor actual y rentabilidad.
- Exportar reportes en CSV, Excel y PDF.
- Crear, validar y restaurar copias de seguridad desde Configuración.
- Consumir cuentas, categorías, movimientos, metas, gastos recurrentes, transferencias, presupuestos, inversiones, reportes y Dashboard mediante la API FastAPI.

La aplicación Flutter incluida en `mobile/` cuenta actualmente con el Dashboard y la bandeja de compras detectadas conectados a la API. La interfaz React es la experiencia web principal y Streamlit se conserva como cliente legado durante la migración.

### Tarjetas y compras detectadas

- Cada tarjeta débito o crédito se identifica por sus últimos cuatro dígitos y se vincula a una cuenta.
- Al registrar una tarjeta crédito, FinanceOS crea automáticamente una cuenta de deuda independiente; su saldo negativo representa lo pendiente.
- Los avisos bancarios siempre llegan como candidatos y requieren confirmación antes de crear movimientos.
- Débito descuenta la cuenta bancaria; crédito afecta únicamente la cuenta de deuda vinculada.
- El pago de una tarjeta crédito es una transferencia desde una cuenta bancaria hacia la deuda: reduce ambos saldos sin duplicar el gasto.
- La moneda del aviso debe coincidir con la tarjeta y su cuenta vinculada.
- Una huella de banco, tarjeta, comercio, valor y fecha evita duplicar el mismo aviso.

En la web, abre **Tarjetas** y pega el aviso. En móvil, abre el icono de notificaciones. La lectura automática de notificaciones Android requiere generar el proyecto nativo con Flutter y autorización explícita del usuario.

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

### Nuevo frontend React

El frontend profesional vive en `frontend/` y consume la API FastAPI. Ejecuta primero la API:

```powershell
uvicorn api.main:app --reload --port 8000
```

Después, en otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` durante el desarrollo, porque Vite actualiza los cambios al instante.

Para usar una sola dirección, compila el frontend y luego inicia FastAPI:

```powershell
cd frontend
npm run build
cd ..
uvicorn api.main:app --reload --port 8000
```

Abre `http://localhost:8000`. FastAPI servirá la aplicación React y conservará su documentación en `http://localhost:8000/docs`.

La base de datos SQLite se crea localmente en `database/finance.db` y no se versiona.

## Convenciones financieras

El flujo detallado, la matriz de efectos y las reglas contra duplicados están documentados en [`docs/FLUJO_CONTABLE.md`](docs/FLUJO_CONTABLE.md).

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

## Web y movil protegidos

La API admite PostgreSQL mediante `FINANCEOS_DATABASE_URL` y exige sesiones individuales. Copia `.env.example`, configura valores seguros en el servidor y no publiques ese archivo. No se compilan secretos compartidos dentro de React ni del APK.

Para ejecutar Flutter contra una API publicada usa:

```powershell
flutter run --dart-define=API_URL=https://tu-api.example.com
```

La aplicacion movil incluye el flujo de camara y OCR en `mobile/lib/features/receipts/receipt_scan_page.dart`: toma la foto, propone comercio y total, exige confirmacion y adjunta la imagen al movimiento. La huella del comprobante evita descontar dos veces por reintentos o doble toque.

FinanceOS separa el registro normal de la administración de la plataforma:

- En una instalación privada (`FINANCEOS_PUBLIC_SIGNUP=false`), el primer registro configura el `superadmin`; en producción también exige el código secreto `FINANCEOS_BOOTSTRAP_TOKEN`. Después, el registro queda cerrado.
- En una publicación (`FINANCEOS_PUBLIC_SIGNUP=true`), todo autorregistro crea únicamente un `usuario` con espacio financiero independiente.
- El `superadmin` de una publicación se crea desde una terminal privada del servidor, nunca desde la web ni desde la app:

```powershell
python scripts/create_superadmin.py --nombre "Administrador" --correo "admin@dominio.com"
```

El comando solicita una contraseña oculta de al menos 12 caracteres. El superadministrador puede crear o desactivar usuarios desde **Configuración → Personas con acceso**, pero no convertirlos en superadministradores. La API aplica `usuario_id` en cuentas, categorías, movimientos, tarjetas, comprobantes, recurrentes, transferencias, presupuestos, metas, inversiones y auditoría.

La autenticación incluye verificación de correo, recuperación con enlace de un
solo uso, bloqueo temporal, MFA TOTP y sesiones revocables. En desarrollo, los
correos se escriben en `database/correo-desarrollo.txt`; producción exige SMTP.

### Base de despliegue segura

```powershell
Copy-Item .env.production.example .env
# Completa el dominio y los secretos únicamente en el servidor.
docker compose -f compose.production.yml config
docker compose -f compose.production.yml up -d --build
```

El despliegue usa PostgreSQL, Caddy con HTTPS automático y contenedores sin
privilegios. Consulta [Seguridad y privacidad](docs/SEGURIDAD_Y_PRIVACIDAD.md)
antes de exponer el servicio.

## Arquitectura y crecimiento

FinanceOS mantiene la interfaz de Streamlit separada de las reglas financieras:

- `modules/` y `components/` solo presentan datos y capturan acciones de la persona usuaria.
- `core/services/` contiene las reglas de negocio reutilizables: saldos, signos de movimientos, presupuestos, transferencias y conversiones.
- `core/models.py` define el contrato de datos y `core/database.py` administra la base local y las migraciones versionadas.
- `core/providers/` aísla servicios externos, de modo que una futura API no dependa de la interfaz.

Esta separación permite conservar las reglas actuales cuando se agregue una API web o una aplicación móvil. La evolución prevista es:

1. Mantener SQLite para uso personal sin conexión y migraciones idempotentes para cada actualización.
2. Ampliar la API FastAPI existente sin duplicar reglas de cálculo.
3. Migrar la instalación desplegada a PostgreSQL administrado cuando haya sincronización pública entre dispositivos.
4. Completar en Flutter los módulos móviles que ya están disponibles en Streamlit.

### Integridad y trazabilidad

- Las migraciones quedan registradas en la tabla local `schema_migrations`; se aplican al iniciar la aplicación.
- Los índices operativos aceleran consultas de movimientos, presupuestos, tasas y auditoría.
- Las operaciones de cuentas, categorías, movimientos, pagos recurrentes, transferencias y presupuestos dejan registro en `auditoria` dentro de la misma transacción.
- Los servicios validan los datos esenciales antes de guardarlos: nombres, montos, moneda, período y frecuencia.

Para una versión multiusuario se recomienda migrar los importes de `Float` a `Decimal`/`NUMERIC`, conservar la tasa aplicada en cada movimiento y utilizar PostgreSQL. Es un cambio contable que debe hacerse con una migración y pruebas de datos, no como una modificación visual.

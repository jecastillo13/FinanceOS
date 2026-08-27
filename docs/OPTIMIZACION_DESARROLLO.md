# Optimización del desarrollo de FinanceOS

## Objetivo

Reducir revisiones repetitivas, detectar fallos antes de publicar y proporcionar a los agentes una vista estructural del proyecto sin sustituir las pruebas ni la revisión directa del código crítico.

## Validaciones locales

Instala los hooks una sola vez después de clonar el repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_hooks.ps1
```

Los niveles disponibles son:

| Nivel | Alcance |
|---|---|
| `commit` | Archivos preparados, secretos, archivos locales prohibidos y sintaxis Python |
| `push` | Solo las áreas modificadas: backend, React o Flutter |
| `full` | Todo lo anterior más auditorías de dependencias |

La validación móvil no inicia Android Studio ni un emulador. Ejecuta únicamente `flutter analyze` y `flutter test`.

## Codebase Memory MCP — opcional

Codebase Memory mantiene un índice estructural local que facilita búsquedas de clases, funciones, rutas, dependencias e impacto. No reemplaza `pytest`, las compilaciones, la auditoría de seguridad ni la validación profesional de las reglas financieras.

Precauciones recomendadas:

1. Descargar el instalador antes de ejecutarlo y revisar su contenido.
2. Verificar el checksum del binario contra el publicado en la versión oficial.
3. Usar la variante sin interfaz gráfica para reducir memoria.
4. Mantener `ui_enabled=false` y no iniciar un daemon permanente en equipos limitados.
5. Conservar el índice fuera del repositorio; nunca agregarlo a Git.
6. Reiniciar Codex después de registrar el servidor MCP.

Configuración de bajo consumo:

```powershell
codebase-memory-mcp config set auto_index true
codebase-memory-mcp config set auto_watch true
codebase-memory-mcp config set ui_enabled false
```

El primer indexado es completo. Los siguientes pueden aprovechar el índice persistente y la detección de cambios de Git.

## Responsabilidad de cada capa

```text
Hook local         -> respuesta rápida antes del commit o push
GitHub Actions     -> validación completa en un entorno limpio
Codebase Memory    -> navegación e impacto con menos lectura repetitiva
Codex              -> análisis, decisiones e implementación
Revisión humana    -> reglas financieras, tributarias y publicación
```

## Solución de problemas

- Si `pytest` no puede usar el directorio temporal de Windows, los scripts ya fijan `.pytest-tmp` dentro del proyecto.
- Si Flutter no está en `PATH`, define `FLUTTER_BIN` o usa la instalación estable de Puro.
- Si un hook bloquea un commit, corrige el problema indicado. `--no-verify` debe reservarse para emergencias y no sustituye la validación posterior.
- Si Codex no muestra las herramientas MCP después de instalarlas, cierra completamente la aplicación y vuelve a abrir el proyecto.

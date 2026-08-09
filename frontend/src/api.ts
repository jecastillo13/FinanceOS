export type Cuenta = { id: number; nombre: string; tipo: string; saldo: number; moneda: string; color?: string; icono?: string };
export type Categoria = { id: number; nombre: string; tipo: string; color: string; icono?: string; grupo?: string; activa: boolean };
export type TasaCambio = { id: number; moneda_origen: string; moneda_destino: string; tasa: number; fuente?: string; fecha_actualizacion: string };
export type Conversion = { valor_origen: number; origen: string; destino: string; valor_convertido: number };
export type Movimiento = { id: number; fecha: string; descripcion?: string; valor: number; observaciones?: string; cuenta_id: number; categoria_id: number; cuenta: string; moneda: string; categoria: string; tipo: string };
export type Presupuesto = { id: number; anio: number; mes: number; valor: number; categoria_id: number; categoria: string; gastado: number };
export type Meta = { id: number; nombre: string; objetivo: number; moneda: string; fecha_limite?: string; descripcion?: string; pagado: number; aportado: number; pendiente: number; porcentaje: number };
export type Inversion = { id: number; activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker?: string; moneda: string; costo: number; valor: number; ganancia: number; rentabilidad: number; costo_cop?: number; valor_cop?: number };
export type Portafolio = { costo_total_cop: number; valor_total_cop: number; ganancia_total_cop: number; rentabilidad: number; posiciones: Inversion[]; monedas_sin_tasa: string[] };
export type RespaldoEstado = { motor: string; tamano: number; modificado?: string; disponible: boolean };
export type GastoRecurrente = { id: number; nombre: string; valor: number; frecuencia: string; proxima_fecha_pago: string; ultima_fecha_pago?: string; activo: boolean; categoria_id: number; categoria: string };
export type Transferencia = { id: number; fecha: string; valor: number; descripcion?: string; cuenta_origen_id: number; cuenta_destino_id: number; cuenta_origen: string; cuenta_destino: string; moneda: string };
export type ReporteResumen = { anio: number; mes: number; ingresos_cop: number; gastos_cop: number; balance_cop: number; monedas_sin_tasa: string[]; movimientos: number };
export type Resumen = {
  patrimonio: number;
  cuentas_cop: number;
  inversiones_cop: number;
  cuentas: number;
  ingresos: number;
  gastos: number;
  balance: number;
};
export type Graficas = {
  flujo: Array<{ mes: string; ingresos: number; gastos: number; balance: number }>;
  gastos_categoria: Array<{ categoria: string; total?: number; valor?: number }>;
  distribucion: Array<{ cuenta: string; saldo_cop: number; moneda_original: string; tipo?: string }>;
  pendientes: number;
};

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) throw new Error(`La API respondió ${response.status}`);
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
  return response.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
  return response.json() as Promise<T>;
}

async function remove(path: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "DELETE" });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
}

export const financeApi = {
  resumen: () => get<Resumen>("/dashboard/resumen"),
  graficas: () => get<Graficas>("/dashboard/graficas"),
  cuentas: () => get<Cuenta[]>("/cuentas"),
  crearCuenta: (body: { nombre: string; tipo: string; saldo: number; moneda: string }) => post<Cuenta>("/cuentas", body),
  categorias: () => get<Categoria[]>("/categorias"),
  crearCategoria: (body: { nombre: string; tipo: string; color: string; icono: string; grupo: string; orden: number }) => post<Categoria>("/categorias", body),
  actualizarCategoria: (id: number, body: { nombre: string; tipo: string; color: string; icono: string; grupo: string; orden: number; activa: boolean }) => put<Categoria>(`/categorias/${id}`, body),
  eliminarCategoria: (id: number) => remove(`/categorias/${id}`),
  tasas: () => get<TasaCambio[]>("/monedas/tasas"),
  actualizarTasas: () => post<{ actualizadas: boolean; moneda_base: string; ultima_actualizacion?: string; total: number }>("/monedas/tasas/actualizar", {}),
  convertir: (valor: number, origen: string, destino: string) => get<Conversion>(`/monedas/convertir?valor=${valor}&origen=${origen}&destino=${destino}`),
  movimientos: () => get<Movimiento[]>("/movimientos?limite=100"),
  crearMovimiento: (body: { fecha: string; descripcion: string; valor: number; cuenta_id: number; categoria_id: number; observaciones: string }) => post<Movimiento>("/movimientos", body),
  presupuestos: (anio: number, mes: number) => get<Presupuesto[]>(`/presupuestos?anio=${anio}&mes=${mes}`),
  crearPresupuesto: (body: { anio: number; mes: number; categoria_id: number; valor: number }) => post<Presupuesto>("/presupuestos", body),
  metas: () => get<Meta[]>("/metas"),
  crearMeta: (body: { nombre: string; objetivo: number; moneda: string; fecha_limite: string | null; descripcion: string }) => post<Meta>("/metas", body),
  aportarMeta: (metaId: number, body: { fecha: string; valor: number; descripcion: string }) => post(`/metas/${metaId}/aportes`, body),
  inversiones: () => get<Portafolio>("/inversiones"),
  crearInversion: (body: { activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker: string; moneda: string; valores_totales: boolean }) => post<Inversion>("/inversiones", body),
  health: () => get<{ estado: string; servicio: string; version: string }>("/health"),
  estadoRespaldo: () => get<RespaldoEstado>("/configuracion/respaldo"),
  descargarRespaldo: async () => { const response = await fetch(`${BASE_URL}/configuracion/respaldo/descargar`); if (!response.ok) throw new Error("No fue posible crear el respaldo"); return response.blob(); },
  recurrentes: () => get<GastoRecurrente[]>("/gastos-recurrentes"),
  crearRecurrente: (body: { nombre: string; valor: number; frecuencia: string; proxima_fecha_pago: string; categoria_id: number }) => post<GastoRecurrente>("/gastos-recurrentes", body),
  pagarRecurrente: (id: number, body: { cuenta_id: number; fecha_pago: string }) => post<Movimiento>(`/gastos-recurrentes/${id}/pagar`, body),
  transferencias: () => get<Transferencia[]>("/transferencias"),
  crearTransferencia: (body: { fecha: string; cuenta_origen_id: number; cuenta_destino_id: number; valor: number; descripcion: string }) => post<Transferencia>("/transferencias", body),
  reporte: (anio: number, mes: number) => get<ReporteResumen>(`/reportes/${anio}/${mes}/resumen`),
  descargarReporte: async (anio: number, mes: number, formato: "csv"|"xlsx"|"pdf") => { const response=await fetch(`${BASE_URL}/reportes/${anio}/${mes}/${formato}`); if(!response.ok) throw new Error("No fue posible generar el reporte"); return response.blob(); },
};

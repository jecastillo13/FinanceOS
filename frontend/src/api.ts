export type Cuenta = { id: number; nombre: string; tipo: string; saldo: number; moneda: string; color?: string; icono?: string };
export type Categoria = { id: number; nombre: string; tipo: string; color: string; icono?: string; grupo?: string; activa: boolean };
export type Movimiento = { id: number; fecha: string; descripcion?: string; valor: number; observaciones?: string; cuenta_id: number; categoria_id: number; cuenta: string; moneda: string; categoria: string; tipo: string };
export type Presupuesto = { id: number; anio: number; mes: number; valor: number; categoria_id: number; categoria: string; gastado: number };
export type Meta = { id: number; nombre: string; objetivo: number; moneda: string; fecha_limite?: string; descripcion?: string; pagado: number; aportado: number; pendiente: number; porcentaje: number };
export type Inversion = { id: number; activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker?: string; moneda: string; costo: number; valor: number; ganancia: number; rentabilidad: number; costo_cop?: number; valor_cop?: number };
export type Portafolio = { costo_total_cop: number; valor_total_cop: number; ganancia_total_cop: number; rentabilidad: number; posiciones: Inversion[]; monedas_sin_tasa: string[] };
export type RespaldoEstado = { motor: string; tamano: number; modificado?: string; disponible: boolean };
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

export const financeApi = {
  resumen: () => get<Resumen>("/dashboard/resumen"),
  graficas: () => get<Graficas>("/dashboard/graficas"),
  cuentas: () => get<Cuenta[]>("/cuentas"),
  crearCuenta: (body: { nombre: string; tipo: string; saldo: number; moneda: string }) => post<Cuenta>("/cuentas", body),
  categorias: () => get<Categoria[]>("/categorias"),
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
};

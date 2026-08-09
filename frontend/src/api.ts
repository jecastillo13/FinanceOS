export type Cuenta = { id: number; nombre: string; tipo: string; saldo: number; moneda: string; color?: string; icono?: string };
export type Categoria = { id: number; nombre: string; tipo: string; color: string; icono?: string; grupo?: string; activa: boolean };
export type Movimiento = { id: number; fecha: string; descripcion?: string; valor: number; observaciones?: string; cuenta_id: number; categoria_id: number; cuenta: string; moneda: string; categoria: string; tipo: string };
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
};

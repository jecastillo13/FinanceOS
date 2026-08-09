export type Cuenta = { id: number; nombre: string; tipo: string; saldo: number; moneda: string };
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

export const financeApi = {
  resumen: () => get<Resumen>("/dashboard/resumen"),
  graficas: () => get<Graficas>("/dashboard/graficas"),
  cuentas: () => get<Cuenta[]>("/cuentas"),
};

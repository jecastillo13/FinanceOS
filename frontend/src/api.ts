export type Cuenta = { id: number; nombre: string; tipo: string; saldo: number; moneda: string; color?: string; icono?: string };
export type Categoria = { id: number; nombre: string; tipo: string; color: string; icono?: string; grupo?: string; activa: boolean };
export type TasaCambio = { id: number; moneda_origen: string; moneda_destino: string; tasa: number; fuente?: string; fecha_actualizacion: string };
export type Conversion = { valor_origen: number; origen: string; destino: string; valor_convertido: number };
export type Adjunto = { id: number; movimiento_id: number; nombre: string; tipo_mime: string; tamano: number; fecha: string; url_descarga: string };
export type Movimiento = { id: number; fecha: string; descripcion?: string; valor: number; observaciones?: string; cuenta_id: number; categoria_id: number; cuenta: string; moneda: string; categoria: string; tipo: string };
export type Tarjeta = { id: number; nombre: string; banco: string; ultimos_cuatro: string; tipo: "Credito"|"Debito"; moneda: string; cuenta_id: number; activa: boolean; cuenta: string; cuenta_tipo: string; saldo: number };
export type Deteccion = { id: number; origen: string; comercio: string; valor: number; moneda: string; fecha: string; banco: string; ultimos_cuatro?: string; tipo_sugerido?: "Credito"|"Debito"; estado: string; tarjeta_id?: number; movimiento_id?: number; duplicada: boolean };
export type Presupuesto = { id: number; anio: number; mes: number; valor: number; categoria_id: number; categoria: string; gastado: number };
export type Meta = { id: number; nombre: string; objetivo: number; moneda: string; fecha_limite?: string; descripcion?: string; pagado: number; aportado: number; pendiente: number; porcentaje: number };
export type Inversion = { id: number; activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker?: string; moneda: string; costo: number; valor: number; ganancia: number; rentabilidad: number; costo_cop?: number; valor_cop?: number };
export type Portafolio = { costo_total_cop: number; valor_total_cop: number; ganancia_total_cop: number; rentabilidad: number; posiciones: Inversion[]; monedas_sin_tasa: string[] };
export type RespaldoEstado = { motor: string; tamano: number; modificado?: string; disponible: boolean };
export type Usuario = { id: number; nombre: string; correo: string; rol: "usuario"|"superadmin"; activo: boolean };
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
  deudas: Array<{ cuenta: string; saldo_cop: number; moneda_original: string; tipo?: string }>;
  pendientes: number;
};

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";
const API_TOKEN = import.meta.env.VITE_API_TOKEN ?? "";
const authHeaders = (): Record<string,string> => API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {};
const requestOptions = { credentials: "include" as RequestCredentials };

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { headers: authHeaders(), ...requestOptions });
  if (!response.ok) throw new Error(`La API respondió ${response.status}`);
  return response.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify(body), ...requestOptions });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
  return response.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "PUT", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify(body), ...requestOptions });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
  return response.json() as Promise<T>;
}

async function remove(path: string): Promise<void> {
  const response = await fetch(`${BASE_URL}${path}`, { method: "DELETE", headers: authHeaders(), ...requestOptions });
  if (!response.ok) { const data = await response.json().catch(() => null); throw new Error(data?.detail ?? `La API respondió ${response.status}`); }
}

export const financeApi = {
  authStatus: () => get<{ requiere_configuracion: boolean; registro_publico: boolean; registro_disponible: boolean; autenticado: boolean; usuario?: Usuario }>("/auth/status"),
  registrarPropietario: (body:{nombre:string;correo:string;password:string}) => post<{id:number;nombre:string;correo:string}>("/auth/registro",body),
  iniciarSesion: (body:{correo:string;password:string}) => post<{id:number;nombre:string;correo:string}>("/auth/login",body),
  cerrarSesion: () => post<{ok:boolean}>("/auth/logout",{}),
  usuarios: () => get<Usuario[]>("/auth/usuarios"),
  crearUsuario: (body:{nombre:string;correo:string;password:string}) => post<Usuario>("/auth/usuarios",body),
  actualizarUsuario: (id:number,body:{activo:boolean}) => put<Usuario>(`/auth/usuarios/${id}`,body),
  resumen: () => get<Resumen>("/dashboard/resumen"),
  graficas: () => get<Graficas>("/dashboard/graficas"),
  cuentas: () => get<Cuenta[]>("/cuentas"),
  crearCuenta: (body: { nombre: string; tipo: string; saldo: number; moneda: string }) => post<Cuenta>("/cuentas", body),
  actualizarCuenta: (id: number, body: { nombre: string; tipo: string; moneda: string; color: string; icono: string }) => put<Cuenta>(`/cuentas/${id}`, body),
  eliminarCuenta: (id: number) => remove(`/cuentas/${id}`),
  categorias: () => get<Categoria[]>("/categorias"),
  crearCategoria: (body: { nombre: string; tipo: string; color: string; icono: string; grupo: string; orden: number }) => post<Categoria>("/categorias", body),
  actualizarCategoria: (id: number, body: { nombre: string; tipo: string; color: string; icono: string; grupo: string; orden: number; activa: boolean }) => put<Categoria>(`/categorias/${id}`, body),
  eliminarCategoria: (id: number) => remove(`/categorias/${id}`),
  tasas: () => get<TasaCambio[]>("/monedas/tasas"),
  actualizarTasas: () => post<{ actualizadas: boolean; moneda_base: string; ultima_actualizacion?: string; total: number }>("/monedas/tasas/actualizar", {}),
  convertir: (valor: number, origen: string, destino: string) => get<Conversion>(`/monedas/convertir?valor=${valor}&origen=${origen}&destino=${destino}`),
  movimientos: () => get<Movimiento[]>("/movimientos?limite=100"),
  crearMovimiento: (body: { fecha: string; descripcion: string; valor: number; cuenta_id: number; categoria_id: number; observaciones: string; huella?: string }) => post<Movimiento>("/movimientos", body),
  actualizarMovimiento: (id: number, body: { fecha: string; descripcion: string; valor: number; cuenta_id: number; categoria_id: number; observaciones: string; huella?: string }) => put<Movimiento>(`/movimientos/${id}`, body),
  eliminarMovimiento: (id: number) => remove(`/movimientos/${id}`),
  tarjetas: () => get<Tarjeta[]>("/tarjetas"),
  crearTarjeta: (body: { nombre: string; banco: string; ultimos_cuatro: string; tipo: string; moneda: string; cuenta_id?: number }) => post<Tarjeta>("/tarjetas", body),
  eliminarTarjeta: (id: number) => remove(`/tarjetas/${id}`),
  pagarTarjeta: (id: number, body: { cuenta_origen_id: number; valor: number; fecha: string; descripcion: string }) => post<Transferencia>(`/tarjetas/${id}/pagar`, body),
  detecciones: () => get<Deteccion[]>("/detecciones?estado=Pendiente"),
  detectarOperacion: (texto: string, origen="Manual") => post<Deteccion>("/detecciones", { texto, origen }),
  confirmarDeteccion: (id: number, body: { categoria_id: number; tarjeta_id?: number; cuenta_id?: number; descripcion?: string }) => post<Deteccion>(`/detecciones/${id}/confirmar`, body),
  descartarDeteccion: (id: number) => post<Deteccion>(`/detecciones/${id}/descartar`, {}),
  comprobantes: (id: number) => get<Adjunto[]>(`/movimientos/${id}/comprobantes`),
  adjuntarComprobante: async (id: number, archivo: File) => { const data=new FormData(); data.append("archivo",archivo); const response=await fetch(`${BASE_URL}/movimientos/${id}/comprobantes`,{method:"POST",headers:authHeaders(),body:data,...requestOptions}); if(!response.ok){const body=await response.json().catch(()=>null);throw new Error(body?.detail??"No fue posible adjuntar el comprobante")} return response.json() as Promise<Adjunto>; },
  presupuestos: (anio: number, mes: number) => get<Presupuesto[]>(`/presupuestos?anio=${anio}&mes=${mes}`),
  crearPresupuesto: (body: { anio: number; mes: number; categoria_id: number; valor: number }) => post<Presupuesto>("/presupuestos", body),
  metas: () => get<Meta[]>("/metas"),
  crearMeta: (body: { nombre: string; objetivo: number; moneda: string; fecha_limite: string | null; descripcion: string }) => post<Meta>("/metas", body),
  aportarMeta: (metaId: number, body: { fecha: string; valor: number; descripcion: string }) => post(`/metas/${metaId}/aportes`, body),
  pagarMeta: (metaId: number, body: { fecha: string; valor: number; descripcion: string; cuenta_id: number; categoria_id: number; observaciones: string }) => post(`/metas/${metaId}/pagos`, body),
  eliminarMeta: (metaId: number) => remove(`/metas/${metaId}`),
  inversiones: () => get<Portafolio>("/inversiones"),
  crearInversion: (body: { activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker: string; moneda: string; valores_totales: boolean }) => post<Inversion>("/inversiones", body),
  health: () => get<{ estado: string; servicio: string; version: string }>("/health"),
  estadoRespaldo: () => get<RespaldoEstado>("/configuracion/respaldo"),
  descargarRespaldo: async () => { const response = await fetch(`${BASE_URL}/configuracion/respaldo/descargar`,{headers:authHeaders(),...requestOptions}); if (!response.ok) throw new Error("No fue posible crear el respaldo"); return response.blob(); },
  recurrentes: () => get<GastoRecurrente[]>("/gastos-recurrentes"),
  crearRecurrente: (body: { nombre: string; valor: number; frecuencia: string; proxima_fecha_pago: string; categoria_id: number }) => post<GastoRecurrente>("/gastos-recurrentes", body),
  actualizarRecurrente: (id: number, body: { nombre: string; valor: number; frecuencia: string; proxima_fecha_pago: string; categoria_id: number; activa: boolean }) => put<GastoRecurrente>(`/gastos-recurrentes/${id}`, body),
  eliminarRecurrente: (id: number) => remove(`/gastos-recurrentes/${id}`),
  pagarRecurrente: (id: number, body: { cuenta_id: number; fecha_pago: string }) => post<Movimiento>(`/gastos-recurrentes/${id}/pagar`, body),
  transferencias: () => get<Transferencia[]>("/transferencias"),
  crearTransferencia: (body: { fecha: string; cuenta_origen_id: number; cuenta_destino_id: number; valor: number; descripcion: string }) => post<Transferencia>("/transferencias", body),
  eliminarTransferencia: (id: number) => remove(`/transferencias/${id}`),
  reporte: (anio: number, mes: number) => get<ReporteResumen>(`/reportes/${anio}/${mes}/resumen`),
  descargarReporte: async (anio: number, mes: number, formato: "csv"|"xlsx"|"pdf") => { const response=await fetch(`${BASE_URL}/reportes/${anio}/${mes}/${formato}`,{headers:authHeaders(),...requestOptions}); if(!response.ok) throw new Error("No fue posible generar el reporte"); return response.blob(); },
  eliminarPresupuesto: (id: number) => remove(`/presupuestos/${id}`),
  actualizarInversion: (id: number, body: { activo: string; tipo: string; cantidad: number; precio_compra: number; precio_actual: number; broker: string; moneda: string; valores_totales: boolean }) => put<Inversion>(`/inversiones/${id}`, body),
  eliminarInversion: (id: number) => remove(`/inversiones/${id}`),
};

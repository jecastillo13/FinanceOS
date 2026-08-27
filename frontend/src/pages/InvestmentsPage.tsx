import { FormEvent, useEffect, useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BriefcaseBusiness,
  ChartCandlestick,
  Edit3,
  Plus,
  Trash2,
  TrendingUp,
  X,
} from "lucide-react";
import { Cuenta, financeApi, Inversion, Portafolio } from "../api";
import ConfirmDialog from "../components/ConfirmDialog";

const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
export default function InvestmentsPage() {
  const [data, setData] = useState<Portafolio | null>(null);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Inversion | null>(null);
  const [deleting, setDeleting] = useState<Inversion | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [accounts, setAccounts] = useState<Cuenta[]>([]);
  const [initialPosition, setInitialPosition] = useState(true);
  const load = async () => { const [portfolio, cuentas] = await Promise.all([financeApi.inversiones(), financeApi.cuentas()]); setData(portfolio); setAccounts(cuentas); };
  useEffect(() => {
    void load();
  }, []);
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const d = new FormData(e.currentTarget);
    try {
      const body = {
        activo: String(d.get("activo")),
        tipo: String(d.get("tipo")),
        cantidad: Number(d.get("cantidad")),
        precio_compra: Number(d.get("compra")),
        precio_actual: Number(d.get("actual")),
        broker: String(d.get("broker") || ""),
        moneda: String(d.get("moneda")),
        valores_totales: d.get("totales") === "on",
        fecha_apertura: String(d.get("fecha_apertura")),
        es_posicion_inicial: initialPosition,
        cuenta_origen_id: initialPosition ? null : Number(d.get("cuenta_origen_id")),
      };
      if(editing) await financeApi.actualizarInversion(editing.id,body);
      else await financeApi.crearInversion(body);
      setOpen(false);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible guardar");
    } finally {
      setSaving(false);
    }
  };
  const remove=async()=>{if(!deleting)return;setSaving(true);setError("");try{await financeApi.eliminarInversion(deleting.id);setDeleting(null);await load()}catch(err){setError(err instanceof Error?err.message:"No fue posible eliminar")}finally{setSaving(false)}};
  return (
    <section className="module-page">
      <div className="investment-head">
        <div>
          <span className="eyebrow text-cyan-200">DINERO QUE HAS INVERTIDO</span>
          <h2>Inversiones y rendimiento</h2>
          <p>
            Registra posiciones iniciales o nuevas compras. El valor se conserva en su moneda y se consolida en COP.
          </p>
        </div>
        <button className="primary-action" onClick={() => {setEditing(null);setInitialPosition(true);setOpen(true)}}>
          <Plus /> Nueva posición
        </button>
        <div className="market-wave" />
      </div>
      <div className="portfolio-summary">
        <article>
          <span>Valor del portafolio</span>
          <strong>{cop.format(data?.valor_total_cop ?? 0)}</strong>
          <small>
            <TrendingUp /> Consolidado en COP
          </small>
        </article>
        <article>
          <span>Capital invertido</span>
          <strong>{cop.format(data?.costo_total_cop ?? 0)}</strong>
          <small>
            <BriefcaseBusiness /> Base de costo
          </small>
        </article>
        <article
          className={
            (data?.ganancia_total_cop ?? 0) >= 0 ? "positive" : "negative"
          }
        >
          <span>Ganancia total</span>
          <strong>{cop.format(data?.ganancia_total_cop ?? 0)}</strong>
          <small>
            {(data?.ganancia_total_cop ?? 0) >= 0 ? (
              <ArrowUpRight />
            ) : (
              <ArrowDownRight />
            )}
            {(data?.rentabilidad ?? 0).toFixed(2)}% de rentabilidad
          </small>
        </article>
      </div>
      <div className="positions-grid">
        {data?.posiciones.map((item, index) => (
          <article className="position-card" key={item.id}>
            <div className="flex items-start justify-between">
              <span className={`ticker ticker-${index % 4}`}>
                {item.activo.slice(0, 4).toUpperCase()}
              </span>
              <span
                className={
                  item.ganancia >= 0 ? "return positive" : "return negative"
                }
              >
                {item.ganancia >= 0 ? "+" : ""}
                {item.rentabilidad.toFixed(2)}%
              </span>
            </div>
            <div>
              <p>
                {item.tipo} · {item.broker || "Sin broker"}
              </p>
              <h3>{item.activo}</h3>
            </div>
            <div className="position-value">
              <span>Valor actual</span>
              <strong>
                {new Intl.NumberFormat("es-CO", {
                  style: "currency",
                  currency: item.moneda,
                }).format(item.valor)}
              </strong>
            </div>
            <div className="position-foot">
              <span>{item.cantidad.toLocaleString("es-CO")} unidades</span>
              <strong className={item.ganancia >= 0 ? "positive" : "negative"}>
                {item.ganancia >= 0 ? "+" : ""}
                {new Intl.NumberFormat("es-CO", {
                  style: "currency",
                  currency: item.moneda,
                }).format(item.ganancia)}
              </strong>
            </div>
            <small>{item.es_posicion_inicial ? "Posición inicial" : `Pagada desde ${item.cuenta_origen}`}</small>
            <div className="flex gap-2"><button className="ghost-action flex-1" onClick={()=>{setEditing(item);setInitialPosition(item.es_posicion_inicial);setOpen(true)}}><Edit3/> Editar</button><button className="ghost-action" title="Eliminar" onClick={()=>setDeleting(item)}><Trash2/></button></div>
          </article>
        ))}
        {!data?.posiciones.length && (
          <div className="empty-state positions-empty">
            <ChartCandlestick />
            <h3>Tu portafolio comienza aquí</h3>
            <p>Registra tu primera inversión para seguir su rendimiento.</p>
          </div>
        )}
      </div>
      {open && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar"
            onClick={() => {setOpen(false);setEditing(null)}}
          />
          <form className="modern-modal" onSubmit={submit}>
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">{editing?"EDITAR":"NUEVA"} POSICIÓN</span>
                <h3>{editing?"Actualiza la inversión":"Registra una inversión"}</h3>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => {setOpen(false);setEditing(null)}}
              >
                <X />
              </button>
            </div>
            {error && <p className="form-error">{error}</p>}
            <div className="form-grid">
              <label><input type="radio" checked={initialPosition} disabled={Boolean(editing)} onChange={()=>setInitialPosition(true)}/> Ya la tenía antes de usar FinanceOS</label>
              <label><input type="radio" checked={!initialPosition} disabled={Boolean(editing)} onChange={()=>setInitialPosition(false)}/> Comprar con dinero de una cuenta</label>
            </div>
            <p className="form-hint">{initialPosition ? "Úsalo para saldos históricos. Evita dejar el mismo dinero también como efectivo en otra cuenta." : "FinanceOS descontará el costo de la cuenta, pero no lo contará como gasto: el efectivo se convierte en inversión."}</p>
            {!initialPosition && <label>Cuenta que paga<select name="cuenta_origen_id" required defaultValue={editing?.cuenta_origen_id}>{accounts.map(account=><option key={account.id} value={account.id}>{account.nombre} · {account.saldo} {account.moneda}</option>)}</select></label>}
            <label>Fecha de compra o saldo inicial<input name="fecha_apertura" type="date" required defaultValue={editing?.fecha_apertura || new Date().toISOString().slice(0,10)}/></label>
            <div className="form-grid">
              <label>
                Activo
                <input name="activo" required placeholder="Ej: VOO" defaultValue={editing?.activo}/>
              </label>
              <label>
                Tipo
                <select name="tipo" defaultValue={editing?.tipo||"ETF"}>
                  <option>ETF</option>
                  <option>Acción</option>
                  <option>Criptomoneda</option>
                  <option>CDT</option>
                  <option>Fondo</option>
                </select>
              </label>
            </div>
            <div className="form-grid">
              <label>
                Cantidad
                <input
                  name="cantidad"
                  type="number"
                  min="0.00000001"
                  step="any"
                  required
                  defaultValue={editing?.cantidad}
                />
              </label>
              <label>
                Moneda
                <select name="moneda" defaultValue={editing?.moneda||"USD"}>
                  <option>USD</option>
                  <option>COP</option>
                  <option>EUR</option>
                </select>
              </label>
            </div>
            <div className="form-grid">
              <label>
                Precio o costo de compra
                <input
                  name="compra"
                  type="number"
                  min="0.01"
                  step="any"
                  required
                  defaultValue={editing?.precio_compra}
                />
              </label>
              <label>
                Precio o valor actual
                <input
                  name="actual"
                  type="number"
                  min="0.01"
                  step="any"
                  required
                  defaultValue={editing?.precio_actual}
                />
              </label>
            </div>
            <label>
              Broker
              <input name="broker" placeholder="Ej: Hapi" defaultValue={editing?.broker}/>
            </label>
            <label className="check-label">
              <input name="totales" type="checkbox" defaultChecked={editing?.valores_totales}/> Los valores son totales
              reportados por el broker
            </label>
            <button className="modal-submit" disabled={saving}>
              <ChartCandlestick />
              {saving ? "Guardando…" : editing?"Guardar cambios":"Agregar al portafolio"}
            </button>
          </form>
        </div>
      )}
      {deleting&&<ConfirmDialog title="Eliminar inversión" description={deleting.es_posicion_inicial ? `Se eliminará ${deleting.activo} del portafolio.` : `Se eliminará ${deleting.activo} y el costo de compra volverá a ${deleting.cuenta_origen}.`} busy={saving} onCancel={()=>setDeleting(null)} onConfirm={()=>void remove()}/>}
    </section>
  );
}

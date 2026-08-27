import { FormEvent, useEffect, useState } from "react";
import {
  CalendarClock,
  Check,
  Clock3,
  CreditCard,
  Edit3,
  Plus,
  Repeat2,
  Trash2,
  X,
} from "lucide-react";
import { Categoria, Cuenta, financeApi, GastoRecurrente } from "../api";
import ConfirmDialog from "../components/ConfirmDialog";

export default function RecurringPage({ accounts }: { accounts: Cuenta[] }) {
  const [items, setItems] = useState<GastoRecurrente[]>([]);
  const [categories, setCategories] = useState<Categoria[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<GastoRecurrente | null>(null);
  const [deleting, setDeleting] = useState<GastoRecurrente | null>(null);
  const [paying, setPaying] = useState<GastoRecurrente | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const load = async () => {
    const [r, c] = await Promise.all([
      financeApi.recurrentes(),
      financeApi.categorias(),
    ]);
    setItems(r);
    setCategories(c.filter((x) => x.tipo.toLowerCase() === "gasto"));
  };
  useEffect(() => {
    void load();
  }, []);
  const create = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const d = new FormData(e.currentTarget);
    try {
      const body = {
        nombre: String(d.get("nombre")),
        valor: Number(d.get("valor")),
        frecuencia: String(d.get("frecuencia")),
        proxima_fecha_pago: String(d.get("fecha")),
        categoria_id: Number(d.get("categoria")),
      };
      if (editing) await financeApi.actualizarRecurrente(editing.id, {...body, activa:true});
      else await financeApi.crearRecurrente(body);
      setOpen(false);
      setEditing(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible guardar");
    } finally {
      setSaving(false);
    }
  };
  const remove = async () => { if(!deleting)return; setSaving(true); setError(""); try { await financeApi.eliminarRecurrente(deleting.id); setDeleting(null); await load(); } catch(err) { setError(err instanceof Error?err.message:"No fue posible eliminar"); } finally { setSaving(false); } };
  const pay = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!paying) return;
    setSaving(true);
    setError("");
    const d = new FormData(e.currentTarget);
    try {
      await financeApi.pagarRecurrente(paying.id, {
        cuenta_id: Number(d.get("cuenta")),
        fecha_pago: String(d.get("fecha")),
      });
      setPaying(null);
      await load();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No fue posible registrar el pago",
      );
    } finally {
      setSaving(false);
    }
  };
  return (
    <section className="module-page">
      <div className="module-hero recurring-hero">
        <div>
          <span className="eyebrow text-cyan-200">
            LO QUE DEBES PAGAR DE NUEVO
          </span>
          <h2>Pagos recurrentes</h2>
          <p>
            Programa servicios, suscripciones y cuotas. Al marcar un pago, se crea el gasto correspondiente.
          </p>
        </div>
        <button className="primary-action" onClick={() => {setEditing(null);setOpen(true)}}>
          <Plus /> Nuevo recurrente
        </button>
        <div className="module-orb" />
      </div>
      <div className="recurring-grid">
        {items.map((item, index) => {
          const due = new Date(`${item.proxima_fecha_pago}T00:00:00`);
          const days = Math.ceil((due.getTime() - Date.now()) / 86400000);
          return (
            <article className="recurring-card" key={item.id}>
              <div className="flex items-start justify-between">
                <span className={`recurring-logo recurring-${index % 4}`}>
                  <Repeat2 />
                </span>
                <span className={days <= 5 ? "due-chip urgent" : "due-chip"}>
                  <Clock3 />{" "}
                  {days < 0 ? "Vencido" : days === 0 ? "Hoy" : `${days} días`}
                </span>
              </div>
              <div>
                <p>
                  {item.categoria} · {item.frecuencia}
                </p>
                <h3>{item.nombre}</h3>
                <strong>
                  {new Intl.NumberFormat("es-CO", {
                    style: "currency",
                    currency: "COP",
                  }).format(item.valor)}
                </strong>
              </div>
              <div className="due-date">
                <CalendarClock />
                <span>
                  Próximo pago
                  <strong>
                    {due.toLocaleDateString("es-CO", {
                      day: "numeric",
                      month: "long",
                    })}
                  </strong>
                </span>
              </div>
              <div className="flex gap-2"><button className="pay-action flex-1" onClick={() => setPaying(item)}><Check /> Marcar como pagado</button><button className="ghost-action" title="Editar" onClick={()=>{setEditing(item);setOpen(true)}}><Edit3/></button><button className="ghost-action" title="Eliminar" onClick={()=>setDeleting(item)}><Trash2/></button></div>
            </article>
          );
        })}
        {!items.length && (
          <div className="empty-state recurring-empty">
            <Repeat2 />
            <h3>Sin pagos recurrentes</h3>
            <p>Programa tus obligaciones frecuentes.</p>
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
          <form className="modern-modal" onSubmit={create}>
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">{editing?"EDITAR":"NUEVO"} RECURRENTE</span>
                <h3>{editing?"Actualiza el pago":"Programa un pago"}</h3>
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
            <label>
              Nombre
              <input name="nombre" required placeholder="Ej: Arriendo" defaultValue={editing?.nombre}/>
            </label>
            <div className="form-grid">
              <label>
                Valor
                <input
                  name="valor"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                  defaultValue={editing?.valor}
                />
              </label>
              <label>
                Frecuencia
                <select name="frecuencia" defaultValue={editing?.frecuencia||"Mensual"}>
                  <option>Mensual</option>
                  <option>Quincenal</option>
                  <option>Semanal</option>
                  <option>Anual</option>
                </select>
              </label>
            </div>
            <div className="form-grid">
              <label>
                Próximo pago
                <input name="fecha" type="date" required defaultValue={editing?.proxima_fecha_pago}/>
              </label>
              <label>
                Categoría
                <select name="categoria" defaultValue={editing?.categoria_id}>
                  {categories.map((x) => (
                    <option value={x.id} key={x.id}>
                      {x.nombre}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button className="modal-submit" disabled={saving}>
              <Repeat2 />
              {saving ? "Guardando…" : editing?"Guardar cambios":"Programar gasto"}
            </button>
          </form>
        </div>
      )}
      {deleting&&<ConfirmDialog title="Eliminar gasto recurrente" description={`Se eliminará ${deleting.nombre}. Los movimientos de pagos anteriores se conservarán para no alterar tu historial.`} busy={saving} onCancel={()=>setDeleting(null)} onConfirm={()=>void remove()}/>}
      {paying && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar"
            onClick={() => setPaying(null)}
          />
          <form className="modern-modal" onSubmit={pay}>
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">CONFIRMAR PAGO</span>
                <h3>{paying.nombre}</h3>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setPaying(null)}
              >
                <X />
              </button>
            </div>
            {error && <p className="form-error">{error}</p>}
            <label>
              Cuenta de pago
              <select name="cuenta">
                {accounts.map((x) => (
                  <option value={x.id} key={x.id}>
                    {x.nombre} ({x.moneda})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Fecha del pago
              <input
                name="fecha"
                type="date"
                defaultValue={new Date().toISOString().slice(0, 10)}
                required
              />
            </label>
            <button className="modal-submit" disabled={saving}>
              <CreditCard />
              {saving ? "Registrando…" : "Pagar y crear movimiento"}
            </button>
          </form>
        </div>
      )}
    </section>
  );
}

import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ChartNoAxesCombined,
  Plus,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import { Categoria, financeApi, Presupuesto } from "../api";
import ConfirmDialog from "../components/ConfirmDialog";

const now = new Date();
const months = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];
const money = (value: number) =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(value);

export default function BudgetsPage() {
  const [year, setYear] = useState(now.getFullYear()),
    [month, setMonth] = useState(now.getMonth() + 1);
  const [items, setItems] = useState<Presupuesto[]>([]),
    [categories, setCategories] = useState<Categoria[]>([]);
  const [open, setOpen] = useState(false),
    [deleting, setDeleting] = useState<Presupuesto | null>(null),
    [saving, setSaving] = useState(false),
    [error, setError] = useState("");
  const load = async () => {
    try {
      const [b, c] = await Promise.all([
        financeApi.presupuestos(year, month),
        financeApi.categorias(),
      ]);
      setItems(b);
      setCategories(c.filter((x) => x.tipo.toLowerCase() === "gasto"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible cargar");
    }
  };
  useEffect(() => {
    void load();
  }, [year, month]);
  const totals = useMemo(
    () =>
      items.reduce(
        (a, x) => ({ budget: a.budget + x.valor, spent: a.spent + x.gastado }),
        { budget: 0, spent: 0 },
      ),
    [items],
  );
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const d = new FormData(e.currentTarget);
    try {
      await financeApi.crearPresupuesto({
        anio: year,
        mes: month,
        categoria_id: Number(d.get("categoria")),
        valor: Number(d.get("valor")),
      });
      setOpen(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible guardar");
    } finally {
      setSaving(false);
    }
  };
  const remove = async () => {
    if (!deleting) return;
    setSaving(true);
    setError("");
    try {
      await financeApi.eliminarPresupuesto(deleting.id);
      setDeleting(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No fue posible eliminar");
    } finally {
      setSaving(false);
    }
  };
  return (
    <section className="module-page">
      <div className="module-hero budget-hero">
        <div>
          <span className="eyebrow text-cyan-200">
            PLANIFICACIÓN INTELIGENTE
          </span>
          <h2>Presupuestos vivos</h2>
          <p>Decide antes de gastar y observa el avance en tiempo real.</p>
        </div>
        <button
          className="primary-action"
          onClick={() => setOpen(true)}
          disabled={!categories.length}
        >
          <Plus size={17} /> Nuevo presupuesto
        </button>
        <div className="module-orb" />
      </div>
      {error && <p className="form-error">{error}</p>}
      <div className="period-control">
        <select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
        >
          {months.map((m, i) => (
            <option value={i + 1} key={m}>
              {m}
            </option>
          ))}
        </select>
        <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[year - 1, year, year + 1].map((y) => (
            <option key={y}>{y}</option>
          ))}
        </select>
        <div>
          <span>Planificado</span>
          <strong>{money(totals.budget)}</strong>
        </div>
        <div>
          <span>Consumido</span>
          <strong>
            {totals.budget
              ? Math.round((totals.spent / totals.budget) * 100)
              : 0}
            %
          </strong>
        </div>
      </div>
      <div className="budget-grid">
        {items.map((item, index) => {
          const pct = Math.min(
              item.valor ? (item.gastado / item.valor) * 100 : 0,
              100,
            ),
            warning = pct >= 80;
          return (
            <article key={item.id} className="budget-card">
              <div className="flex items-start justify-between">
                <span className={`budget-symbol symbol-${index % 4}`}>
                  <ChartNoAxesCombined />
                </span>
                <div className="flex items-center gap-2">
                  {warning ? (
                    <span className="warning-chip">
                      <AlertTriangle /> Atención
                    </span>
                  ) : (
                    <span className="safe-chip">
                      <ShieldCheck /> Saludable
                    </span>
                  )}
                  <button
                    className="inline-delete"
                    title="Eliminar presupuesto"
                    onClick={() => setDeleting(item)}
                  >
                    <Trash2 />
                  </button>
                </div>
              </div>
              <h3>{item.categoria}</h3>
              <div className="budget-values">
                <strong>{money(item.gastado)}</strong>
                <span>de {money(item.valor)}</span>
              </div>
              <div className="progress-track">
                <i style={{ width: `${pct}%` }} />
              </div>
              <p>
                {Math.round(pct)}% utilizado ·{" "}
                {money(Math.max(0, item.valor - item.gastado))} disponibles
              </p>
            </article>
          );
        })}
        {!items.length && (
          <div className="empty-state budget-empty">
            <ChartNoAxesCombined />
            <h3>Este mes está libre</h3>
            <p>Crea tu primer presupuesto para comenzar a planificar.</p>
          </div>
        )}
      </div>
      {deleting && (
        <ConfirmDialog
          title="Eliminar presupuesto"
          description={`Se eliminará el límite de ${deleting.categoria}; los movimientos existentes no cambiarán.`}
          busy={saving}
          onCancel={() => setDeleting(null)}
          onConfirm={() => void remove()}
        />
      )}
      {open && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar"
            onClick={() => setOpen(false)}
          />
          <form className="modern-modal" onSubmit={submit}>
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">NUEVO PRESUPUESTO</span>
                <h3>Define tu límite</h3>
              </div>
              <button
                type="button"
                className="icon-button"
                onClick={() => setOpen(false)}
              >
                <X />
              </button>
            </div>
            <label>
              Categoría
              <select name="categoria" required>
                {categories.map((x) => (
                  <option value={x.id} key={x.id}>
                    {x.icono} {x.nombre}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Valor máximo
              <input name="valor" type="number" min="1" step="0.01" required />
            </label>
            <button className="modal-submit" disabled={saving}>
              <ChartNoAxesCombined />
              {saving ? "Guardando…" : "Crear presupuesto"}
            </button>
          </form>
        </div>
      )}
    </section>
  );
}

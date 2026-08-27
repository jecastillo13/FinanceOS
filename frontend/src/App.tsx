import { Fragment, lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  Bell,
  ChartNoAxesCombined,
  ChevronRight,
  CircleDollarSign,
  Command,
  CreditCard,
  LayoutDashboard,
  Menu,
  FileChartColumn,
  Plus,
  ReceiptText,
  RefreshCw,
  Repeat2,
  Search,
  Settings,
  Sparkles,
  Target,
  TrendingUp,
  WalletCards,
  X,
  Tags,
  Globe2,
  Camera,
  ShieldCheck,
  UserPlus,
  HelpCircle,
  CheckCircle2,
  Gauge,
  Info,
} from "lucide-react";
import { Cuenta, financeApi, Graficas, Resumen, Usuario } from "./api";
import AccountsPage from "./pages/AccountsPage";
import MovementsPage from "./pages/MovementsPage";
import BudgetsPage from "./pages/BudgetsPage";
import GoalsPage from "./pages/GoalsPage";
import InvestmentsPage from "./pages/InvestmentsPage";
import SettingsPage from "./pages/SettingsPage";
import RecurringPage from "./pages/RecurringPage";
import TransfersPage from "./pages/TransfersPage";
import ReportsPage from "./pages/ReportsPage";
import CategoriesPage from "./pages/CategoriesPage";
import CurrenciesPage from "./pages/CurrenciesPage";
import CardsPage from "./pages/CardsPage";
import AuthPage from "./pages/AuthPage";

const DashboardCharts = lazy(() => import("./DashboardCharts"));
const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const nav = [
  { key: "Centro", label: "Inicio", description: "Resumen y próximos pasos", group: "Resumen", Icon: LayoutDashboard },
  { key: "Cuentas", label: "Cuentas y saldos", description: "Dónde está tu dinero", group: "Registrar", Icon: WalletCards },
  { key: "Tarjetas", label: "Tarjetas y compras", description: "Medios de pago y avisos", group: "Registrar", Icon: CreditCard },
  { key: "Movimientos", label: "Ingresos y gastos", description: "Todo lo que entra y sale", group: "Registrar", Icon: ReceiptText },
  { key: "Recurrentes", label: "Pagos recurrentes", description: "Obligaciones que se repiten", group: "Registrar", Icon: Repeat2 },
  { key: "Transferencias", label: "Transferencias", description: "Mover dinero entre cuentas", group: "Registrar", Icon: ArrowLeftRight },
  { key: "Presupuestos", label: "Presupuestos", description: "Límites mensuales de gasto", group: "Planear", Icon: ChartNoAxesCombined },
  { key: "Metas", label: "Metas", description: "Ahorros y pagos futuros", group: "Planear", Icon: Target },
  { key: "Inversiones", label: "Inversiones", description: "Portafolio y rendimiento", group: "Planear", Icon: TrendingUp },
  { key: "Categorías", label: "Categorías", description: "Clasificar ingresos y gastos", group: "Revisar", Icon: Tags },
  { key: "Monedas", label: "Monedas y tasas", description: "Conversión a COP", group: "Revisar", Icon: Globe2 },
  { key: "Reportes", label: "Reportes", description: "Resumen y exportación", group: "Revisar", Icon: FileChartColumn },
  { key: "Configuración", label: "Configuración", description: "Seguridad, usuarios y datos", group: "Sistema", Icon: Settings },
] as const;

type FinancialInsight = {
  title: string;
  detail: string;
  metric: string;
  tone: "good" | "watch" | "neutral";
  page: string;
  action: string;
};

function buildFinancialInsights(
  summary: Resumen | null,
  charts: Graficas | null,
): FinancialInsight[] {
  if (!summary) return [];

  const insights: FinancialInsight[] = [];
  const hasMonthlyActivity = summary.ingresos > 0 || summary.gastos > 0;
  const spendingRate = summary.ingresos > 0 ? (summary.gastos / summary.ingresos) * 100 : null;
  const investmentRate = summary.patrimonio > 0 ? (summary.inversiones_cop / summary.patrimonio) * 100 : 0;

  if (!hasMonthlyActivity) {
    insights.push({ title: "Aún no hay flujo para evaluar", detail: "Registra ingresos y gastos del mes para calcular capacidad de ahorro y detectar desviaciones.", metric: "0 movimientos del mes", tone: "neutral", page: "Movimientos", action: "Registrar actividad" });
  } else if (summary.balance < 0) {
    insights.push({ title: "Tus gastos superan tus ingresos", detail: `El déficit del mes es ${cop.format(Math.abs(summary.balance))}. Conviene revisar primero las categorías con mayor gasto.`, metric: `${Math.round(spendingRate ?? 0)}% de tus ingresos gastado`, tone: "watch", page: "Presupuestos", action: "Revisar presupuesto" });
  } else {
    const savingsRate = summary.ingresos > 0 ? (summary.balance / summary.ingresos) * 100 : 0;
    insights.push({ title: "Tu flujo mensual está en positivo", detail: `Después de gastos conservas ${cop.format(summary.balance)}. Esta es tu capacidad de ahorro estimada del mes.`, metric: `${Math.round(savingsRate)}% de ahorro mensual`, tone: "good", page: "Metas", action: "Asignar a una meta" });
  }

  const distribution = [...(charts?.distribucion ?? [])].sort((a, b) => b.saldo_cop - a.saldo_cop);
  const largest = distribution[0];
  const liquidTotal = distribution.reduce((total, item) => total + Math.max(0, item.saldo_cop), 0);
  const concentration = largest && liquidTotal > 0 ? (largest.saldo_cop / liquidTotal) * 100 : 0;

  insights.push({
    title: concentration >= 70 ? "Tu liquidez está concentrada" : "Tu liquidez está distribuida",
    detail: largest ? `${largest.cuenta} representa aproximadamente ${Math.round(concentration)}% del dinero disponible entre tus cuentas.` : "Crea al menos una cuenta para medir liquidez y concentración de tu dinero.",
    metric: largest ? `${Math.round(concentration)}% en ${largest.cuenta}` : "Sin cuentas para analizar",
    tone: concentration >= 70 ? "watch" : "neutral",
    page: "Cuentas",
    action: "Ver cuentas",
  });

  const topExpense = [...(charts?.gastos_categoria ?? [])]
    .map((item) => ({ name: item.categoria, value: item.total ?? item.valor ?? 0 }))
    .sort((a, b) => b.value - a.value)[0];

  insights.push({
    title: topExpense ? "Esta categoría lidera tus gastos" : "Gastos por categorizar",
    detail: topExpense ? `${topExpense.name} acumula ${cop.format(topExpense.value)} este mes. Compáralo con tu presupuesto antes de tomar decisiones.` : "Cuando registres gastos, FinanceOS mostrará cuál categoría consume más dinero.",
    metric: topExpense ? topExpense.name : "Sin gastos clasificados",
    tone: "neutral",
    page: topExpense ? "Categorías" : "Movimientos",
    action: topExpense ? "Ver categorías" : "Registrar un gasto",
  });

  insights.push({
    title: investmentRate > 0 ? "Tu patrimonio también está invertido" : "No hay inversiones registradas",
    detail: investmentRate > 0 ? `${cop.format(summary.inversiones_cop)} está registrado en inversiones y se incluye en tu patrimonio consolidado.` : "Puedes registrar posiciones iniciales sin inventar movimientos históricos y empezar el seguimiento desde hoy.",
    metric: `${Math.round(investmentRate)}% del patrimonio invertido`,
    tone: "neutral",
    page: "Inversiones",
    action: "Ver inversiones",
  });

  return insights;
}

function Metric({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: number;
  icon: typeof TrendingUp;
  accent: string;
}) {
  return (
    <article className="metric-card group">
      <div className="flex items-center gap-3">
        <span className={`metric-icon ${accent}`}>
          <Icon size={17} />
        </span>
        <p>{label}</p>
      </div>
      <strong>{cop.format(value)}</strong>
      <span className="metric-line" />
    </article>
  );
}

function Skeletons() {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {Array.from({ length: 3 }).map((_, i) => (
        <div
          key={i}
          className="h-28 animate-pulse rounded-[1.75rem] bg-white/[.045]"
        />
      ))}
    </div>
  );
}

function WelcomeCenter({
  user,
  onClose,
  onNavigate,
}: {
  user: Usuario;
  onClose: () => void;
  onNavigate: (page: string, anchor?: string) => void;
}) {
  const admin = user.rol === "superadmin";
  return (
    <div
      className="welcome-layer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-title"
    >
      <div className="welcome-backdrop" />
      <section className="welcome-center">
        <button
          className="welcome-close"
          aria-label="Cerrar guía"
          onClick={onClose}
        >
          <X />
        </button>
        <div className="welcome-intro">
          <span className="welcome-logo">
            <CircleDollarSign />
          </span>
          <div>
            <span className="eyebrow">PRIMEROS PASOS · FINANCEOS</span>
            <h2 id="welcome-title">Hola, {user.nombre}</h2>
            <p>
              Todo está conectado. Elige una acción para comenzar y confirma
              siempre los datos antes de afectar tus saldos.
            </p>
          </div>
        </div>
        <div className="welcome-grid">
          <button
            onClick={() => onNavigate("Movimientos", "captura-comprobante")}
          >
            <span className="welcome-action cyan">
              <Camera />
            </span>
            <div>
              <strong>Fotografiar una factura</strong>
              <p>
                En celular abre la cámara; en computador también puedes subir
                PDF o imagen.
              </p>
            </div>
            <CheckCircle2 />
          </button>
          <button onClick={() => onNavigate("Configuración", "mfa-seguridad")}>
            <span className="welcome-action violet">
              <ShieldCheck />
            </span>
            <div>
              <strong>Activar doble seguridad</strong>
              <p>
                Conecta Google o Microsoft Authenticator y protege cada inicio
                de sesión.
              </p>
            </div>
            <CheckCircle2 />
          </button>
          {admin && (
            <button
              onClick={() => onNavigate("Configuración", "usuarios-acceso")}
            >
              <span className="welcome-action orange">
                <UserPlus />
              </span>
              <div>
                <strong>Crear otro usuario</strong>
                <p>
                  Tú eres administrador. Cada persona tendrá datos financieros
                  totalmente separados.
                </p>
              </div>
              <CheckCircle2 />
            </button>
          )}
          <button onClick={() => onNavigate("Cuentas")}>
            <span className="welcome-action mint">
              <WalletCards />
            </span>
            <div>
              <strong>Revisar tus cuentas</strong>
              <p>Verifica saldos y monedas antes de registrar movimientos.</p>
            </div>
            <CheckCircle2 />
          </button>
        </div>
        <div className="welcome-note">
          <ShieldCheck />
          <p>
            <strong>Privacidad por diseño.</strong> FinanceOS nunca mezcla
            información entre usuarios. Una fotografía no crea un movimiento
            hasta que tú confirmes cuenta, categoría y valor.
          </p>
        </div>
        <button className="welcome-enter" onClick={onClose}>
          Entrar al Centro Financiero <ChevronRight />
        </button>
      </section>
    </div>
  );
}

function FinanceApp({
  user,
  onLogout,
}: {
  user: Usuario;
  onLogout: () => Promise<void>;
}) {
  const [menu, setMenu] = useState(false);
  const [welcome, setWelcome] = useState(true);
  const [active, setActive] = useState<string>("Centro");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<Resumen | null>(null);
  const [charts, setCharts] = useState<Graficas | null>(null);
  const [accounts, setAccounts] = useState<Cuenta[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [intelligenceOpen, setIntelligenceOpen] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [resumen, graficas, cuentas] = await Promise.all([
        financeApi.resumen(),
        financeApi.graficas(),
        financeApi.cuentas(),
      ]);
      setSummary(resumen);
      setCharts(graficas);
      setAccounts(cuentas);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "No fue posible conectar con FinanceOS.",
      );
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") {
        setSearchOpen(false);
        setNotificationsOpen(false);
        setIntelligenceOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const financialInsights = buildFinancialInsights(summary, charts);
  const primaryInsight = financialInsights[0];
  const navigate = (page: string, anchor?: string) => {
    setActive(page);
    setWelcome(false);
    setMenu(false);
    if (anchor)
      setTimeout(
        () =>
          document
            .getElementById(anchor)
            ?.scrollIntoView({ behavior: "smooth", block: "center" }),
        180,
      );
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="noise" />
      {menu && (
        <button
          aria-label="Cerrar menú"
          className="fixed inset-0 z-40 bg-[#02050d]/70 backdrop-blur-md lg:hidden"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={`nav-rail ${menu ? "nav-open" : ""}`} aria-label="Navegación principal">
        <div className="nav-brand">
          <div className="brand-orb"><CircleDollarSign size={25} /></div>
          <div className="nav-brand-copy"><strong>FinanceOS</strong><span>Finanzas claras</span></div>
        </div>
        <nav>
          {nav.map((item, index) => (
            <Fragment key={item.key}>
              {(index === 0 || nav[index - 1].group !== item.group) && <span className="nav-group">{item.group}</span>}
              <button
                className={active === item.key ? "active" : ""}
                aria-label={`${item.label}: ${item.description}`}
                onClick={() => { setActive(item.key); setMenu(false); }}
              >
                <item.Icon size={19} />
                <span><strong>{item.label}</strong><small>{item.description}</small></span>
                {active === item.key && <i />}
              </button>
            </Fragment>
          ))}
        </nav>
        <div className="mt-auto flex flex-col items-center gap-3">
          <button
            className="rail-help"
            title="Guía de funciones"
            aria-label="Abrir guía de funciones"
            onClick={() => {
              setWelcome(true);
              setMenu(false);
            }}
          >
            <HelpCircle />
          </button>
          <span className="online-dot" title="API conectada" />
          <button
            aria-label="Cerrar navegación"
            className="rail-close lg:hidden"
            onClick={() => setMenu(false)}
          >
            <X size={18} />
          </button>
          <button
            className="avatar"
            title={`${user.nombre} · Cerrar sesión`}
            aria-label="Cerrar sesión"
            onClick={() => void onLogout()}
          >
            {user.nombre.trim().slice(0, 2).toUpperCase()}
          </button>
        </div>
      </aside>

      <main className="relative z-10 min-h-screen px-4 pb-20 lg:px-8 xl:px-12">
        <header className="topbar mx-auto max-w-[1480px]">
          <div className="flex items-center gap-3">
            <button
              aria-label="Abrir menú"
              className="icon-button lg:hidden"
              onClick={() => setMenu(true)}
            >
              <Menu size={20} />
            </button>
            <div>
              <span className="eyebrow">FINANCEOS · EN LÍNEA</span>
              <h1>{nav.find((item) => item.key === active)?.label ?? active}</h1>
            </div>
          </div>
          <button className="command-bar" onClick={() => setSearchOpen(true)}>
            <Search size={17} />
            <span>Buscar en FinanceOS</span>
            <kbd>
              <Command size={12} /> K
            </kbd>
          </button>
          <div className="flex gap-2">
            <button
              aria-label="Abrir guía"
              title="Guía de funciones"
              className="icon-button"
              onClick={() => setWelcome(true)}
            >
              <HelpCircle size={18} />
            </button>
            <button
              aria-label="Notificaciones"
              className="icon-button"
              onClick={() => setNotificationsOpen(true)}
            >
              <Bell size={18} />
              <i className="notification" />
            </button>
            <button
              aria-label="Actualizar"
              onClick={() => void load()}
              className="icon-button hover:rotate-45"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1480px]">
          {error && (
            <div className="error-banner">
              {error}. Verifica que FastAPI esté activo en el puerto 8000.
            </div>
          )}

          {active === "Centro" ? (
            <>
              <section className="hero-grid">
                <article className="wealth-card">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="relative z-10 flex h-full flex-col justify-between">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="eyebrow text-cyan-200">
                          PATRIMONIO TOTAL
                        </span>
                        <div className="mt-3 flex items-center gap-2">
                          <span className="live-pill">
                            <i /> EN VIVO
                          </span>
                          <span className="text-xs text-white/40">
                            Consolidado en COP
                          </span>
                        </div>
                      </div>
                      <span className="sparkle">
                        <Sparkles size={20} />
                      </span>
                    </div>
                    <div>
                      <p className="wealth-value">
                        {loading ? "—" : cop.format(summary?.patrimonio ?? 0)}
                      </p>
                      <div className="mt-6 flex flex-wrap gap-3">
                        <button
                          className="primary-action"
                          onClick={() => setActive("Movimientos")}
                        >
                          <Plus size={17} /> Nuevo movimiento
                        </button>
                        <button
                          className="ghost-action"
                          onClick={() => setActive("Transferencias")}
                        >
                          <ArrowLeftRight size={17} /> Transferir
                        </button>
                      </div>
                    </div>
                  </div>
                </article>

                <div className="pulse-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">ESTE MES</span>
                      <h2>Ingresos y gastos</h2>
                    </div>
                    <span className="pulse-ring">
                      <i />
                    </span>
                  </div>
                  {loading ? (
                    <Skeletons />
                  ) : (
                    <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                      <Metric
                        label="Balance"
                        value={summary?.balance ?? 0}
                        icon={TrendingUp}
                        accent="violet"
                      />
                      <Metric
                        label="Ingresos"
                        value={summary?.ingresos ?? 0}
                        icon={ArrowUpRight}
                        accent="mint"
                      />
                      <Metric
                        label="Gastos"
                        value={summary?.gastos ?? 0}
                        icon={ArrowDownRight}
                        accent="coral"
                      />
                    </div>
                  )}
                  <div className="insight-strip">
                    <span>
                      <Sparkles size={15} />
                    </span>
                    <p>
                      <strong>Así se calcula.</strong> Ingresos menos gastos
                      produce el balance del mes.
                    </p>
                    <ChevronRight size={17} />
                  </div>
                </div>
              </section>

              <section className="finance-flow" aria-labelledby="finance-flow-title">
                <div className="finance-flow-heading">
                  <span className="eyebrow">CÓMO FUNCIONA FINANCEOS</span>
                  <h2 id="finance-flow-title">Empieza aquí y sigue estos pasos</h2>
                  <p>Cada paso alimenta al siguiente; no son módulos aislados.</p>
                </div>
                <div className="finance-flow-steps">
                  <button onClick={() => navigate("Cuentas")}>
                    <i>1</i><span><strong>Crea tus cuentas</strong><small>Registra los saldos con los que empiezas.</small></span><ChevronRight />
                  </button>
                  <button onClick={() => navigate("Movimientos")}>
                    <i>2</i><span><strong>Registra lo que entra y sale</strong><small>Cada operación actualiza cuentas y categorías.</small></span><ChevronRight />
                  </button>
                  <button onClick={() => navigate("Presupuestos")}>
                    <i>3</i><span><strong>Planea tu dinero</strong><small>Define presupuestos, pagos y metas.</small></span><ChevronRight />
                  </button>
                  <button onClick={() => navigate("Reportes")}>
                    <i>4</i><span><strong>Revisa los resultados</strong><small>Comprende el mes y exporta cuando lo necesites.</small></span><ChevronRight />
                  </button>
                </div>
              </section>

              <Suspense
                fallback={
                  <div className="mt-5 grid gap-5 xl:grid-cols-[1.65fr_1fr]">
                    <div className="chart-skeleton" />
                    <div className="chart-skeleton" />
                  </div>
                }
              >
                <DashboardCharts
                  charts={charts}
                  patrimonio={summary?.patrimonio ?? 0}
                />
              </Suspense>

              <section className="lower-grid">
                <article className="accounts-panel">
                  <div className="panel-heading">
                    <div>
                      <span className="eyebrow">DÓNDE ESTÁ TU DINERO</span>
                      <h2>Tus cuentas</h2>
                    </div>
                    <button
                      className="text-action"
                      onClick={() => setActive("Cuentas")}
                    >
                      Explorar <ChevronRight size={15} />
                    </button>
                  </div>
                  <div className="accounts-track">
                    {accounts.slice(0, 4).map((account, index) => (
                      <div className="account-tile" key={account.id}>
                        <div className="flex items-center justify-between">
                          <span className={`account-logo logo-${index % 4}`}>
                            <CreditCard size={18} />
                          </span>
                          <span className="currency-chip">
                            {account.moneda}
                          </span>
                        </div>
                        <div>
                          <p>{account.nombre}</p>
                          <strong>
                            {new Intl.NumberFormat("es-CO", {
                              style: "currency",
                              currency: account.moneda,
                            }).format(account.saldo)}
                          </strong>
                        </div>
                        <span className="account-glow" />
                      </div>
                    ))}
                  </div>
                </article>
                <article className="ai-panel">
                  <div className="ai-panel-head">
                    <span className="ai-icon"><Sparkles size={21} /></span>
                    <span className="ai-engine-state"><i /> Motor local · datos privados</span>
                  </div>
                  <div className="ai-panel-copy">
                    <span className="eyebrow text-violet-200">
                      ANÁLISIS FINANCIERO
                    </span>
                    <h2>{primaryInsight?.title ?? "Preparando tu análisis"}</h2>
                    <p>
                      {primaryInsight?.detail ?? "FinanceOS está consolidando tu flujo, patrimonio, concentración y gastos."}
                    </p>
                  </div>
                  <div className="ai-analysis-scope" aria-label="Indicadores analizados">
                    <span><Gauge size={15} /> Flujo mensual</span>
                    <span><WalletCards size={15} /> Patrimonio</span>
                    <span><ReceiptText size={15} /> Gastos</span>
                  </div>
                  <button onClick={() => setIntelligenceOpen(true)}>
                    Ver qué está analizando <ChevronRight size={17} />
                  </button>
                </article>
              </section>
            </>
          ) : active === "Cuentas" ? (
            <AccountsPage accounts={accounts} onChanged={load} />
          ) : active === "Tarjetas" ? (
            <CardsPage accounts={accounts} onChanged={load} />
          ) : active === "Categorías" ? (
            <CategoriesPage />
          ) : active === "Movimientos" ? (
            <MovementsPage accounts={accounts} />
          ) : active === "Recurrentes" ? (
            <RecurringPage accounts={accounts} />
          ) : active === "Transferencias" ? (
            <TransfersPage accounts={accounts} onChanged={load} />
          ) : active === "Presupuestos" ? (
            <BudgetsPage />
          ) : active === "Metas" ? (
            <GoalsPage />
          ) : active === "Inversiones" ? (
            <InvestmentsPage />
          ) : active === "Monedas" ? (
            <CurrenciesPage />
          ) : active === "Reportes" ? (
            <ReportsPage />
          ) : (
            <SettingsPage />
          )}
        </div>
      </main>
      {welcome && (
        <WelcomeCenter
          user={user}
          onClose={() => setWelcome(false)}
          onNavigate={navigate}
        />
      )}
      {searchOpen && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar búsqueda"
            onClick={() => setSearchOpen(false)}
          />
          <section className="modern-modal navigation-modal">
            <div className="navigation-modal-head flex items-start justify-between">
              <div>
                <span className="eyebrow">NAVEGACIÓN RÁPIDA</span>
                <h3>¿Qué quieres abrir?</h3>
              </div>
              <button
                className="icon-button"
                onClick={() => setSearchOpen(false)}
              >
                <X />
              </button>
            </div>
            <label className="navigation-search">
              Buscar módulo
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cuentas, metas, reportes…"
              />
            </label>
            <div className="welcome-grid navigation-results">
              {nav
                .filter((item) => `${item.label} ${item.description}`.toLowerCase().includes(search.toLowerCase()))
                .map((item) => (
                  <button
                    key={item.key}
                    onClick={() => {
                      navigate(item.key);
                      setSearchOpen(false);
                      setSearch("");
                    }}
                  >
                    <span className="welcome-action violet">
                      <item.Icon />
                    </span>
                    <div>
                      <strong>{item.label}</strong>
                      <p>{item.description}</p>
                    </div>
                    <ChevronRight />
                  </button>
                ))}
            </div>
          </section>
        </div>
      )}
      {notificationsOpen && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar notificaciones"
            onClick={() => setNotificationsOpen(false)}
          />
          <section className="modern-modal">
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">CENTRO DE ALERTAS</span>
                <h3>Estado financiero</h3>
              </div>
              <button
                className="icon-button"
                onClick={() => setNotificationsOpen(false)}
              >
                <X />
              </button>
            </div>
            <div className="welcome-note">
              <CheckCircle2 />
              <p>
                <strong>Sistema conectado.</strong> Tus cifras están
                actualizadas y consolidadas en COP.
              </p>
            </div>
            <div className="welcome-grid">
              <button
                onClick={() => {
                  navigate("Presupuestos");
                  setNotificationsOpen(false);
                }}
              >
                <span className="welcome-action orange">
                  <ChartNoAxesCombined />
                </span>
                <div>
                  <strong>Revisar presupuestos</strong>
                  <p>Consulta límites y alertas del mes.</p>
                </div>
                <ChevronRight />
              </button>
              <button
                onClick={() => {
                  navigate("Recurrentes");
                  setNotificationsOpen(false);
                }}
              >
                <span className="welcome-action cyan">
                  <Repeat2 />
                </span>
                <div>
                  <strong>Pagos recurrentes</strong>
                  <p>Comprueba próximos vencimientos.</p>
                </div>
                <ChevronRight />
              </button>
            </div>
          </section>
        </div>
      )}
      {intelligenceOpen && (
        <div className="modal-layer">
          <button
            className="modal-backdrop"
            aria-label="Cerrar resumen"
            onClick={() => setIntelligenceOpen(false)}
          />
          <section className="modern-modal">
            <div className="flex items-start justify-between">
              <div>
                <span className="eyebrow">ANÁLISIS FINANCIERO LOCAL</span>
                <h3>Qué está pasando con tu dinero</h3>
              </div>
              <button
                className="icon-button"
                onClick={() => setIntelligenceOpen(false)}
              >
                <X />
              </button>
            </div>
            <div className="ai-privacy-note">
              <Info size={18} />
              <p>
                <strong>Análisis explicable y privado.</strong> FinanceOS calcula estos resultados con reglas financieras sobre tus datos actuales. No los envía a un proveedor externo de IA.
              </p>
            </div>
            <div className="ai-insight-list">
              {financialInsights.map((insight) => (
                <article className={`ai-insight ${insight.tone}`} key={insight.title}>
                  <span className="ai-insight-marker">{insight.tone === "good" ? <CheckCircle2 /> : <Gauge />}</span>
                  <div>
                    <small>{insight.metric}</small>
                    <strong>{insight.title}</strong>
                    <p>{insight.detail}</p>
                    <button onClick={() => { navigate(insight.page); setIntelligenceOpen(false); }}>
                      {insight.action} <ChevronRight size={16} />
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState<{
    loading: boolean;
    configuracion: boolean;
    registroPublico: boolean;
    aprovisionamientoLocalRequerido: boolean;
    autenticado: boolean;
    usuario?: Usuario;
  }>({
    loading: true,
    configuracion: false,
    registroPublico: false,
    aprovisionamientoLocalRequerido: false,
    autenticado: false,
  });
  const check = async () => {
    try {
      const state = await financeApi.authStatus();
      setAuth({
        loading: false,
        configuracion: state.requiere_configuracion,
        registroPublico: state.registro_publico,
        aprovisionamientoLocalRequerido: state.aprovisionamiento_local_requerido,
        autenticado: state.autenticado,
        usuario: state.usuario,
      });
    } catch {
      setAuth({
        loading: false,
        configuracion: false,
        registroPublico: false,
        aprovisionamientoLocalRequerido: false,
        autenticado: false,
      });
    }
  };
  useEffect(() => {
    void check();
  }, []);
  if (auth.loading)
    return (
      <main className="auth-page">
        <div className="auth-loader">
          <CircleDollarSign />
          <span>Protegiendo FinanceOS…</span>
        </div>
      </main>
    );
  if (!auth.autenticado)
    return (
      <AuthPage
        configuracionInicial={auth.configuracion}
        registroPublico={auth.registroPublico}
        aprovisionamientoLocalRequerido={auth.aprovisionamientoLocalRequerido}
        onAuthenticated={() => void check()}
      />
    );
  return (
    <FinanceApp
      user={auth.usuario!}
      onLogout={async () => {
        await financeApi.cerrarSesion();
        await check();
      }}
    />
  );
}

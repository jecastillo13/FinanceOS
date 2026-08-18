import { lazy, Suspense, useEffect, useState } from "react";
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
  ["Centro", LayoutDashboard],
  ["Cuentas", WalletCards],
  ["Tarjetas", CreditCard],
  ["Categorías", Tags],
  ["Movimientos", ReceiptText],
  ["Recurrentes", Repeat2],
  ["Transferencias", ArrowLeftRight],
  ["Presupuestos", ChartNoAxesCombined],
  ["Metas", Target],
  ["Inversiones", TrendingUp],
  ["Monedas", Globe2],
  ["Reportes", FileChartColumn],
  ["Configuración", Settings],
] as const;

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
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
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
      <aside className={`nav-rail ${menu ? "nav-open" : ""}`}>
        <div className="brand-orb">
          <CircleDollarSign size={25} />
          <span className="brand-tooltip">FinanceOS</span>
        </div>
        <nav>
          {nav.map(([label, Icon]) => (
            <button
              key={label}
              className={active === label ? "active" : ""}
              aria-label={label}
              title={label}
              onClick={() => {
                setActive(label);
                setMenu(false);
              }}
            >
              <Icon size={20} />
              <span>{label}</span>
              {active === label && <i />}
            </button>
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

      <main className="relative z-10 min-h-screen px-4 pb-20 lg:ml-24 lg:px-8 xl:px-12">
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
              <h1>{active}</h1>
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
                      <span className="eyebrow">PULSO DEL MES</span>
                      <h2>Tu actividad</h2>
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
                      <strong>Todo bajo control.</strong> No tienes alertas
                      críticas este mes.
                    </p>
                    <ChevronRight size={17} />
                  </div>
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
                      <span className="eyebrow">LIQUIDEZ</span>
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
                  <span className="ai-icon">
                    <Sparkles size={21} />
                  </span>
                  <div>
                    <span className="eyebrow text-violet-200">
                      FINANCEOS INTELLIGENCE
                    </span>
                    <h2>Tu resumen inteligente</h2>
                    <p>
                      Tu patrimonio está distribuido entre {accounts.length}{" "}
                      cuentas. Consulta ahora un análisis basado en tus datos
                      actuales.
                    </p>
                  </div>
                  <button onClick={() => setIntelligenceOpen(true)}>
                    Descubrir <ChevronRight size={15} />
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
          <section className="modern-modal">
            <div className="flex items-start justify-between">
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
            <label>
              Buscar módulo
              <input
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cuentas, metas, reportes…"
              />
            </label>
            <div className="welcome-grid">
              {nav
                .filter(([label]) =>
                  label.toLowerCase().includes(search.toLowerCase()),
                )
                .map(([label, Icon]) => (
                  <button
                    key={label}
                    onClick={() => {
                      navigate(label);
                      setSearchOpen(false);
                      setSearch("");
                    }}
                  >
                    <span className="welcome-action violet">
                      <Icon />
                    </span>
                    <div>
                      <strong>{label}</strong>
                      <p>Abrir módulo de FinanceOS</p>
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
                <span className="eyebrow">FINANCEOS INTELLIGENCE</span>
                <h3>Lectura de tu situación actual</h3>
              </div>
              <button
                className="icon-button"
                onClick={() => setIntelligenceOpen(false)}
              >
                <X />
              </button>
            </div>
            <div className="welcome-note">
              <Sparkles />
              <p>
                <strong>
                  {(summary?.balance ?? 0) >= 0
                    ? "Balance positivo."
                    : "Atención al balance."}
                </strong>{" "}
                Este mes ingresaste {cop.format(summary?.ingresos ?? 0)} y
                gastaste {cop.format(summary?.gastos ?? 0)}. Tu patrimonio
                consolidado es {cop.format(summary?.patrimonio ?? 0)}.
              </p>
            </div>
            <button
              className="modal-submit"
              onClick={() => {
                navigate("Reportes");
                setIntelligenceOpen(false);
              }}
            >
              <FileChartColumn /> Ver análisis completo
            </button>
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
    autenticado: boolean;
    usuario?: Usuario;
  }>({
    loading: true,
    configuracion: false,
    registroPublico: false,
    autenticado: false,
  });
  const check = async () => {
    try {
      const state = await financeApi.authStatus();
      setAuth({
        loading: false,
        configuracion: state.requiere_configuracion,
        registroPublico: state.registro_publico,
        autenticado: state.autenticado,
        usuario: state.usuario,
      });
    } catch {
      setAuth({
        loading: false,
        configuracion: false,
        registroPublico: false,
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

import { lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowDownRight, ArrowLeftRight, ArrowUpRight, Bell, ChartNoAxesCombined,
  ChevronRight, CircleDollarSign, Command, CreditCard, LayoutDashboard, Menu,
  Plus, ReceiptText, RefreshCw, Search, Settings, Sparkles, Target, TrendingUp,
  WalletCards, X,
} from "lucide-react";
import { Cuenta, financeApi, Graficas, Resumen } from "./api";
import AccountsPage from "./pages/AccountsPage";
import MovementsPage from "./pages/MovementsPage";
import BudgetsPage from "./pages/BudgetsPage";
import GoalsPage from "./pages/GoalsPage";
import InvestmentsPage from "./pages/InvestmentsPage";
import SettingsPage from "./pages/SettingsPage";

const DashboardCharts = lazy(() => import("./DashboardCharts"));
const cop = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const nav = [
  ["Centro", LayoutDashboard], ["Cuentas", WalletCards], ["Movimientos", ReceiptText],
  ["Presupuestos", ChartNoAxesCombined], ["Metas", Target], ["Inversiones", TrendingUp], ["Configuración", Settings],
] as const;

function Metric({ label, value, icon: Icon, accent }: { label: string; value: number; icon: typeof TrendingUp; accent: string }) {
  return <article className="metric-card group">
    <div className="flex items-center gap-3"><span className={`metric-icon ${accent}`}><Icon size={17}/></span><p>{label}</p></div>
    <strong>{cop.format(value)}</strong>
    <span className="metric-line" />
  </article>;
}

function Skeletons() {
  return <div className="grid gap-3 sm:grid-cols-3">{Array.from({length:3}).map((_,i)=><div key={i} className="h-28 animate-pulse rounded-[1.75rem] bg-white/[.045]"/>)}</div>;
}

export default function App() {
  const [menu, setMenu] = useState(false);
  const [active, setActive] = useState<string>("Centro");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<Resumen | null>(null);
  const [charts, setCharts] = useState<Graficas | null>(null);
  const [accounts, setAccounts] = useState<Cuenta[]>([]);

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [resumen, graficas, cuentas] = await Promise.all([financeApi.resumen(), financeApi.graficas(), financeApi.cuentas()]);
      setSummary(resumen); setCharts(graficas); setAccounts(cuentas);
    } catch (e) { setError(e instanceof Error ? e.message : "No fue posible conectar con FinanceOS."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  return <div className="app-shell">
    <div className="ambient ambient-one"/><div className="ambient ambient-two"/><div className="noise"/>
    {menu && <button aria-label="Cerrar menú" className="fixed inset-0 z-40 bg-[#02050d]/70 backdrop-blur-md lg:hidden" onClick={()=>setMenu(false)}/>}
    <aside className={`nav-rail ${menu ? "nav-open" : ""}`}>
      <div className="brand-orb"><CircleDollarSign size={25}/><span className="brand-tooltip">FinanceOS</span></div>
      <nav>{nav.map(([label,Icon])=><button key={label} className={active===label?"active":""} aria-label={label} title={label} onClick={()=>{setActive(label);setMenu(false)}}><Icon size={20}/><span>{label}</span>{active===label&&<i/>}</button>)}</nav>
      <div className="mt-auto flex flex-col items-center gap-3"><span className="online-dot" title="API conectada"/><button aria-label="Cerrar navegación" className="rail-close lg:hidden" onClick={()=>setMenu(false)}><X size={18}/></button><div className="avatar">JC</div></div>
    </aside>

    <main className="relative z-10 min-h-screen px-4 pb-20 lg:ml-24 lg:px-8 xl:px-12">
      <header className="topbar mx-auto max-w-[1480px]">
        <div className="flex items-center gap-3"><button aria-label="Abrir menú" className="icon-button lg:hidden" onClick={()=>setMenu(true)}><Menu size={20}/></button><div><span className="eyebrow">FINANCEOS · EN LÍNEA</span><h1>{active}</h1></div></div>
        <button className="command-bar"><Search size={17}/><span>Buscar en FinanceOS</span><kbd><Command size={12}/> K</kbd></button>
        <div className="flex gap-2"><button aria-label="Notificaciones" className="icon-button"><Bell size={18}/><i className="notification"/></button><button aria-label="Actualizar" onClick={()=>void load()} className="icon-button hover:rotate-45"><RefreshCw size={18}/></button></div>
      </header>

      <div className="mx-auto max-w-[1480px]">
        {error&&<div className="error-banner">{error}. Verifica que FastAPI esté activo en el puerto 8000.</div>}

        {active==="Centro" ? <>

        <section className="hero-grid">
          <article className="wealth-card">
            <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
            <div className="relative z-10 flex h-full flex-col justify-between">
              <div className="flex items-start justify-between"><div><span className="eyebrow text-cyan-200">PATRIMONIO TOTAL</span><div className="mt-3 flex items-center gap-2"><span className="live-pill"><i/> EN VIVO</span><span className="text-xs text-white/40">Consolidado en COP</span></div></div><span className="sparkle"><Sparkles size={20}/></span></div>
              <div><p className="wealth-value">{loading?"—":cop.format(summary?.patrimonio??0)}</p><div className="mt-6 flex flex-wrap gap-3"><button className="primary-action" onClick={()=>setActive("Movimientos")}><Plus size={17}/> Nuevo movimiento</button><button className="ghost-action"><ArrowLeftRight size={17}/> Transferir</button></div></div>
            </div>
          </article>

          <div className="pulse-panel">
            <div className="panel-heading"><div><span className="eyebrow">PULSO DEL MES</span><h2>Tu actividad</h2></div><span className="pulse-ring"><i/></span></div>
            {loading?<Skeletons/>:<div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <Metric label="Balance" value={summary?.balance??0} icon={TrendingUp} accent="violet"/>
              <Metric label="Ingresos" value={summary?.ingresos??0} icon={ArrowUpRight} accent="mint"/>
              <Metric label="Gastos" value={summary?.gastos??0} icon={ArrowDownRight} accent="coral"/>
            </div>}
            <div className="insight-strip"><span><Sparkles size={15}/></span><p><strong>Todo bajo control.</strong> No tienes alertas críticas este mes.</p><ChevronRight size={17}/></div>
          </div>
        </section>

        <Suspense fallback={<div className="mt-5 grid gap-5 xl:grid-cols-[1.65fr_1fr]"><div className="chart-skeleton"/><div className="chart-skeleton"/></div>}><DashboardCharts charts={charts} patrimonio={summary?.patrimonio??0}/></Suspense>

        <section className="lower-grid">
          <article className="accounts-panel">
            <div className="panel-heading"><div><span className="eyebrow">LIQUIDEZ</span><h2>Tus cuentas</h2></div><button className="text-action" onClick={()=>setActive("Cuentas")}>Explorar <ChevronRight size={15}/></button></div>
            <div className="accounts-track">{accounts.slice(0,4).map((account,index)=><div className="account-tile" key={account.id}><div className="flex items-center justify-between"><span className={`account-logo logo-${index%4}`}><CreditCard size={18}/></span><span className="currency-chip">{account.moneda}</span></div><div><p>{account.nombre}</p><strong>{new Intl.NumberFormat("es-CO",{style:"currency",currency:account.moneda}).format(account.saldo)}</strong></div><span className="account-glow"/></div>)}</div>
          </article>
          <article className="ai-panel"><span className="ai-icon"><Sparkles size={21}/></span><div><span className="eyebrow text-violet-200">FINANCEOS INTELLIGENCE</span><h2>Tu resumen inteligente</h2><p>Tu patrimonio está distribuido entre {accounts.length} cuentas. Próximamente recibirás análisis y proyecciones personalizadas.</p></div><button>Descubrir <ChevronRight size={15}/></button></article>
        </section>
        </> : active==="Cuentas" ? <AccountsPage accounts={accounts} onChanged={load}/> : active==="Movimientos" ? <MovementsPage accounts={accounts}/> : active==="Presupuestos" ? <BudgetsPage/> : active==="Metas" ? <GoalsPage/> : active==="Inversiones" ? <InvestmentsPage/> : <SettingsPage/>}
      </div>
    </main>
  </div>;
}

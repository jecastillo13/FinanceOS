import { useMemo } from "react";
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Graficas } from "./api";

const colors = ["#7c7cff", "#32d5c4", "#20a9ff", "#f9a85d", "#ce70ff"];
const cop = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function DashboardCharts({ charts, patrimonio }: { charts: Graficas | null; patrimonio: number }) {
  const distribution = useMemo(() => charts?.distribucion.map((item) => ({ ...item, cuenta: item.cuenta.replace(/^\S+\s/, "") })) ?? [], [charts]);
  return <section className="mt-[18px] grid gap-[18px] xl:grid-cols-[1.62fr_1fr]">
    <article className="chart-panel"><div className="chart-title"><div><span>RENDIMIENTO</span><h3>Movimiento de capital</h3><p>Ingresos y gastos · últimos seis meses</p></div><div className="chart-legend"><i/> Ingresos <i/> Gastos</div></div>
      <ResponsiveContainer width="100%" height={310}><AreaChart data={charts?.flujo ?? []} margin={{ left: 4, right: 8, top:16 }}><defs><linearGradient id="income" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#42e1c0" stopOpacity={.36}/><stop offset="1" stopColor="#42e1c0" stopOpacity={0}/></linearGradient><linearGradient id="expense" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8273ff" stopOpacity={.34}/><stop offset="1" stopColor="#8273ff" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="rgba(255,255,255,.045)" vertical={false}/><XAxis dataKey="mes" stroke="#566178" tickLine={false} axisLine={false}/><YAxis stroke="#566178" tickLine={false} axisLine={false} tickFormatter={(v) => `$${Math.round(v/1000)}k`}/><Tooltip contentStyle={{ background: "#10182b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 16 }}/><Area type="monotone" dataKey="ingresos" stroke="#42e1c0" strokeWidth={3} fill="url(#income)"/><Area type="monotone" dataKey="gastos" stroke="#8273ff" strokeWidth={3} fill="url(#expense)"/></AreaChart></ResponsiveContainer>
    </article>
    <article className="chart-panel distribution-panel"><div className="chart-title"><div><span>PORTAFOLIO</span><h3>Distribución</h3><p>Composición del patrimonio</p></div></div>
      <div className="relative mt-3 h-56"><ResponsiveContainer><PieChart><Pie data={distribution} dataKey="saldo_cop" nameKey="cuenta" innerRadius={62} outerRadius={91} paddingAngle={4}>{distribution.map((_, i) => <Cell key={i} fill={colors[i % colors.length]}/>)}</Pie><Tooltip contentStyle={{ background: "#111c32", border: "1px solid #334160", borderRadius: 16 }} formatter={(v) => cop.format(Number(v))}/></PieChart></ResponsiveContainer><div className="pointer-events-none absolute inset-0 grid place-content-center text-center"><span className="text-xs text-slate-500">Total</span><strong className="text-lg">{cop.format(patrimonio)}</strong></div></div>
      <div className="space-y-2">{distribution.slice(0,4).map((item,i) => <div key={`${item.cuenta}-${i}`} className="flex items-center justify-between text-sm"><span className="flex min-w-0 items-center gap-2 text-slate-300"><i className="h-2.5 w-2.5 shrink-0 rounded-full" style={{background:colors[i%colors.length]}}/><span className="truncate">{item.cuenta}</span></span><strong>{cop.format(item.saldo_cop)}</strong></div>)}</div>
    </article>
  </section>;
}

import plotly.graph_objects as go


PALETTE = ["#7C83FF", "#35D6B4", "#35B8F4", "#F6C85F", "#FA7185", "#A78BFA"]


def _base_layout(figura, *, hovermode="closest"):
    figura.update_layout(
        template=None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,16,32,.18)",
        font=dict(family="Inter, sans-serif", color="#B8C5DF", size=12),
        hovermode=hovermode,
        hoverlabel=dict(bgcolor="#17233F", bordercolor="#53689A", font=dict(color="#FFFFFF", size=13)),
        margin=dict(l=58, r=14, t=18, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
        transition=dict(duration=350, easing="cubic-in-out"),
    )
    figura.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(118,137,184,.18)")
    figura.update_yaxes(
        gridcolor="rgba(118,137,184,.12)", zeroline=False, tickprefix="$",
        tickformat="~s", separatethousands=True, automargin=True,
    )
    return figura


def flujo_caja_chart(flujo):
    meses = [fila["mes"] for fila in flujo]
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=meses, y=[fila["ingresos"] for fila in flujo], name="Ingresos", mode="lines+markers",
        line=dict(color="#35D6B4", width=3, shape="spline", smoothing=1.1),
        marker=dict(size=7, color="#35D6B4", line=dict(color="#D8FFF6", width=1.5)),
        fill="tozeroy", fillcolor="rgba(53,214,180,.12)", hovertemplate="%{x}<br>Ingresos: $%{y:,.0f}<extra></extra>",
    ))
    figura.add_trace(go.Scatter(
        x=meses, y=[fila["gastos"] for fila in flujo], name="Gastos", mode="lines+markers",
        line=dict(color="#FA7185", width=3, shape="spline", smoothing=1.1),
        marker=dict(size=7, color="#FA7185", line=dict(color="#FFE1E6", width=1.5)),
        fill="tozeroy", fillcolor="rgba(250,113,133,.10)", hovertemplate="%{x}<br>Gastos: $%{y:,.0f}<extra></extra>",
    ))
    _base_layout(figura, hovermode="x unified")
    figura.update_layout(height=350)
    return figura


def dona_chart(datos, nombres, valores, *, centro="TOTAL", colores=None):
    total = sum(float(item[valores] or 0) for item in datos)
    figura = go.Figure(go.Pie(
        labels=[item[nombres] for item in datos], values=[item[valores] for item in datos], hole=.68,
        sort=False, direction="clockwise", marker=dict(colors=colores or PALETTE, line=dict(color="#11182C", width=3)),
        textinfo="percent", textfont=dict(color="#F5F7FF", size=11),
        hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    _base_layout(figura)
    figura.update_layout(
        height=350, showlegend=True,
        annotations=[dict(text=f"<span style='font-size:11px;color:#93A4C4'>{centro}</span><br><b>${total:,.0f}</b>", x=.5, y=.5, showarrow=False, font=dict(size=18, color="#FFFFFF"))],
    )
    return figura

"""
Dashboard Profesional de FacturIA 2.1.0 con Streamlit
Sistema avanzado de análisis financiero multi-persona con KPIs profesionales
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Optional

# Agregar el directorio raíz al path para imports
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database import (
    get_database,
    obtener_transacciones,
    calcular_estadisticas_periodo,
    obtener_top_categorias,
    obtener_totales_mes_actual
)
from src.database.models import TipoTransaccion
from src.config import CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS

# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="FacturIA 2.1.0 - Dashboard Profesional",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profesional Mejorado
st.markdown("""
    <style>
    /* Variables de colores profesionales */
    :root {
        --primary-green: #00CC66;
        --primary-red: #FF4444;
        --dark-bg: #0E1117;
        --card-bg: #1E2127;
    }

    /* Métricas grandes y destacadas */
    .big-metric {
        font-size: 3rem !important;
        font-weight: 800;
        line-height: 1.2;
    }

    .positive {
        color: #00CC66;
        text-shadow: 0 0 10px rgba(0, 204, 102, 0.3);
    }

    .negative {
        color: #FF4444;
        text-shadow: 0 0 10px rgba(255, 68, 68, 0.3);
    }

    /* Tarjetas profesionales */
    .metric-card {
        background: linear-gradient(135deg, #1E2127 0%, #2D3139 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #00CC66;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin: 0.5rem 0;
    }

    .metric-title {
        font-size: 0.9rem;
        color: #8B92A8;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        margin: 0.5rem 0;
    }

    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* Tabs profesionales */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1E2127;
        padding: 0.5rem;
        border-radius: 10px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #8B92A8;
        font-weight: 600;
        font-size: 0.95rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: #00CC66;
        color: white;
    }

    /* Headers profesionales */
    h1 {
        font-weight: 800;
        letter-spacing: -1px;
    }

    h2 {
        font-weight: 700;
        color: #00CC66;
        border-bottom: 2px solid #00CC66;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }

    h3 {
        font-weight: 600;
        color: #8B92A8;
    }

    /* Tabla profesional */
    .dataframe {
        font-size: 0.9rem;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #00CC66;
    }
    </style>
""", unsafe_allow_html=True)


# ==================== FUNCIONES AUXILIARES ====================

@st.cache_resource
def inicializar_db():
    """Inicializa la conexión a la base de datos"""
    try:
        db = get_database()
        return db
    except Exception as e:
        st.error(f"❌ Error al conectar con la base de datos: {e}")
        return None


def formatear_monto(monto: float) -> str:
    """Formatea un monto con símbolo de pesos y separadores"""
    return f"${monto:,.2f}".replace(",", ".")


def formatear_porcentaje(valor: float) -> str:
    """Formatea un porcentaje"""
    return f"{valor:.1f}%"


def calcular_variacion_porcentual(actual: float, anterior: float) -> float:
    """Calcula la variación porcentual entre dos valores"""
    if anterior == 0:
        return 0 if actual == 0 else 100
    return ((actual - anterior) / anterior) * 100


# ==================== FUNCIONES DE DATOS ====================

def obtener_personas_unicas(session) -> List[str]:
    """Obtiene lista de personas únicas en las transacciones"""
    from sqlalchemy import distinct
    from src.database.models import Transaccion

    personas = session.query(distinct(Transaccion.persona)).all()
    return [p[0] for p in personas if p[0]]


def calcular_estadisticas_por_persona(
    session,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    persona: Optional[str] = None
) -> Dict:
    """Calcula estadísticas para una persona específica o todas"""
    from src.database.models import Transaccion
    from sqlalchemy import and_

    query = session.query(Transaccion).filter(
        and_(
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        )
    )

    if persona and persona != "Todas":
        query = query.filter(Transaccion.persona == persona)

    transacciones = query.all()

    # Calcular totales
    ingresos = [t for t in transacciones if t.tipo == TipoTransaccion.INGRESO]
    egresos = [t for t in transacciones if t.tipo == TipoTransaccion.EGRESO]

    total_ingresos = sum(t.monto for t in ingresos)
    total_egresos = sum(t.monto for t in egresos)
    balance = total_ingresos - total_egresos

    # Agrupar por categoría
    categorias_ingresos = {}
    for t in ingresos:
        cat = t.categoria
        categorias_ingresos[cat] = categorias_ingresos.get(cat, 0) + t.monto

    categorias_egresos = {}
    for t in egresos:
        cat = t.categoria
        categorias_egresos[cat] = categorias_egresos.get(cat, 0) + t.monto

    # Análisis temporal
    transacciones_por_dia = {}
    for t in transacciones:
        fecha = t.fecha_transaccion.date() if t.fecha_transaccion else None
        if fecha:
            if fecha not in transacciones_por_dia:
                transacciones_por_dia[fecha] = {"ingresos": 0, "egresos": 0}

            if t.tipo == TipoTransaccion.INGRESO:
                transacciones_por_dia[fecha]["ingresos"] += t.monto
            else:
                transacciones_por_dia[fecha]["egresos"] += t.monto

    # Calcular días con datos
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    dias_con_datos = len(transacciones_por_dia)

    # Promedios diarios
    promedio_ingreso_dia = total_ingresos / dias_periodo if dias_periodo > 0 else 0
    promedio_egreso_dia = total_egresos / dias_periodo if dias_periodo > 0 else 0

    return {
        "persona": persona or "Todas",
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "total_transacciones": len(transacciones),
        "total_ingresos": round(total_ingresos, 2),
        "total_egresos": round(total_egresos, 2),
        "balance": round(balance, 2),
        "cantidad_ingresos": len(ingresos),
        "cantidad_egresos": len(egresos),
        "categorias_ingresos": {k: round(v, 2) for k, v in categorias_ingresos.items()},
        "categorias_egresos": {k: round(v, 2) for k, v in categorias_egresos.items()},
        "transacciones_por_dia": transacciones_por_dia,
        "dias_periodo": dias_periodo,
        "dias_con_datos": dias_con_datos,
        "promedio_ingreso_dia": round(promedio_ingreso_dia, 2),
        "promedio_egreso_dia": round(promedio_egreso_dia, 2)
    }


def calcular_ratios_financieros(stats: Dict, stats_anterior: Optional[Dict] = None) -> Dict:
    """Calcula ratios financieros profesionales"""
    ingresos = stats['total_ingresos']
    egresos = stats['total_egresos']
    balance = stats['balance']
    dias = stats['dias_periodo']

    # Ratios básicos
    tasa_ahorro = (balance / ingresos * 100) if ingresos > 0 else 0
    ratio_ingreso_egreso = (ingresos / egresos) if egresos > 0 else float('inf')
    burn_rate = egresos / dias if dias > 0 else 0  # Gasto diario promedio

    # Proyecciones
    dias_hasta_cero = (balance / burn_rate) if burn_rate > 0 and balance > 0 else float('inf')

    # Eficiencia de gasto
    eficiencia_gasto = (1 - (egresos / ingresos)) * 100 if ingresos > 0 else 0

    ratios = {
        "tasa_ahorro": round(tasa_ahorro, 2),
        "ratio_ingreso_egreso": round(ratio_ingreso_egreso, 2) if ratio_ingreso_egreso != float('inf') else 0,
        "burn_rate": round(burn_rate, 2),
        "promedio_gasto_diario": round(burn_rate, 2),
        "dias_hasta_cero": int(dias_hasta_cero) if dias_hasta_cero != float('inf') else None,
        "eficiencia_gasto": round(eficiencia_gasto, 2)
    }

    # Calcular variaciones si hay período anterior
    if stats_anterior:
        ingresos_ant = stats_anterior['total_ingresos']
        egresos_ant = stats_anterior['total_egresos']
        balance_ant = stats_anterior['balance']

        ratios["var_ingresos"] = calcular_variacion_porcentual(ingresos, ingresos_ant)
        ratios["var_egresos"] = calcular_variacion_porcentual(egresos, egresos_ant)
        ratios["var_balance"] = calcular_variacion_porcentual(balance, balance_ant)
    else:
        ratios["var_ingresos"] = 0
        ratios["var_egresos"] = 0
        ratios["var_balance"] = 0

    return ratios


# ==================== COMPONENTES VISUALES ====================

def mostrar_kpis_profesionales(stats: Dict, ratios: Dict):
    """Muestra KPIs principales con diseño profesional"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta_ingresos = f"{ratios['var_ingresos']:+.1f}%" if ratios['var_ingresos'] != 0 else None
        st.metric(
            label="💵 TOTAL INGRESOS",
            value=formatear_monto(stats['total_ingresos']),
            delta=delta_ingresos,
            delta_color="normal"
        )
        st.caption(f"📊 {stats['cantidad_ingresos']} transacciones | Promedio: {formatear_monto(stats['promedio_ingreso_dia'])}/día")

    with col2:
        delta_egresos = f"{ratios['var_egresos']:+.1f}%" if ratios['var_egresos'] != 0 else None
        st.metric(
            label="💸 TOTAL EGRESOS",
            value=formatear_monto(stats['total_egresos']),
            delta=delta_egresos,
            delta_color="inverse"
        )
        st.caption(f"📊 {stats['cantidad_egresos']} transacciones | Promedio: {formatear_monto(stats['promedio_egreso_dia'])}/día")

    with col3:
        delta_balance = f"{ratios['var_balance']:+.1f}%" if ratios['var_balance'] != 0 else None
        st.metric(
            label="📊 BALANCE NETO",
            value=formatear_monto(stats['balance']),
            delta=delta_balance,
            delta_color="normal" if stats['balance'] > 0 else "inverse"
        )
        st.caption(f"{'✅ Superávit' if stats['balance'] > 0 else '⚠️ Déficit'} | Tasa ahorro: {formatear_porcentaje(ratios['tasa_ahorro'])}")

    with col4:
        st.metric(
            label="📄 TRANSACCIONES",
            value=f"{stats['total_transacciones']}",
            delta=f"{stats['dias_con_datos']}/{stats['dias_periodo']} días activos"
        )
        st.caption(f"Ratio I/E: {ratios['ratio_ingreso_egreso']:.2f}x | Burn rate: {formatear_monto(ratios['burn_rate'])}/día")


def mostrar_ratios_financieros(ratios: Dict):
    """Muestra ratios financieros profesionales"""

    st.subheader("📈 Ratios Financieros Profesionales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**💰 Tasa de Ahorro**")
        color = "green" if ratios['tasa_ahorro'] > 0 else "red"
        st.markdown(f"<h2 style='color:{color};'>{formatear_porcentaje(ratios['tasa_ahorro'])}</h2>", unsafe_allow_html=True)

        # Indicador visual
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ratios['tasa_ahorro'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': "darkgreen" if ratios['tasa_ahorro'] > 0 else "darkred"},
                'steps': [
                    {'range': [-100, 0], 'color': "lightgray"},
                    {'range': [0, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 20
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**🔥 Burn Rate (Gasto Diario)**")
        st.markdown(f"<h2 style='color:orange;'>{formatear_monto(ratios['burn_rate'])}</h2>", unsafe_allow_html=True)

        if ratios['dias_hasta_cero']:
            st.info(f"⏱️ Proyección: {ratios['dias_hasta_cero']} días hasta balance cero")
        else:
            st.success("✅ Balance sostenible")

    with col3:
        st.markdown("**⚖️ Ratio Ingreso/Egreso**")
        ratio_val = ratios['ratio_ingreso_egreso']
        color = "green" if ratio_val > 1 else "red"
        st.markdown(f"<h2 style='color:{color};'>{ratio_val:.2f}x</h2>", unsafe_allow_html=True)

        if ratio_val > 1:
            st.success(f"✅ Ingresos {formatear_porcentaje((ratio_val - 1) * 100)} superiores")
        elif ratio_val < 1:
            st.error(f"⚠️ Egresos {formatear_porcentaje((1 - ratio_val) * 100)} superiores")
        else:
            st.warning("⚖️ Balance equilibrado")

    with col4:
        st.markdown("**⚡ Eficiencia de Gasto**")
        efic = ratios['eficiencia_gasto']
        color = "green" if efic > 0 else "red"
        st.markdown(f"<h2 style='color:{color};'>{formatear_porcentaje(efic)}</h2>", unsafe_allow_html=True)

        if efic > 20:
            st.success("🌟 Excelente gestión")
        elif efic > 0:
            st.info("👍 Gestión positiva")
        else:
            st.error("⚠️ Revisar gastos")


def grafico_evolucion_temporal(stats: Dict):
    """Gráfico de evolución temporal de ingresos y egresos"""

    transacciones_dia = stats['transacciones_por_dia']

    if not transacciones_dia:
        st.info("No hay datos temporales para mostrar")
        return

    # Preparar datos
    fechas = sorted(transacciones_dia.keys())
    ingresos_dia = [transacciones_dia[f]["ingresos"] for f in fechas]
    egresos_dia = [transacciones_dia[f]["egresos"] for f in fechas]
    balance_dia = [transacciones_dia[f]["ingresos"] - transacciones_dia[f]["egresos"] for f in fechas]

    # Crear gráfico con subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.6, 0.4],
        subplot_titles=("Flujo Diario de Caja", "Balance Acumulado"),
        vertical_spacing=0.12
    )

    # Subplot 1: Ingresos y Egresos
    fig.add_trace(
        go.Bar(name='Ingresos', x=fechas, y=ingresos_dia, marker_color='#00CC66'),
        row=1, col=1
    )

    fig.add_trace(
        go.Bar(name='Egresos', x=fechas, y=egresos_dia, marker_color='#FF4444'),
        row=1, col=1
    )

    # Subplot 2: Balance acumulado
    balance_acumulado = []
    acum = 0
    for bal in balance_dia:
        acum += bal
        balance_acumulado.append(acum)

    fig.add_trace(
        go.Scatter(
            name='Balance Acumulado',
            x=fechas,
            y=balance_acumulado,
            mode='lines+markers',
            line=dict(color='#00AAFF', width=3),
            fill='tozeroy',
            fillcolor='rgba(0, 170, 255, 0.1)'
        ),
        row=2, col=1
    )

    # Añadir línea de cero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

    # Layout
    fig.update_layout(
        height=600,
        showlegend=True,
        hovermode='x unified',
        barmode='group',
        title_text="Análisis Temporal Detallado"
    )

    fig.update_xaxes(title_text="Fecha", row=2, col=1)
    fig.update_yaxes(title_text="Monto ($)", row=1, col=1)
    fig.update_yaxes(title_text="Balance Acumulado ($)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


def grafico_comparacion_personas(session, fecha_inicio, fecha_fin, personas: List[str]):
    """Gráfico comparativo entre personas"""

    if len(personas) < 2:
        st.info("Se necesitan al menos 2 personas para comparar")
        return

    # Calcular stats por persona
    datos_personas = []

    for persona in personas:
        stats = calcular_estadisticas_por_persona(session, fecha_inicio, fecha_fin, persona)
        datos_personas.append({
            "Persona": persona,
            "Ingresos": stats['total_ingresos'],
            "Egresos": stats['total_egresos'],
            "Balance": stats['balance'],
            "Transacciones": stats['total_transacciones']
        })

    df = pd.DataFrame(datos_personas)

    # Crear subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Ingresos por Persona", "Egresos por Persona", "Balance por Persona"),
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )

    # Ingresos
    fig.add_trace(
        go.Bar(name='Ingresos', x=df['Persona'], y=df['Ingresos'], marker_color='#00CC66'),
        row=1, col=1
    )

    # Egresos
    fig.add_trace(
        go.Bar(name='Egresos', x=df['Persona'], y=df['Egresos'], marker_color='#FF4444'),
        row=1, col=2
    )

    # Balance
    colors = ['#00CC66' if b > 0 else '#FF4444' for b in df['Balance']]
    fig.add_trace(
        go.Bar(name='Balance', x=df['Persona'], y=df['Balance'], marker_color=colors),
        row=1, col=3
    )

    fig.update_layout(height=400, showlegend=False, title_text="Comparación Multi-Persona")

    st.plotly_chart(fig, use_container_width=True)

    # Tabla comparativa
    st.subheader("📊 Tabla Comparativa Detallada")

    # Formatear tabla
    df_formatted = df.copy()
    df_formatted['Ingresos'] = df_formatted['Ingresos'].apply(formatear_monto)
    df_formatted['Egresos'] = df_formatted['Egresos'].apply(formatear_monto)
    df_formatted['Balance'] = df_formatted['Balance'].apply(formatear_monto)

    st.dataframe(df_formatted, use_container_width=True, hide_index=True)


def grafico_categorias_detallado(stats: Dict, tipo: str):
    """Gráfico detallado de categorías con ranking"""

    categorias = stats[f'categorias_{tipo}s']

    if not categorias:
        st.info(f"No hay {tipo}s en este período")
        return

    # Ordenar por monto
    categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1], reverse=True)

    cats = [c[0] for c in categorias_ordenadas]
    montos = [c[1] for c in categorias_ordenadas]

    # Calcular porcentajes
    total = sum(montos)
    porcentajes = [m/total*100 for m in montos]

    # Crear dos columnas
    col1, col2 = st.columns([1, 1])

    with col1:
        # Gráfico de torta
        fig_pie = px.pie(
            values=montos,
            names=cats,
            title=f"Distribución de {tipo.capitalize()}s",
            color_discrete_sequence=px.colors.sequential.Greens if tipo == "ingreso" else px.colors.sequential.Reds
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Gráfico de barras horizontales
        fig_bar = go.Figure(go.Bar(
            x=montos,
            y=cats,
            orientation='h',
            marker_color='#00CC66' if tipo == "ingreso" else '#FF4444',
            text=[f'{formatear_monto(m)} ({p:.1f}%)' for m, p in zip(montos, porcentajes)],
            textposition='auto'
        ))

        fig_bar.update_layout(
            title=f"Ranking de {tipo.capitalize()}s por Monto",
            xaxis_title="Monto ($)",
            yaxis_title="Categoría",
            height=400
        )

        st.plotly_chart(fig_bar, use_container_width=True)


def tabla_transacciones_completa(session, filtros: Dict):
    """Tabla completa de transacciones con filtros"""

    transacciones = obtener_transacciones(
        session,
        tipo=filtros.get('tipo'),
        categoria=filtros.get('categoria'),
        fecha_desde=filtros.get('fecha_desde'),
        fecha_hasta=filtros.get('fecha_hasta'),
        limite=200
    )

    if not transacciones:
        st.info("No hay transacciones para mostrar")
        return

    # Convertir a DataFrame
    data = []
    for t in transacciones:
        data.append({
            "ID": t.id,
            "Fecha": t.fecha_transaccion.strftime('%Y-%m-%d %H:%M') if t.fecha_transaccion else "N/A",
            "Persona": t.persona or "General",
            "Tipo": t.tipo.value.upper() if t.tipo else "N/A",
            "Categoría": t.categoria,
            "Monto": t.monto,
            "Emisor/Receptor": t.emisor_receptor[:30] if t.emisor_receptor else "N/A",
            "Descripción": t.descripcion[:50] if t.descripcion else "",
            "Origen": t.origen.value.upper() if t.origen else "N/A"
        })

    df = pd.DataFrame(data)

    # Formatear monto para display
    df_display = df.copy()
    df_display['Monto'] = df_display['Monto'].apply(formatear_monto)

    # Mostrar estadísticas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros", len(df))
    with col2:
        personas_unicas = df['Persona'].nunique()
        st.metric("Personas", personas_unicas)
    with col3:
        categorias_unicas = df['Categoría'].nunique()
        st.metric("Categorías", categorias_unicas)

    # Tabla interactiva
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Monto": st.column_config.TextColumn("Monto", help="Monto de la transacción"),
            "Tipo": st.column_config.TextColumn("Tipo", help="Ingreso o Egreso")
        }
    )

    # Opción de descarga
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f'transacciones_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )


# ==================== SIDEBAR Y FILTROS ====================

def filtros_sidebar(session):
    """Sidebar con filtros profesionales"""

    st.sidebar.title("⚙️ Panel de Control")
    st.sidebar.markdown("---")

    # === FILTRO DE PERSONA ===
    st.sidebar.subheader("👤 Persona")
    personas = obtener_personas_unicas(session)
    personas_opciones = ["Todas"] + personas

    persona_seleccionada = st.sidebar.selectbox(
        "Seleccionar persona",
        personas_opciones,
        index=0
    )

    # === FILTRO DE PERÍODO ===
    st.sidebar.subheader("📅 Período")

    opciones_periodo = {
        "Hoy": 0,
        "Últimos 7 días": 7,
        "Últimos 15 días": 15,
        "Últimos 30 días": 30,
        "Mes actual": -1,
        "Último trimestre": 90,
        "Último semestre": 180,
        "Año actual": -3,
        "Personalizado": -2
    }

    periodo = st.sidebar.selectbox(
        "Seleccionar período",
        list(opciones_periodo.keys()),
        index=3  # Default: Últimos 30 días
    )

    # Calcular fechas
    hoy = datetime.now()

    if periodo == "Personalizado":
        fecha_desde = st.sidebar.date_input(
            "Desde",
            value=hoy - timedelta(days=30)
        )
        fecha_hasta = st.sidebar.date_input(
            "Hasta",
            value=hoy
        )
        fecha_desde = datetime.combine(fecha_desde, datetime.min.time())
        fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())

    elif opciones_periodo[periodo] == -1:  # Mes actual
        fecha_desde = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = (fecha_desde + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    elif opciones_periodo[periodo] == -3:  # Año actual
        fecha_desde = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_hasta = hoy

    else:
        dias = opciones_periodo[periodo]
        fecha_desde = hoy - timedelta(days=dias)
        fecha_hasta = hoy

    # Mostrar período seleccionado
    st.sidebar.info(f"📆 {fecha_desde.strftime('%d/%m/%Y')} → {fecha_hasta.strftime('%d/%m/%Y')}")

    # === FILTRO DE TIPO ===
    st.sidebar.subheader("💰 Tipo de Transacción")
    tipo_filtro = st.sidebar.radio(
        "Filtrar por tipo",
        ["Todas", "Ingresos", "Egresos"],
        index=0
    )

    tipo_map = {
        "Todas": None,
        "Ingresos": "ingreso",
        "Egresos": "egreso"
    }

    # === FILTRO DE CATEGORÍA ===
    st.sidebar.subheader("🏷️ Categoría")

    if tipo_filtro == "Ingresos":
        categorias_disponibles = CATEGORIAS_INGRESOS
    elif tipo_filtro == "Egresos":
        categorias_disponibles = CATEGORIAS_EGRESOS
    else:
        categorias_disponibles = CATEGORIAS_INGRESOS + CATEGORIAS_EGRESOS

    categoria_filtro = st.sidebar.selectbox(
        "Seleccionar categoría",
        ["Todas"] + categorias_disponibles,
        index=0
    )

    categoria = None if categoria_filtro == "Todas" else categoria_filtro

    st.sidebar.markdown("---")

    # === OPCIONES ADICIONALES ===
    st.sidebar.subheader("🔧 Opciones")

    comparar_personas = st.sidebar.checkbox("Comparar todas las personas", value=False)
    mostrar_ratios = st.sidebar.checkbox("Mostrar ratios financieros", value=True)

    st.sidebar.markdown("---")

    # Botón de refrescar
    if st.sidebar.button("🔄 Refrescar Dashboard", use_container_width=True):
        st.rerun()

    return {
        "persona": persona_seleccionada if not comparar_personas else None,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "tipo": tipo_map[tipo_filtro],
        "categoria": categoria,
        "comparar_personas": comparar_personas,
        "mostrar_ratios": mostrar_ratios,
        "personas_list": personas
    }


# ==================== MAIN ====================

def main():
    """Función principal del dashboard profesional"""

    # Header
    st.title("💰 FacturIA 2.1.0 - Dashboard Profesional")
    st.markdown("**Sistema Avanzado de Análisis Financiero Multi-Persona con KPIs Profesionales**")
    st.markdown("---")

    # Inicializar DB
    db = inicializar_db()

    if db is None:
        st.error("❌ No se pudo conectar a la base de datos. Verifica la configuración.")
        st.stop()

    if not db.verificar_conexion():
        st.error("❌ Error de conexión a la base de datos")
        st.stop()

    # Obtener filtros
    with db.get_session() as session:
        filtros = filtros_sidebar(session)

        # ==================== ANÁLISIS PRINCIPAL ====================

        # Calcular estadísticas del período actual
        stats_actual = calcular_estadisticas_por_persona(
            session,
            filtros['fecha_desde'],
            filtros['fecha_hasta'],
            filtros['persona']
        )

        # Calcular estadísticas del período anterior (para comparación)
        dias_periodo = (filtros['fecha_hasta'] - filtros['fecha_desde']).days
        fecha_desde_anterior = filtros['fecha_desde'] - timedelta(days=dias_periodo)
        fecha_hasta_anterior = filtros['fecha_desde'] - timedelta(seconds=1)

        stats_anterior = calcular_estadisticas_por_persona(
            session,
            fecha_desde_anterior,
            fecha_hasta_anterior,
            filtros['persona']
        )

        # Calcular ratios financieros
        ratios = calcular_ratios_financieros(stats_actual, stats_anterior)

        # ==================== HEADER CON INFO DEL FILTRO ====================

        if filtros['persona'] and filtros['persona'] != "Todas":
            st.info(f"👤 Mostrando datos para: **{filtros['persona']}**")
        elif filtros['comparar_personas']:
            st.info(f"👥 Modo comparación: Analizando {len(filtros['personas_list'])} personas")
        else:
            st.info("📊 Mostrando datos consolidados de todas las personas")

        # ==================== KPIS PRINCIPALES ====================

        st.header("📊 KPIs Principales")
        mostrar_kpis_profesionales(stats_actual, ratios)

        st.markdown("---")

        # ==================== RATIOS FINANCIEROS ====================

        if filtros['mostrar_ratios']:
            mostrar_ratios_financieros(ratios)
            st.markdown("---")

        # ==================== TABS DE ANÁLISIS ====================

        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Evolución Temporal",
            "🏷️ Análisis por Categorías",
            "👥 Comparación por Persona",
            "📋 Transacciones Detalladas"
        ])

        # === TAB 1: EVOLUCIÓN TEMPORAL ===
        with tab1:
            st.subheader("📈 Evolución Temporal del Flujo de Caja")
            grafico_evolucion_temporal(stats_actual)

            # Estadísticas adicionales
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📊 Estadísticas del Período**")
                st.write(f"• Días totales: {stats_actual['dias_periodo']}")
                st.write(f"• Días con actividad: {stats_actual['dias_con_datos']}")
                st.write(f"• Promedio ingresos/día: {formatear_monto(stats_actual['promedio_ingreso_dia'])}")
                st.write(f"• Promedio egresos/día: {formatear_monto(stats_actual['promedio_egreso_dia'])}")

            with col2:
                st.markdown("**🎯 Proyecciones**")
                if ratios['dias_hasta_cero']:
                    st.warning(f"⏱️ Con el gasto actual, el balance llegará a cero en **{ratios['dias_hasta_cero']} días**")
                else:
                    st.success("✅ El balance actual es sostenible con el flujo de ingresos")

                # Proyección mensual
                ingresos_proyectados = stats_actual['promedio_ingreso_dia'] * 30
                egresos_proyectados = stats_actual['promedio_egreso_dia'] * 30
                balance_proyectado = ingresos_proyectados - egresos_proyectados

                st.write(f"• Proyección ingresos mes: {formatear_monto(ingresos_proyectados)}")
                st.write(f"• Proyección egresos mes: {formatear_monto(egresos_proyectados)}")
                st.write(f"• Balance proyectado mes: {formatear_monto(balance_proyectado)}")

        # === TAB 2: CATEGORÍAS ===
        with tab2:
            st.subheader("🏷️ Análisis Detallado por Categorías")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 💵 Ingresos")
                grafico_categorias_detallado(stats_actual, "ingreso")

            with col2:
                st.markdown("### 💸 Egresos")
                grafico_categorias_detallado(stats_actual, "egreso")

        # === TAB 3: COMPARACIÓN PERSONAS ===
        with tab3:
            st.subheader("👥 Comparación Multi-Persona")

            if filtros['comparar_personas'] or len(filtros['personas_list']) > 1:
                grafico_comparacion_personas(
                    session,
                    filtros['fecha_desde'],
                    filtros['fecha_hasta'],
                    filtros['personas_list']
                )

                # Análisis individual por persona
                st.markdown("---")
                st.subheader("📊 Análisis Individual por Persona")

                for persona in filtros['personas_list']:
                    with st.expander(f"👤 {persona}"):
                        stats_persona = calcular_estadisticas_por_persona(
                            session,
                            filtros['fecha_desde'],
                            filtros['fecha_hasta'],
                            persona
                        )

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Ingresos", formatear_monto(stats_persona['total_ingresos']))
                        with col2:
                            st.metric("Egresos", formatear_monto(stats_persona['total_egresos']))
                        with col3:
                            st.metric("Balance", formatear_monto(stats_persona['balance']))

                        # Top 3 categorías
                        if stats_persona['categorias_egresos']:
                            st.markdown("**Top 3 Egresos:**")
                            top_egresos = sorted(stats_persona['categorias_egresos'].items(), key=lambda x: x[1], reverse=True)[:3]
                            for idx, (cat, monto) in enumerate(top_egresos, 1):
                                st.write(f"{idx}. {cat}: {formatear_monto(monto)}")
            else:
                st.info("Activa la opción 'Comparar todas las personas' en el panel de control para ver este análisis")

        # === TAB 4: TRANSACCIONES ===
        with tab4:
            st.subheader("📋 Listado Completo de Transacciones")
            tabla_transacciones_completa(session, filtros)

    # ==================== FOOTER ====================

    st.markdown("---")
    st.markdown(
        f"**FacturIA 2.1.0** - Dashboard Profesional de Análisis Financiero | "
        f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()

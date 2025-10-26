"""
Dashboard de FacturIA 2.0 con Streamlit
Visualización en tiempo real de transacciones financieras
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys

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
from src.config import CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS

# Configuración de la página
st.set_page_config(
    page_title="FacturIA 2.0 - Dashboard Financiero",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .big-metric {
        font-size: 2.5rem !important;
        font-weight: bold;
    }
    .positive {
        color: #00CC00;
    }
    .negative {
        color: #FF4444;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def inicializar_db():
    """Inicializa la conexión a la base de datos"""
    try:
        db = get_database()
        return db
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None


def formatear_monto(monto):
    """Formatea un monto con separadores de miles"""
    return f"${monto:,.2f}".replace(",", ".")


def mostrar_kpis(stats):
    """Muestra los KPIs principales"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💵 Total Ingresos",
            value=formatear_monto(stats['total_ingresos']),
            delta=f"{stats['cantidad_ingresos']} transacciones"
        )

    with col2:
        st.metric(
            label="💸 Total Egresos",
            value=formatear_monto(stats['total_egresos']),
            delta=f"{stats['cantidad_egresos']} transacciones",
            delta_color="inverse"
        )

    with col3:
        balance = stats['balance']
        st.metric(
            label="📊 Balance",
            value=formatear_monto(balance),
            delta="Positivo" if balance > 0 else "Negativo",
            delta_color="normal" if balance > 0 else "inverse"
        )

    with col4:
        total = stats['total_transacciones']
        st.metric(
            label="📄 Transacciones Totales",
            value=f"{total}",
            delta=f"{stats['cantidad_ingresos'] + stats['cantidad_egresos']}"
        )


def grafico_ingresos_vs_egresos(stats):
    """Gráfico de barras: Ingresos vs Egresos"""
    fig = go.Figure(data=[
        go.Bar(
            name='Ingresos',
            x=['Transacciones'],
            y=[stats['total_ingresos']],
            marker_color='#00CC66'
        ),
        go.Bar(
            name='Egresos',
            x=['Transacciones'],
            y=[stats['total_egresos']],
            marker_color='#FF6666'
        )
    ])

    fig.update_layout(
        title="Ingresos vs Egresos",
        yaxis_title="Monto ($)",
        barmode='group',
        height=400
    )

    return fig


def grafico_categorias_pie(categorias, titulo, colores):
    """Gráfico de torta para categorías"""
    if not categorias:
        return None

    df = pd.DataFrame([
        {"Categoría": k, "Monto": v}
        for k, v in categorias.items()
    ])

    fig = px.pie(
        df,
        values='Monto',
        names='Categoría',
        title=titulo,
        color_discrete_sequence=colores
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)

    return fig


def tabla_transacciones_recientes(transacciones):
    """Tabla con las transacciones más recientes"""
    if not transacciones:
        st.info("No hay transacciones para mostrar")
        return

    # Convertir a DataFrame
    data = []
    for t in transacciones:
        data.append({
            "ID": t.id,
            "Fecha": t.fecha_transaccion.strftime('%Y-%m-%d %H:%M') if t.fecha_transaccion else "N/A",
            "Tipo": t.tipo.value.upper() if t.tipo else "N/A",
            "Categoría": t.categoria,
            "Monto": formatear_monto(t.monto),
            "Descripción": t.descripcion[:50] if t.descripcion else "",
            "Emisor/Receptor": t.emisor_receptor[:30] if t.emisor_receptor else "N/A"
        })

    df = pd.DataFrame(data)

    # Mostrar tabla con formato
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


def filtros_sidebar():
    """Sidebar con filtros"""
    st.sidebar.title("⚙️ Filtros")

    # Filtro de período
    st.sidebar.subheader("Período")

    opciones_periodo = {
        "Hoy": 0,
        "Últimos 7 días": 7,
        "Últimos 30 días": 30,
        "Mes actual": -1,
        "Personalizado": -2
    }

    periodo = st.sidebar.selectbox(
        "Seleccionar período",
        list(opciones_periodo.keys()),
        index=2  # Default: Últimos 30 días
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

    else:
        dias = opciones_periodo[periodo]
        fecha_desde = hoy - timedelta(days=dias)
        fecha_hasta = hoy

    # Filtro de tipo
    st.sidebar.subheader("Tipo de Transacción")
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

    # Filtro de categoría
    st.sidebar.subheader("Categoría")

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

    return {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "tipo": tipo_map[tipo_filtro],
        "categoria": categoria
    }


def main():
    """Función principal del dashboard"""

    # Título
    st.title("💰 FacturIA 2.0 - Dashboard Financiero")
    st.markdown("---")

    # Inicializar base de datos
    db = inicializar_db()

    if db is None:
        st.error("No se pudo conectar a la base de datos. Verifica la configuración.")
        return

    # Verificar conexión
    if not db.verificar_conexion():
        st.error("Error de conexión a la base de datos")
        return

    # Filtros sidebar
    filtros = filtros_sidebar()

    # Botón de refrescar
    col_refresh, col_auto = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refrescar"):
            st.rerun()

    with col_auto:
        auto_refresh = st.checkbox("Auto-refrescar cada 30s", value=False)

    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()

    st.markdown("---")

    # Obtener estadísticas del período
    with db.get_session() as session:
        stats = calcular_estadisticas_periodo(
            session,
            filtros['fecha_desde'],
            filtros['fecha_hasta']
        )

        # Mostrar KPIs
        st.header("📊 Resumen del Período")
        mostrar_kpis(stats)

        st.markdown("---")

        # Gráficos principales
        st.header("📈 Análisis Visual")

        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de ingresos vs egresos
            fig1 = grafico_ingresos_vs_egresos(stats)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Balance del período
            fig_balance = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=stats['balance'],
                title={'text': "Balance del Período"},
                delta={'reference': 0},
                gauge={
                    'axis': {'range': [None, stats['total_ingresos']]},
                    'bar': {'color': "darkgreen" if stats['balance'] > 0 else "darkred"},
                    'steps': [
                        {'range': [0, stats['total_ingresos'] * 0.5], 'color': "lightgray"},
                        {'range': [stats['total_ingresos'] * 0.5, stats['total_ingresos']], 'color': "gray"}
                    ],
                }
            ))
            fig_balance.update_layout(height=400)
            st.plotly_chart(fig_balance, use_container_width=True)

        # Gráficos de categorías
        col3, col4 = st.columns(2)

        with col3:
            if stats['categorias_ingresos']:
                fig_ingresos = grafico_categorias_pie(
                    stats['categorias_ingresos'],
                    "Distribución de Ingresos",
                    px.colors.sequential.Greens
                )
                st.plotly_chart(fig_ingresos, use_container_width=True)
            else:
                st.info("No hay ingresos en este período")

        with col4:
            if stats['categorias_egresos']:
                fig_egresos = grafico_categorias_pie(
                    stats['categorias_egresos'],
                    "Distribución de Egresos",
                    px.colors.sequential.Reds
                )
                st.plotly_chart(fig_egresos, use_container_width=True)
            else:
                st.info("No hay egresos en este período")

        st.markdown("---")

        # Top categorías
        st.header("🏆 Top Categorías")

        col5, col6 = st.columns(2)

        with col5:
            st.subheader("Ingresos Principales")
            top_ingresos = obtener_top_categorias(session, "ingreso", 5)

            if top_ingresos:
                for idx, cat in enumerate(top_ingresos, 1):
                    st.write(f"{idx}. **{cat['categoria']}**: {formatear_monto(cat['total'])} ({cat['cantidad']} transacciones)")
            else:
                st.info("No hay datos")

        with col6:
            st.subheader("Egresos Principales")
            top_egresos = obtener_top_categorias(session, "egreso", 5)

            if top_egresos:
                for idx, cat in enumerate(top_egresos, 1):
                    st.write(f"{idx}. **{cat['categoria']}**: {formatear_monto(cat['total'])} ({cat['cantidad']} transacciones)")
            else:
                st.info("No hay datos")

        st.markdown("---")

        # Transacciones recientes
        st.header("📋 Transacciones Recientes")

        transacciones = obtener_transacciones(
            session,
            tipo=filtros['tipo'],
            categoria=filtros['categoria'],
            fecha_desde=filtros['fecha_desde'],
            fecha_hasta=filtros['fecha_hasta'],
            limite=50
        )

        tabla_transacciones_recientes(transacciones)

    # Footer
    st.markdown("---")
    st.markdown(
        "**FacturIA 2.0** - Sistema de Gestión Financiera Automatizado | "
        f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    main()

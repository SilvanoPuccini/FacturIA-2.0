"""
Interfaz Completa de Revisión y Edición Manual de Transacciones
FacturIA 2.1.0 - Sistema Profesional de Gestión Financiera
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database import (
    get_database,
    obtener_transacciones,
    obtener_transaccion,
    actualizar_transaccion,
    eliminar_transaccion,
    crear_transaccion
)
from src.config import CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS
from src.database.models import TipoTransaccion

# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="FacturIA 2.1.0 - Revisar y Editar",
    page_icon="📝",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
.stAlert {
    border-radius: 10px;
}
.edit-form {
    background-color: #1E2127;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #00CC66;
}
</style>
""", unsafe_allow_html=True)

# ==================== FUNCIONES AUXILIARES ====================

def formatear_monto(monto: float) -> str:
    """Formatea un monto con separadores"""
    return f"${monto:,.2f}".replace(",", ".")


def parsear_monto(monto_str: str) -> float:
    """Parsea un string de monto a float"""
    try:
        # Remover símbolos y espacios
        monto_limpio = monto_str.replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
        return float(monto_limpio)
    except ValueError:
        return 0.0


# ==================== MAIN ====================

st.title("📝 Revisar y Editar Transacciones")
st.markdown("**Gestión Manual de Transacciones - FacturIA 2.1.0**")
st.markdown("---")

# Inicializar base de datos
db = get_database()

if not db or not db.verificar_conexion():
    st.error("❌ Error al conectar con la base de datos. Verifica la configuración.")
    st.stop()

# ==================== MODO DE OPERACIÓN ====================

modo = st.radio(
    "Modo de Operación",
    ["📋 Ver y Editar", "➕ Crear Nueva Transacción"],
    horizontal=True
)

st.markdown("---")

# ==================== MODO: CREAR NUEVA TRANSACCIÓN ====================

if modo == "➕ Crear Nueva Transacción":
    st.subheader("➕ Crear Nueva Transacción")

    with st.form("form_crear", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            tipo_nuevo = st.selectbox(
                "Tipo *",
                ["ingreso", "egreso"],
                help="Tipo de transacción"
            )

            # Categorías según el tipo
            if tipo_nuevo == "ingreso":
                categorias_disponibles = CATEGORIAS_INGRESOS
            else:
                categorias_disponibles = CATEGORIAS_EGRESOS

            categoria_nuevo = st.selectbox(
                "Categoría *",
                categorias_disponibles,
                help="Categoría de la transacción"
            )

            monto_nuevo = st.number_input(
                "Monto *",
                min_value=0.01,
                value=100.0,
                step=10.0,
                format="%.2f",
                help="Monto de la transacción"
            )

            fecha_nuevo = st.date_input(
                "Fecha *",
                value=datetime.now().date(),
                help="Fecha de la transacción"
            )

        with col2:
            persona_nuevo = st.text_input(
                "Persona",
                value="General",
                help="Nombre de la persona asociada a la transacción"
            )

            emisor_receptor_nuevo = st.text_input(
                "Emisor/Receptor",
                help="Nombre de la empresa o persona"
            )

            numero_comprobante_nuevo = st.text_input(
                "Número de Comprobante",
                help="Ej: 001-00012345"
            )

        descripcion_nuevo = st.text_area(
            "Descripción",
            help="Descripción detallada de la transacción"
        )

        submitted = st.form_submit_button("✅ Crear Transacción", use_container_width=True)

        if submitted:
            if not categoria_nuevo or monto_nuevo <= 0:
                st.error("❌ Completa todos los campos obligatorios (*)")
            else:
                try:
                    with db.get_session() as session:
                        nueva_transaccion = {
                            "tipo": tipo_nuevo,
                            "categoria": categoria_nuevo,
                            "monto": monto_nuevo,
                            "fecha_transaccion": datetime.combine(fecha_nuevo, datetime.min.time()),
                            "persona": persona_nuevo or "General",
                            "emisor_receptor": emisor_receptor_nuevo,
                            "descripcion": descripcion_nuevo,
                            "numero_comprobante": numero_comprobante_nuevo,
                            "origen": "csv",  # Manual
                            "procesado_por_ia": False,
                            "editado_manualmente": True,
                            "requiere_revision": False
                        }

                        transaccion_creada = crear_transaccion(session, nueva_transaccion)

                        st.success(f"✅ Transacción #{transaccion_creada.id} creada exitosamente!")
                        st.balloons()

                except Exception as e:
                    st.error(f"❌ Error al crear transacción: {e}")

# ==================== MODO: VER Y EDITAR ====================

else:
    # Filtros
    with st.expander("🔍 Filtros", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            filtro_tipo = st.selectbox(
                "Tipo",
                ["Todas", "Ingresos", "Egresos"]
            )

        with col2:
            filtro_requiere_revision = st.selectbox(
                "Estado de Revisión",
                ["Todas", "Requiere revisión", "Revisadas"]
            )

        with col3:
            filtro_limite = st.number_input(
                "Cantidad a mostrar",
                min_value=10,
                max_value=500,
                value=100,
                step=10
            )

    # Obtener transacciones con filtros
    with db.get_session() as session:
        tipo_filtrado = None
        if filtro_tipo == "Ingresos":
            tipo_filtrado = "ingreso"
        elif filtro_tipo == "Egresos":
            tipo_filtrado = "egreso"

        transacciones = obtener_transacciones(
            session,
            tipo=tipo_filtrado,
            limite=int(filtro_limite)
        )

        # Filtrar por revisión si es necesario
        if filtro_requiere_revision == "Requiere revisión":
            transacciones = [t for t in transacciones if t.requiere_revision]
        elif filtro_requiere_revision == "Revisadas":
            transacciones = [t for t in transacciones if not t.requiere_revision]

        # Mostrar estadísticas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📊 Total Transacciones", len(transacciones))

        with col2:
            requieren_revision = sum(1 for t in transacciones if t.requiere_revision)
            st.metric("⚠️ Requieren Revisión", requieren_revision)

        with col3:
            editadas = sum(1 for t in transacciones if t.editado_manualmente)
            st.metric("✏️ Editadas Manualmente", editadas)

        with col4:
            procesadas_ia = sum(1 for t in transacciones if t.procesado_por_ia)
            st.metric("🤖 Procesadas por IA", procesadas_ia)

        st.markdown("---")

        # Tabla de transacciones
        if transacciones:
            st.subheader(f"📋 Listado de Transacciones ({len(transacciones)})")

            # Crear DataFrame para visualización
            data = []
            for t in transacciones:
                status = []
                if t.requiere_revision:
                    status.append("⚠️")
                if t.editado_manualmente:
                    status.append("✏️")
                if t.procesado_por_ia:
                    status.append("🤖")

                data.append({
                    "ID": t.id,
                    "Estado": " ".join(status) if status else "✅",
                    "Fecha": t.fecha_transaccion.strftime('%Y-%m-%d') if t.fecha_transaccion else "N/A",
                    "Tipo": "💵" if t.tipo == TipoTransaccion.INGRESO else "💸",
                    "Categoría": t.categoria,
                    "Monto": formatear_monto(t.monto),
                    "Persona": t.persona or "General",
                    "Emisor/Receptor": (t.emisor_receptor[:20] + "...") if t.emisor_receptor and len(t.emisor_receptor) > 20 else (t.emisor_receptor or ""),
                    "Descripción": (t.descripcion[:30] + "...") if t.descripcion and len(t.descripcion) > 30 else (t.descripcion or "")
                })

            df = pd.DataFrame(data)

            # Mostrar tabla
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Monto": st.column_config.TextColumn("Monto", help="Monto de la transacción"),
                    "Estado": st.column_config.TextColumn("Estado", help="⚠️=Revisión ✏️=Editada 🤖=IA ✅=OK")
                }
            )

            st.markdown("---")

            # ==================== SECCIÓN DE EDICIÓN ====================

            st.subheader("✏️ Editar Transacción")

            # Selector de transacción a editar
            transaccion_id_editar = st.number_input(
                "ID de Transacción a Editar",
                min_value=1,
                value=1,
                step=1,
                help="Ingresa el ID de la transacción que deseas editar"
            )

            # Obtener transacción a editar
            transaccion_editar = obtener_transaccion(session, int(transaccion_id_editar))

            if transaccion_editar:
                # Mostrar información actual
                with st.expander(f"📄 Transacción #{transaccion_editar.id} - Información Actual", expanded=True):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Tipo:** {transaccion_editar.tipo.value.upper() if transaccion_editar.tipo else 'N/A'}")
                        st.write(f"**Categoría:** {transaccion_editar.categoria}")
                        st.write(f"**Monto:** {formatear_monto(transaccion_editar.monto)}")

                    with col2:
                        st.write(f"**Fecha:** {transaccion_editar.fecha_transaccion.strftime('%Y-%m-%d') if transaccion_editar.fecha_transaccion else 'N/A'}")
                        st.write(f"**Persona:** {transaccion_editar.persona or 'General'}")
                        st.write(f"**Emisor/Receptor:** {transaccion_editar.emisor_receptor or 'N/A'}")

                    with col3:
                        st.write(f"**Requiere Revisión:** {'⚠️ Sí' if transaccion_editar.requiere_revision else '✅ No'}")
                        st.write(f"**Procesada por IA:** {'🤖 Sí' if transaccion_editar.procesado_por_ia else '❌ No'}")
                        st.write(f"**Editada:** {'✏️ Sí' if transaccion_editar.editado_manualmente else '❌ No'}")

                    if transaccion_editar.descripcion:
                        st.write(f"**Descripción:** {transaccion_editar.descripcion}")

                    if transaccion_editar.requiere_revision and hasattr(transaccion_editar, 'razon_revision'):
                        st.warning(f"⚠️ Razón de revisión: {transaccion_editar.razon_revision}")

                # Formulario de edición
                st.markdown("### 📝 Editar Valores")

                with st.form(f"form_editar_{transaccion_id_editar}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        tipo_editado = st.selectbox(
                            "Tipo",
                            ["ingreso", "egreso"],
                            index=0 if transaccion_editar.tipo == TipoTransaccion.INGRESO else 1
                        )

                        # Categorías según el tipo
                        if tipo_editado == "ingreso":
                            categorias_disponibles = CATEGORIAS_INGRESOS
                        else:
                            categorias_disponibles = CATEGORIAS_EGRESOS

                        # Índice de categoría actual
                        try:
                            indice_categoria = categorias_disponibles.index(transaccion_editar.categoria)
                        except ValueError:
                            indice_categoria = 0

                        categoria_editada = st.selectbox(
                            "Categoría",
                            categorias_disponibles,
                            index=indice_categoria
                        )

                        monto_editado = st.number_input(
                            "Monto",
                            min_value=0.01,
                            value=float(transaccion_editar.monto),
                            step=10.0,
                            format="%.2f"
                        )

                        fecha_editada = st.date_input(
                            "Fecha",
                            value=transaccion_editar.fecha_transaccion.date() if transaccion_editar.fecha_transaccion else date.today()
                        )

                    with col2:
                        persona_editada = st.text_input(
                            "Persona",
                            value=transaccion_editar.persona or "General"
                        )

                        emisor_receptor_editado = st.text_input(
                            "Emisor/Receptor",
                            value=transaccion_editar.emisor_receptor or ""
                        )

                        numero_comprobante_editado = st.text_input(
                            "Número de Comprobante",
                            value=transaccion_editar.numero_comprobante or ""
                        )

                    descripcion_editada = st.text_area(
                        "Descripción",
                        value=transaccion_editar.descripcion or ""
                    )

                    requiere_revision_editado = st.checkbox(
                        "Marcar como 'Requiere Revisión'",
                        value=transaccion_editar.requiere_revision
                    )

                    col_btn1, col_btn2 = st.columns([1, 1])

                    with col_btn1:
                        guardar = st.form_submit_button("✅ Guardar Cambios", use_container_width=True)

                    with col_btn2:
                        eliminar = st.form_submit_button("⚠️ Eliminar Permanentemente", use_container_width=True, type="secondary")

                    if guardar:
                        try:
                            datos_actualizados = {
                                "tipo": TipoTransaccion(tipo_editado),
                                "categoria": categoria_editada,
                                "monto": monto_editado,
                                "fecha_transaccion": datetime.combine(fecha_editada, datetime.min.time()),
                                "persona": persona_editada,
                                "emisor_receptor": emisor_receptor_editado,
                                "descripcion": descripcion_editada,
                                "numero_comprobante": numero_comprobante_editado,
                                "requiere_revision": requiere_revision_editado,
                                "editado_manualmente": True,
                                "fecha_ultima_edicion": datetime.now()
                            }

                            actualizar_transaccion(session, transaccion_id_editar, datos_actualizados)

                            st.success(f"✅ Transacción #{transaccion_id_editar} actualizada exitosamente!")
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ Error al actualizar transacción: {e}")

                    if eliminar:
                        try:
                            eliminar_transaccion(session, transaccion_id_editar)
                            st.success(f"🗑️ Transacción #{transaccion_id_editar} eliminada exitosamente!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al eliminar transacción: {e}")

            else:
                st.warning(f"⚠️ No se encontró transacción con ID #{transaccion_id_editar}")

        else:
            st.info("📭 No hay transacciones que coincidan con los filtros. Ejecuta: `python crear_datos_prueba.py`")

# Footer
st.markdown("---")
st.caption("**FacturIA 2.1.0** - Sistema de Gestión Financiera Automatizado con IA | Interfaz de Revisión Manual")

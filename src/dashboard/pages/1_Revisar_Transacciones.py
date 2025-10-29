"""Interfaz de Revisión Manual de Transacciones"""
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database import get_database, obtener_transacciones, obtener_transaccion, actualizar_transaccion
from src.config import CATEGORIAS_INGRESOS, CATEGORIAS_EGRESOS
from src.database.models import TipoTransaccion

st.set_page_config(page_title="FacturIA 2.0 - Revisar", page_icon="📝", layout="wide")
st.title("📝 Revisar y Editar Transacciones")
st.markdown("Interfaz de revisión manual - FacturIA 2.1.0")

db = get_database()
if db and db.verificar_conexion():
    with db.get_session() as session:
        transacciones = obtener_transacciones(session, limite=100)
        
        st.subheader(f"📋 Total: {len(transacciones)} transacciones")
        
        if transacciones:
            data = []
            for t in transacciones:
                data.append({
                    "ID": t.id,
                    "Fecha": t.fecha_transaccion.strftime('%Y-%m-%d') if t.fecha_transaccion else "N/A",
                    "Tipo": t.tipo.value.upper() if t.tipo else "N/A",
                    "Categoría": t.categoria,
                    "Monto": f"${t.monto:,.2f}",
                    "Persona": getattr(t, 'persona', 'General') or "General",
                    "Descripción": (t.descripcion[:50] + "...") if t.descripcion and len(t.descripcion) > 50 else (t.descripcion or "")
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.info("💡 Interfaz de edición completa próximamente")
        else:
            st.info("No hay transacciones. Ejecuta: python crear_datos_prueba.py")
else:
    st.error("Error al conectar con la base de datos")

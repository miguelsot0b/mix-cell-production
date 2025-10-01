import streamlit as st
import pandas as pd
import numpy as np
import math
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Producción MIX",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🏭 Sistema de Planificación de Producción MIX")
st.markdown("---")

def clean_number(value):
    """Limpia números que pueden tener comas y los convierte a enteros"""
    if pd.isna(value) or value == '' or value == 0:
        return 0
    try:
        # Convertir a string y remover comas
        cleaned = str(value).replace(',', '').replace('$', '').strip()
        return int(float(cleaned)) if cleaned else 0
    except (ValueError, TypeError):
        return 0

def analyze_prp_for_cell(prp_df, part_numbers):
    """Analiza el archivo PRP para obtener información de las partes de una celda específica"""
    results = []
    
    for part_number in part_numbers:
        # Filtrar para esta parte específica y solo Customer Releases
        part_data = prp_df[
            (prp_df['Part No'] == part_number) & 
            (prp_df['Demand Type'] == 'Customer Releases')
        ]
        
        if part_data.empty:
            continue
            
        # Obtener la primera fila (debería ser única)
        row = part_data.iloc[0]
        
        # Obtener inventario FG actual
        inv_fg = clean_number(row.get('Inv FG', 0))
        
        # Sumar TODOS los Customer Releases (Past Due + todas las fechas futuras)
        total_customer_releases = 0
        
        # Past Due
        total_customer_releases += clean_number(row.get('Past Due', 0))
        
        # Todas las columnas de fecha
        date_columns = [col for col in prp_df.columns if '/' in str(col) and col != 'Fecha De Actualizacion']
        for date_col in date_columns:
            total_customer_releases += clean_number(row.get(date_col, 0))
        
        # Calcular déficit: Customer Releases - Inventario FG
        deficit = total_customer_releases - inv_fg
        
        if deficit > 0:  # Solo si hay déficit
            results.append({
                'part_number': part_number,
                'total_customer_releases': total_customer_releases,
                'inv_fg': inv_fg,
                'deficit': deficit
            })
    
    return results

def calculate_containers_needed(deficit, parts_df, part_number):
    """Calcula cuántos contenedores se necesitan para una parte específica"""
    # Buscar el tamaño del contenedor para esta parte
    part_info = parts_df[parts_df['part_numbers'] == part_number]
    
    if part_info.empty:
        return 0
    
    container_size = part_info.iloc[0]['pieces_per_container']
    container_size = clean_number(container_size)
    
    if container_size <= 0:
        return 0
    
    # Calcular contenedores necesarios (redondear hacia arriba)
    containers = math.ceil(deficit / container_size)
    return containers

def get_top_3_critical_parts(prp_analysis, parts_df):
    """Obtiene las 3 partes más críticas basadas en mayor déficit"""
    if len(prp_analysis) == 0:
        return []
    
    # Ordenar por déficit (descendente) - los que más necesitan producción
    sorted_parts = sorted(prp_analysis, key=lambda x: x['deficit'], reverse=True)
    
    # Tomar las primeras 3 partes con mayor déficit
    top_3 = sorted_parts[:3]
    
    # Calcular contenedores para cada parte
    for part in top_3:
        part['containers'] = calculate_containers_needed(
            part['deficit'], parts_df, part['part_number']
        )
    
    return top_3

def get_visual_color(parts_df, part_number):
    """Obtiene el color visual basado en visual_id"""
    try:
        part_info = parts_df[parts_df['part_numbers'] == part_number]
        if not part_info.empty:
            visual_id = part_info.iloc[0]['visual_id']
            
            color_map = {
                'Amarillo': '#FFF3CD',
                'Naranja': '#FFE4B5', 
                'Rosa': '#FFE4E1',
                'Verde': '#D4EDDA',
                'Blanco': '#F8F9FA'
            }
            
            return color_map.get(visual_id, '#F8F9FA')
    except:
        pass
    return '#F8F9FA'

# Cache para datos con auto-refresh cada 10 minutos
@st.cache_data(ttl=600)
def load_data():
    """Carga los datos desde archivos CSV"""
    try:
        parts_df = pd.read_csv("data/parts_data.csv")
        prp_df = pd.read_csv("data/prp.csv")
        return parts_df, prp_df
    except FileNotFoundError as e:
        st.error(f"❌ No se encontró el archivo: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    # Auto-refresh setup
    if 'last_refresh_time' not in st.session_state:
        st.session_state.last_refresh_time = time.time()

    current_time = time.time()
    if current_time - st.session_state.last_refresh_time > 600:  # 10 minutos
        st.session_state.last_refresh_time = current_time
        st.cache_data.clear()
        st.rerun()

    # Cargar y validar datos
    try:
        parts_df, prp_df = load_data()
        
        if parts_df.empty or prp_df.empty:
            st.error("❌ No se pudieron cargar los datos necesarios")
            return
        
        # Verificar que existen las columnas requeridas
        required_parts_cols = ['cell_name', 'part_numbers', 'pieces_per_container', 'family']
        missing_cols = [col for col in required_parts_cols if col not in parts_df.columns]
        if missing_cols:
            st.error(f"❌ Error: Faltan columnas en parts_data.csv: {missing_cols}")
            st.stop()
            
        if 'Part No' not in prp_df.columns:
            st.error("❌ Error: No se encontró la columna 'Part No' en prp.csv")
            st.stop()
            
    except Exception as e:
        st.error(f"❌ Error al validar datos: {str(e)}")
        return

    # Sidebar para controles
    with st.sidebar:
        st.header("🏭 Selección de Producción")
        
        # Dropdown 1: Cell Name (sin repetir)
        cell_names = sorted(parts_df['cell_name'].unique().tolist())
        selected_cell = st.selectbox(
            "📍 Celda:",
            options=cell_names,
            help="Selecciona la celda de producción"
        )
        
        # Dropdown 2: Family (tipos de familia)
        families = sorted(parts_df['family'].unique().tolist())
        selected_family = st.selectbox(
            "🎯 Familia:",
            options=families,
            help="Selecciona el tipo de familia"
        )

    # Área principal
    with st.container():
        # Filtrar por la celda y familia seleccionadas
        filtered_parts = parts_df[
            (parts_df['cell_name'] == selected_cell) & 
            (parts_df['family'] == selected_family)
        ]
        
        if filtered_parts.empty:
            st.warning(f"⚠️ No se encontraron partes para la celda '{selected_cell}' y familia '{selected_family}'")
            return
        
        # Obtener los números de parte para esta combinación
        part_numbers = []
        for _, row in filtered_parts.iterrows():
            part_numbers_str = row['part_numbers']
            part_numbers.extend([p.strip() for p in part_numbers_str.split(',')])
        
        # Análisis PRP
        with st.spinner("🔍 Analizando datos de PRP..."):
            prp_analysis = analyze_prp_for_cell(prp_df, part_numbers)
            
        
        if not prp_analysis:
            st.success("✅ No hay partes críticas para esta celda en este momento")
            st.info("Todas las partes tienen suficiente inventario para cubrir los Customer Releases")
            return
        
        # Obtener TOP 3 partes críticas
        top_3_parts = get_top_3_critical_parts(prp_analysis, parts_df)
        
        if not top_3_parts:
            st.success("✅ No hay partes críticas para esta celda en este momento")
            return
        
        # Mostrar TOP 3
        st.markdown("## 🎯 SECUENCIA DE PRODUCCIÓN")
        st.markdown("### Los siguientes contenedores deben producirse:")
        st.markdown("---")
        
        cols = st.columns(3)
        
        for i, part_info in enumerate(top_3_parts):
            part_number = part_info['part_number']
            containers = part_info['containers']
            deficit = part_info['deficit']
            
            # Obtener color de fondo
            bg_color = get_visual_color(parts_df, part_number)
            
            with cols[i]:
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 25px; border-radius: 15px; 
                            margin: 10px 0; border-left: 8px solid #d73502; 
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); text-align: center;">
                    <h3 style="margin: 0; color: #d73502;">
                        #{i+1}
                    </h3>
                    <h4 style="margin: 15px 0; color: #333; font-weight: bold;">
                        {part_number}
                    </h4>
                    <div style="margin: 20px 0;">
                        <div style="font-size: 48px; font-weight: bold; color: #d73502;">
                            {containers}
                        </div>
                        <div style="font-size: 18px; color: #666; margin: 10px 0;">
                            CONTENEDORES
                        </div>
                    </div>
                    <div style="font-size: 14px; color: #666; border-top: 1px solid #ddd; padding-top: 15px;">
                        <strong>Faltante: {deficit:,} piezas</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Información adicional de la celda
        st.markdown("---")
        st.markdown("## 📊 Información de la Celda")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🏭 Celda", selected_cell)
            
        with col2:
            st.metric("🎯 Familia", selected_family)
            
        with col3:
            # Obtener el rate de cualquier parte de esta celda (todas tienen el mismo rate)
            if not filtered_parts.empty:
                rate = clean_number(filtered_parts.iloc[0].get('rate_per_hour', 0))
                st.metric("⚡ Rate/Hora", f"{rate:,}")
            else:
                st.metric("⚡ Rate/Hora", "N/A")

if __name__ == "__main__":
    main()
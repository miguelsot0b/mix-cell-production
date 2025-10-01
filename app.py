import streamlit as st
import pandas as pd
import numpy as np
import math
from datetime import datetime
import time
import gdown
import os
import requests
from config import *

# Configuración de Google Drive se importa desde config.py

def download_from_google_drive(file_id, output_path):
    """Descarga un archivo desde Google Drive usando su ID"""
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)
        return True
    except Exception as e:
        st.error(f"{MESSAGES['error_loading']}{e}")
        return False

def check_file_age(file_path, max_age_seconds=AUTO_UPDATE_INTERVAL):
    """Verifica si un archivo necesita actualizarse basado en su edad"""
    if not os.path.exists(file_path):
        return True  # Archivo no existe, necesita descarga
    
    file_age = time.time() - os.path.getmtime(file_path)
    return file_age > max_age_seconds

def update_prp_file():
    """Actualiza el archivo PRP desde Google Drive si es necesario"""
    
    # Verificar si necesita actualización
    if check_file_age(PRP_FILE_PATH):
        st.info(MESSAGES['updating'])
        
        # Crear directorio si no existe
        os.makedirs(DATA_FOLDER, exist_ok=True)
        
        # Intentar descargar desde Google Drive
        if GOOGLE_DRIVE_PRP_ID != "TU_ID_DEL_ARCHIVO_AQUI":
            success = download_from_google_drive(GOOGLE_DRIVE_PRP_ID, PRP_FILE_PATH)
            if success:
                st.success(MESSAGES['updated'])
                return True
            else:
                st.warning(MESSAGES['update_failed'])
        else:
            st.warning(MESSAGES['no_id'])
    
    return os.path.exists(PRP_FILE_PATH)

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
        past_due = clean_number(row.get('Past Due', 0))
        
        # Simular día por día para encontrar cuándo se queda sin inventario
        running_inventory = inv_fg - past_due  # Restar Past Due primero
        
        # Obtener columnas de fechas ordenadas
        date_columns = [col for col in prp_df.columns if '/' in str(col) and col != 'Fecha De Actualizacion']
        date_columns_sorted = sorted(date_columns, key=lambda x: pd.to_datetime(x, format='%m/%d/%Y'))
        
        first_shortage_date = None
        deficit_amount = 0
        
        # Revisar día por día hasta encontrar déficit
        for date_col in date_columns_sorted:
            daily_demand = clean_number(row.get(date_col, 0))
            running_inventory -= daily_demand
            
            # Si el inventario se vuelve negativo, encontramos el primer déficit
            if running_inventory < 0 and first_shortage_date is None:
                first_shortage_date = pd.to_datetime(date_col, format='%m/%d/%Y')
                deficit_amount = abs(running_inventory)
                break
        
        # Solo incluir si hay déficit (inventario insuficiente)
        if first_shortage_date is not None:
            results.append({
                'part_number': part_number,
                'inv_fg': inv_fg,
                'past_due': past_due,
                'first_shortage_date': first_shortage_date,
                'deficit': deficit_amount,
                'days_until_shortage': (first_shortage_date - pd.Timestamp.now()).days
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
    """Obtiene las 3 partes más críticas basadas en fecha más cercana y mayor déficit"""
    if len(prp_analysis) == 0:
        return []
    
    # Ordenar por: 1) Fecha más cercana (ascendente), 2) Mayor déficit (descendente)
    sorted_parts = sorted(prp_analysis, key=lambda x: (x['first_shortage_date'], -x['deficit']))
    
    # Tomar las primeras 3 partes más críticas
    top_3 = sorted_parts[:3]
    
    # Calcular contenedores para cada parte
    for part in top_3:
        part['containers'] = calculate_containers_needed(
            part['deficit'], parts_df, part['part_number']
        )
    
    return top_3

def get_visual_color(parts_df, part_number):
    """Obtiene el color visual basado en visual_id con colores mejorados para operadores"""
    try:
        part_info = parts_df[parts_df['part_numbers'] == part_number]
        if not part_info.empty:
            visual_id = part_info.iloc[0]['visual_id']
            
            # Colores mejorados y más vibrantes para operadores
            color_map = {
                'Amarillo': '#FFE135',    # Amarillo brillante
                'Naranja': '#FF8C42',     # Naranja vibrante
                'Rosa': '#FF69B4',        # Rosa fuerte
                'Verde': '#32CD32',       # Verde lima brillante
                'Blanco': '#F5F5F5'       # Blanco suave
            }
            
            return color_map.get(visual_id, '#E8E8E8')  # Gris claro por defecto
    except:
        pass
    return '#E8E8E8'  # Gris claro por defecto

# Cache para datos con auto-refresh inteligente
@st.cache_data(ttl=CACHE_TTL)  # Cache basado en configuración
def load_data():
    """Carga los datos desde archivos CSV con actualización automática desde Google Drive"""
    try:
        # Actualizar archivo PRP desde Google Drive si es necesario
        update_prp_file()
        
        # Cargar datos
        parts_df = pd.read_csv(PARTS_FILE_PATH)
        prp_df = pd.read_csv(PRP_FILE_PATH)
        
        # Mostrar información de última actualización
        if os.path.exists(PRP_FILE_PATH):
            last_modified = datetime.fromtimestamp(os.path.getmtime(PRP_FILE_PATH))
            st.sidebar.info(f"{MESSAGES['last_update']}{last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return parts_df, prp_df
    except FileNotFoundError as e:
        st.error(f"{MESSAGES['file_not_found']}{str(e)}")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"{MESSAGES['error_loading']}{str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    # Sidebar con controles
    st.sidebar.header("🔧 Controles")
    
    # Botón para forzar actualización de datos
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        # Limpiar cache
        st.cache_data.clear()
        # Forzar descarga desde Google Drive
        if os.path.exists(PRP_FILE_PATH):
            os.remove(PRP_FILE_PATH)  # Eliminar archivo local para forzar descarga
        st.rerun()
    
    # Información del sistema de actualización
    st.sidebar.markdown("### 📡 Sistema de Actualización")
    st.sidebar.info("• Verifica cada 30 minutos si hay nuevos datos\n• Descarga automáticamente desde Google Drive\n• Usa archivo local como respaldo")
    
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
                
                # Obtener color de fondo basado en visual_id
                bg_color = get_visual_color(parts_df, part_number)
                
                with cols[i]:
                    # Usar componentes nativos de Streamlit en lugar de HTML personalizado
                    with st.container():
                        # Badge de prioridad y título
                        st.markdown(f"<div style='background-color: #d73502; color: white; padding: 5px 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;'><strong>PRIORIDAD #{i+1}</strong></div>", unsafe_allow_html=True)
                        
                        # Número de parte con color de fondo
                        st.markdown(f"<div style='background-color: {bg_color}; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px; border: 2px solid rgba(0,0,0,0.1);'><strong>{part_number}</strong></div>", unsafe_allow_html=True)
                        
                        # Número de contenedores grande
                        st.markdown(f"<div style='text-align: center; margin: 20px 0;'><div style='font-size: 64px; font-weight: 900; color: #d73502; margin: 0;'>{containers}</div><div style='font-size: 20px; color: #333; font-weight: bold;'>CONTENEDORES</div></div>", unsafe_allow_html=True)
                        
                        # Información del faltante
                        st.markdown(f"<div style='background-color: rgba(215,53,2,0.1); padding: 10px; border-radius: 10px; text-align: center; border-top: 3px solid #d73502;'><strong style='color: #d73502;'>Faltante: {deficit:,} piezas</strong></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
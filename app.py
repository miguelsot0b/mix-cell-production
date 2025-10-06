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

def get_next_update_time():
    """Calcula cuándo será la próxima actualización programada"""
    now = datetime.now()
    current_minute = now.minute
    
    if current_minute < 5:
        # Próxima actualización a los :05 de esta hora
        next_update = now.replace(minute=5, second=0, microsecond=0)
    elif current_minute < 35:
        # Próxima actualización a los :35 de esta hora
        next_update = now.replace(minute=35, second=0, microsecond=0)
    else:
        # Próxima actualización a los :05 de la siguiente hora
        if now.hour == 23:
            next_update = now.replace(hour=0, minute=5, second=0, microsecond=0) + pd.Timedelta(days=1)
        else:
            next_update = now.replace(hour=now.hour+1, minute=5, second=0, microsecond=0)
    
    total_seconds = (next_update - now).total_seconds()
    minutes_until = int(total_seconds / 60)
    seconds_until = int(total_seconds % 60)
    
    return next_update, minutes_until, seconds_until, total_seconds

def format_countdown_message(minutes, seconds):
    """Formatea el mensaje del contador de manera dinámica"""
    if minutes >= 3:
        return f"🕐 Próxima actualización: en {minutes} minutos"
    elif minutes > 0:
        return f"🕐 Próxima actualización: en {minutes} minutos y {seconds} segundos"
    else:
        return f"🕐 Próxima actualización: en {seconds} segundos"

def check_file_age(file_path, max_age_seconds=None, force_update=False):
    """Verifica si un archivo necesita actualizarse basado en horarios específicos (minuto 5 y 35 de cada hora)"""
    if not os.path.exists(file_path):
        return True  # Archivo no existe, necesita descarga
    
    if force_update:
        return True  # Forzar actualización
    
    # Obtener tiempo actual
    now = datetime.now()
    current_minute = now.minute
    
    # Obtener última modificación del archivo
    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    # Determinar si estamos en una ventana de actualización (minutos 5-7 o 35-37 para dar margen)
    is_update_window = (5 <= current_minute <= 7) or (35 <= current_minute <= 37)
    
    if not is_update_window:
        return False  # No estamos en ventana de actualización
    
    # Si estamos en ventana de actualización, verificar si ya se actualizó en esta ventana
    # Calcular la ventana actual (hora + minuto específico)
    if 5 <= current_minute <= 7:
        current_window = now.replace(minute=5, second=0, microsecond=0)
    else:  # 35 <= current_minute <= 37
        current_window = now.replace(minute=35, second=0, microsecond=0)
    
    # Si el archivo fue modificado después del inicio de la ventana actual, no actualizar
    if last_modified >= current_window:
        return False
    
    return True  # Necesita actualización

def update_prp_file(force_update=False):
    """Actualiza el archivo PRP desde Google Drive si es necesario"""
    
    # Verificar si necesita actualización
    if check_file_age(PRP_FILE_PATH, force_update=force_update):
        # Crear directorio si no existe
        os.makedirs(DATA_FOLDER, exist_ok=True)
        
        # Intentar descargar desde Google Drive
        if GOOGLE_DRIVE_PRP_ID != "TU_ID_DEL_ARCHIVO_AQUI":
            # Mostrar mensaje temporal de actualización
            update_placeholder = st.empty()
            update_placeholder.info(MESSAGES['updating'])
            
            success = download_from_google_drive(GOOGLE_DRIVE_PRP_ID, PRP_FILE_PATH)
            
            # Limpiar mensaje temporal
            update_placeholder.empty()
            
            if success:
                # Mostrar mensaje de éxito temporalmente (se limpia automáticamente al recargar)
                success_placeholder = st.empty()
                success_placeholder.success(MESSAGES['updated'])
                return True
            else:
                # Solo mostrar error permanentemente
                st.error(MESSAGES['update_failed'])
                return False
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

# Función para agregar auto-refresh HTML
def add_auto_refresh(interval_seconds):
    """Agrega meta refresh para auto-actualización de página"""
    refresh_html = f"""
    <meta http-equiv="refresh" content="{interval_seconds}">
    <script>
        // Auto-refresh adicional con JavaScript como backup
        setTimeout(function(){{
            window.location.reload();
        }}, {interval_seconds * 1000});
    </script>
    """
    st.markdown(refresh_html, unsafe_allow_html=True)

# CSS minimalista para layout limpio
st.markdown("""
<style>
    .main .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

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
    """Analiza el archivo PRP para obtener información de las partes con demanda secuencial inteligente"""
    # Primero, recopilar TODAS las demandas de TODAS las partes con sus fechas
    all_demands = []
    
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
        
        # Calcular inventario disponible inicial
        available_inventory = inv_fg - past_due
        
        # Obtener columnas de fechas ordenadas
        date_columns = [col for col in prp_df.columns if '/' in str(col) and col != 'Fecha De Actualizacion']
        date_columns_sorted = sorted(date_columns, key=lambda x: pd.to_datetime(x, format='%m/%d/%Y'))
        
        # Simular inventario día por día para encontrar déficits
        running_inventory = available_inventory
        max_days_to_analyze = 30  # Analizar máximo 30 días (1 mes) hacia adelante
        days_analyzed = 0
        
        for date_col in date_columns_sorted:
            if days_analyzed >= max_days_to_analyze:
                break
                
            daily_demand = clean_number(row.get(date_col, 0))
            
            if daily_demand > 0:
                running_inventory -= daily_demand
                
                # Si hay déficit, agregar a lista global
                if running_inventory < 0:
                    shortage_amount = min(daily_demand, abs(running_inventory))
                    all_demands.append({
                        'part_number': part_number,
                        'date': pd.to_datetime(date_col, format='%m/%d/%Y'),
                        'demand': shortage_amount,
                        'inv_fg': inv_fg,
                        'past_due': past_due
                    })
            
            days_analyzed += 1
    
    # Si no hay demandas faltantes, retornar vacío
    if not all_demands:
        return []
    
    # Ordenar todas las demandas por fecha
    all_demands.sort(key=lambda x: x['date'])
    
    # Agrupar demandas secuenciales por parte
    results = []
    current_part = None
    current_group = []
    
    for demand in all_demands:
        if current_part != demand['part_number']:
            # Si cambia la parte, procesar el grupo anterior
            if current_group:
                total_demand = sum(d['demand'] for d in current_group)
                first_date = current_group[0]['date']
                
                results.append({
                    'part_number': current_part,
                    'inv_fg': current_group[0]['inv_fg'],
                    'past_due': current_group[0]['past_due'],
                    'first_shortage_date': first_date,
                    'deficit': total_demand,
                    'days_until_shortage': (first_date - pd.Timestamp.now()).days
                })
            
            # Iniciar nuevo grupo
            current_part = demand['part_number']
            current_group = [demand]
        else:
            # Misma parte, agregar al grupo actual
            current_group.append(demand)
    
    # Procesar el último grupo
    if current_group:
        total_demand = sum(d['demand'] for d in current_group)
        first_date = current_group[0]['date']
        
        results.append({
            'part_number': current_part,
            'inv_fg': current_group[0]['inv_fg'],
            'past_due': current_group[0]['past_due'],
            'first_shortage_date': first_date,
            'deficit': total_demand,
            'days_until_shortage': (first_date - pd.Timestamp.now()).days
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
    """Obtiene las 3 partes más críticas con lógica de continuidad inteligente día por día"""
    if len(prp_analysis) == 0:
        return []
    
    # Ordenar por: 1) Fecha más cercana (ascendente), 2) Mayor déficit (descendente)
    sorted_parts = sorted(prp_analysis, key=lambda x: (x['first_shortage_date'], -x['deficit']))
    
    # Agrupar por fechas para análisis día por día
    daily_groups = {}
    for part in sorted_parts:
        date_key = part['first_shortage_date'].date()
        if date_key not in daily_groups:
            daily_groups[date_key] = []
        daily_groups[date_key].append(part)
    
    # Ordenar fechas
    sorted_dates = sorted(daily_groups.keys())
    
    # NUEVA LÓGICA: Continuidad inteligente día por día
    result_sequence = []
    processed_parts = set()
    
    for current_date in sorted_dates:
        current_day_parts = daily_groups[current_date]
        
        # Si es el primer día y solo hay una parte, buscar continuidad
        if len(current_day_parts) == 1:
            part = current_day_parts[0]
            part_number = part['part_number']
            
            if part_number in processed_parts:
                continue
                
            # Buscar si esta parte continúa en días siguientes
            total_containers = calculate_containers_needed(part['deficit'], parts_df, part_number)
            total_deficit = part['deficit']
            grouped_days = [current_date]
            
            # Revisar días subsecuentes para esta misma parte
            for next_date in sorted_dates[sorted_dates.index(current_date) + 1:]:
                next_day_parts = daily_groups[next_date]
                
                # Buscar si la misma parte aparece en el día siguiente
                same_part_in_next_day = None
                for next_part in next_day_parts:
                    if next_part['part_number'] == part_number:
                        same_part_in_next_day = next_part
                        break
                
                if same_part_in_next_day:
                    # Continuar agrupando esta parte
                    total_containers += calculate_containers_needed(same_part_in_next_day['deficit'], parts_df, part_number)
                    total_deficit += same_part_in_next_day['deficit']
                    grouped_days.append(next_date)
                else:
                    # Esta parte ya no aparece en días siguientes, terminar agrupación
                    break
            
            # Crear entrada agrupada
            grouped_part = part.copy()
            grouped_part['containers'] = total_containers
            grouped_part['deficit'] = total_deficit
            grouped_part['kanban_group_date'] = current_date
            grouped_part['kanban_sequence'] = len(result_sequence) + 1
            
            if len(grouped_days) > 1:
                grouped_part['is_grouped'] = True
                grouped_part['grouped_containers'] = total_containers
                grouped_part['grouped_days'] = len(grouped_days)
            
            result_sequence.append(grouped_part)
            processed_parts.add(part_number)
            
        else:
            # Día con múltiples partes - procesar individualmente por déficit
            day_parts_sorted = sorted(current_day_parts, key=lambda x: -x['deficit'])
            
            for part in day_parts_sorted:
                if part['part_number'] in processed_parts:
                    continue
                    
                part['containers'] = calculate_containers_needed(part['deficit'], parts_df, part['part_number'])
                part['kanban_group_date'] = current_date
                part['kanban_sequence'] = len(result_sequence) + 1
                
                # Marcar si es mismo día con otras partes
                if len(current_day_parts) > 1:
                    part['is_same_day_group'] = True
                
                result_sequence.append(part)
                processed_parts.add(part['part_number'])
        
        # Limitar a TOP 3 para evitar lista muy larga
        if len(result_sequence) >= 3:
            break
    
    return result_sequence[:3]

def detect_same_day_session(current_parts):
    """Detecta si hay múltiples partes del mismo día en la lista actual"""
    if not current_parts:
        return False
    
    today = datetime.now().date()
    
    # Contar cuántas partes críticas son para HOY
    same_day_count = 0
    for part in current_parts:
        if part['first_shortage_date'].date() == today:
            same_day_count += 1
    
    # Si hay 2 o más partes para hoy = sesión activa
    return same_day_count >= 2

def save_daily_sequence(sequence, session_state):
    """Guarda la secuencia del día en session_state"""
    today = datetime.now().date()
    
    # Guardar solo los identificadores esenciales
    stored_sequence = []
    for i, part in enumerate(sequence):
        stored_sequence.append({
            'part_number': part['part_number'],
            'original_priority': i + 1,
            'kanban_group_date': part.get('kanban_group_date', today)
        })
    
    # Guardar en session_state
    session_state['daily_kanban_sequence'] = stored_sequence
    session_state['kanban_sequence_date'] = today

def load_stored_sequence(session_state):
    """Recupera la secuencia guardada si es del día actual"""
    today = datetime.now().date()
    
    # Verificar si hay secuencia guardada y es de hoy
    if ('daily_kanban_sequence' in session_state and 
        'kanban_sequence_date' in session_state and
        session_state['kanban_sequence_date'] == today):
        
        return session_state['daily_kanban_sequence']
    
    return None  # No hay secuencia guardada o es de otro día

def apply_stored_sequence(stored_sequence, current_sequence):
    """Aplica la secuencia guardada a los datos actuales"""
    result = []
    
    # Crear un diccionario de partes actuales para búsqueda rápida
    current_parts_dict = {part['part_number']: part for part in current_sequence}
    
    # Aplicar el orden guardado
    for stored_part in stored_sequence:
        part_number = stored_part['part_number']
        
        # Si la parte aún existe en datos actuales
        if part_number in current_parts_dict:
            # Tomar datos actuales pero mantener prioridad original
            current_part = current_parts_dict[part_number].copy()
            current_part['locked_priority'] = stored_part['original_priority']
            current_part['is_sequence_locked'] = True
            result.append(current_part)
    
    return result[:3]  # Limitar a TOP 3

def detect_pull_ahead(current_sequence, stored_sequence):
    """Detecta si hay un pull ahead que requiere romper el lock de secuencia"""
    if not stored_sequence or not current_sequence:
        return False
    
    # Obtener la fecha más temprana de la secuencia guardada
    stored_earliest_date = None
    for stored_part in stored_sequence:
        # La fecha se guarda como kanban_group_date
        stored_date = stored_part.get('kanban_group_date')
        if stored_date and (stored_earliest_date is None or stored_date < stored_earliest_date):
            stored_earliest_date = stored_date
    
    # Obtener la fecha más temprana de la secuencia actual
    current_earliest_date = None
    for current_part in current_sequence:
        current_date = current_part['first_shortage_date'].date()
        if current_earliest_date is None or current_date < current_earliest_date:
            current_earliest_date = current_date
    
    # Si la fecha más temprana actual es anterior a la guardada = PULL AHEAD
    if (stored_earliest_date and current_earliest_date and 
        current_earliest_date < stored_earliest_date):
        return True
    
    return False

def get_top_3_critical_parts_with_lock(prp_analysis, parts_df, session_state):
    """Versión mejorada que respeta la secuencia diaria para evitar cambios innecesarios, 
    pero detecta pull ahead para casos urgentes"""
    if len(prp_analysis) == 0:
        return []
    
    # PASO 1: Calcular secuencia actual normal
    current_sequence = get_top_3_critical_parts(prp_analysis, parts_df)
    
    # PASO 2: Verificar si hay sesión del mismo día activa
    if detect_same_day_session(current_sequence):
        
        # PASO 3: Intentar cargar secuencia guardada
        stored_sequence = load_stored_sequence(session_state)
        
        if stored_sequence:
            # PASO 4: DETECTAR PULL AHEAD antes de aplicar lock
            if detect_pull_ahead(current_sequence, stored_sequence):
                # PULL AHEAD DETECTADO - Romper lock y crear nueva secuencia
                save_daily_sequence(current_sequence, session_state)
                # Marcar las partes nuevas como pull ahead para mostrar al operador
                for part in current_sequence:
                    if part['first_shortage_date'].date() < datetime.now().date():
                        part['is_pull_ahead'] = True
                return current_sequence
            
            # PASO 5: No hay pull ahead - Aplicar secuencia guardada a datos actuales
            locked_sequence = apply_stored_sequence(stored_sequence, current_sequence)
            if locked_sequence:
                return locked_sequence
    
    # PASO 6: Primera vez del día o no hay sesión activa
    # Guardar nueva secuencia
    save_daily_sequence(current_sequence, session_state)
    return current_sequence

def get_part_description(parts_df, part_number):
    """Obtiene la descripción de una parte específica"""
    try:
        part_info = parts_df[parts_df['part_numbers'] == part_number]
        if not part_info.empty:
            description = part_info.iloc[0]['description']
            return description if pd.notna(description) else ""
    except:
        pass
    return ""

def get_visual_color(parts_df, part_number):
    """Obtiene el color visual basado en visual_id con colores mejorados para operadores"""
    try:
        part_info = parts_df[parts_df['part_numbers'] == part_number]
        if not part_info.empty:
            visual_id = part_info.iloc[0]['visual_id']
            
            # Colores mejorados y más vibrantes para operadores
            color_map = {
                'Amarillo': '#FFE135',      # Amarillo brillante
                'Naranja': '#FF8C42',       # Naranja vibrante
                'Rosa': '#FF69B4',          # Rosa fuerte
                'Verde': '#32CD32',         # Verde lima brillante
                'Blanco': '#F5F5F5',        # Blanco suave
                'Verde Menta': '#00E5A0',   # Verde menta brillante
                'Azul': '#4169E1',          # Azul real vibrante
                'Cafe Claro': '#D2B48C'     # Café claro beige
            }
            
            return color_map.get(visual_id, '#E8E8E8')  # Gris claro por defecto
    except:
        pass
    return '#E8E8E8'  # Gris claro por defecto

# Cache para datos con auto-refresh inteligente
@st.cache_data(ttl=CACHE_TTL)  # Cache basado en configuración
def load_data(force_update=False):
    """Carga los datos desde archivos CSV con actualización automática desde Google Drive"""
    try:
        # Actualizar archivo PRP desde Google Drive si es necesario
        update_prp_file(force_update=force_update)
        
        # Cargar datos
        parts_df = pd.read_csv(PARTS_FILE_PATH)
        prp_df = pd.read_csv(PRP_FILE_PATH)
        
        # Mostrar información de última actualización desde el CSV de manera discreta
        if not prp_df.empty and 'Fecha De Actualizacion' in prp_df.columns:
            # Obtener la fecha de actualización del PRP (todas las filas tienen la misma fecha)
            fecha_actualizacion = prp_df['Fecha De Actualizacion'].iloc[0]
            try:
                # Convertir a datetime para mejor formato
                fecha_dt = pd.to_datetime(fecha_actualizacion)
                # Solo mostrar en sidebar si no se mostró arriba recientemente
                if 'data_timestamp' not in st.session_state or st.session_state.data_timestamp != fecha_dt:
                    st.sidebar.info(f"📅 Última actualización: {fecha_dt.strftime('%H:%M:%S')}")
            except:
                st.sidebar.info(f"📅 Última actualización: {fecha_actualizacion}")
        elif os.path.exists(PRP_FILE_PATH):
            # Fallback a fecha de modificación del archivo si no hay columna
            last_modified = datetime.fromtimestamp(os.path.getmtime(PRP_FILE_PATH))
            st.sidebar.info(f"📅 Archivo local: {last_modified.strftime('%H:%M:%S')}")
        
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
    
    # Configuración de auto-refresh con persistencia usando URL params
    st.sidebar.markdown("### ⚙️ Configuración")
    
    # Obtener parámetros de URL para persistencia
    query_params = st.query_params
    url_refresh_enabled = query_params.get("refresh_enabled", "true").lower() == "true"
    url_refresh_interval = int(query_params.get("refresh_interval", "300"))
    
    # Inicializar configuración con valores de URL o defaults
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = url_refresh_enabled
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = url_refresh_interval
    
    auto_refresh_enabled = st.sidebar.checkbox(
        "🔄 Auto-refresh página", 
        value=st.session_state.auto_refresh_enabled,
        key="auto_refresh_checkbox",
        help="Refresca la página automáticamente"
    )
    
    # Actualizar session_state
    st.session_state.auto_refresh_enabled = auto_refresh_enabled
    
    if auto_refresh_enabled:
        # Encontrar el índice actual basado en el valor guardado
        options = [60, 300, 600, 900]  # 1, 5, 10, 15 minutos en segundos
        try:
            current_index = options.index(st.session_state.refresh_interval)
        except ValueError:
            current_index = 1  # Default a 5 minutos si no se encuentra
        
        refresh_interval = st.sidebar.selectbox(
            "⏱️ Intervalo de refresh:",
            options=options,
            format_func=lambda x: f"{x//60} minutos" if x >= 60 else f"{x} segundos",
            index=current_index,
            key="refresh_interval_select",
            help="Cada cuánto tiempo se refresca automáticamente la página"
        )
        
        # Actualizar session_state con la nueva selección
        st.session_state.refresh_interval = refresh_interval
        
        # Actualizar URL params para persistencia
        st.query_params.update({
            "refresh_enabled": "true",
            "refresh_interval": str(refresh_interval)
        })
        
    else:
        refresh_interval = 0  # Deshabilitado
        # Actualizar URL params
        st.query_params.update({
            "refresh_enabled": "false",
            "refresh_interval": "300"
        })
    
    # Botón para forzar actualización de datos
    if st.sidebar.button("🔄 Actualizar Datos Ahora"):
        with st.spinner("Actualizando datos..."):
            # Limpiar cache
            st.cache_data.clear()
            # Forzar descarga desde Google Drive
            if os.path.exists(PRP_FILE_PATH):
                os.remove(PRP_FILE_PATH)  # Eliminar archivo local para forzar descarga
            # Limpiar timestamp para mostrar nueva información
            if 'data_timestamp' in st.session_state:
                del st.session_state.data_timestamp
        st.rerun()
    
    # Calcular próxima actualización
    next_update, minutes_until, seconds_until, total_seconds = get_next_update_time()
    
    # Crear contador dinámico que se actualiza automáticamente
    countdown_message = format_countdown_message(minutes_until, seconds_until)
    
    # Mostrar contador en sidebar con colores según urgencia
    if total_seconds <= 60:  # Último minuto - rojo
        st.sidebar.error(countdown_message)
    elif total_seconds <= 180:  # Últimos 3 minutos - amarillo
        st.sidebar.warning(countdown_message)
    else:  # Normal - verde
        st.sidebar.success(countdown_message)
    
    # Verificar si se está forzando una actualización automática
    now = datetime.now()
    current_minute = now.minute
    
    # Forzar actualización si estamos en ventana de actualización
    force_update = (5 <= current_minute <= 7) or (35 <= current_minute <= 37)
    
    # También forzar si el archivo es muy viejo (más de 1 hora)
    if os.path.exists(PRP_FILE_PATH):
        last_modified = datetime.fromtimestamp(os.path.getmtime(PRP_FILE_PATH))
        hours_old = (now - last_modified).total_seconds() / 3600
        if hours_old > 1:
            force_update = True
    
    if force_update and 'last_forced_update' not in st.session_state:
        # Limpiar cache y forzar actualización solo una vez por sesión en cada ventana
        st.cache_data.clear()
        if os.path.exists(PRP_FILE_PATH):
            os.remove(PRP_FILE_PATH)  # Eliminar archivo local para forzar descarga
        st.session_state.last_forced_update = now.strftime('%H:%M')

    # Cargar y validar datos
    try:
        parts_df, prp_df = load_data(force_update=force_update)
        
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
        
        # Solo usar query params como último recurso si no hay nada en session_state
        if "cell_selection" not in st.session_state:
            query_params = st.query_params
            if query_params.get("selected_cell") and query_params.get("selected_cell") in cell_names:
                default_cell_index = cell_names.index(query_params.get("selected_cell"))
            else:
                default_cell_index = 0
        else:
            # Si ya existe en session_state, usar ese valor
            try:
                default_cell_index = cell_names.index(st.session_state.cell_selection)
            except (ValueError, KeyError):
                default_cell_index = 0
                
        selected_cell = st.selectbox(
            "📍 Celda:",
            options=cell_names,
            index=default_cell_index,
            key="cell_selection",
            help="Selecciona la celda de producción"
        )
        
        # Dropdown 2: Family (tipos de familia)
        families = sorted(parts_df['family'].unique().tolist())
        
        # Solo usar query params como último recurso si no hay nada en session_state
        if "family_selection" not in st.session_state:
            query_params = st.query_params
            if query_params.get("selected_family") and query_params.get("selected_family") in families:
                default_family_index = families.index(query_params.get("selected_family"))
            else:
                default_family_index = 0
        else:
            # Si ya existe en session_state, usar ese valor
            try:
                default_family_index = families.index(st.session_state.family_selection)
            except (ValueError, KeyError):
                default_family_index = 0
                
        selected_family = st.selectbox(
            "🎯 Familia:",
            options=families,
            index=default_family_index,
            key="family_selection",
            help="Selecciona el tipo de familia"
        )
        
        # Actualizar URL params inmediatamente cuando hay cambios
        current_url_cell = query_params.get("selected_cell")
        current_url_family = query_params.get("selected_family")
        
        if selected_cell != current_url_cell or selected_family != current_url_family:
            # Actualizar query params de Streamlit
            st.query_params.update({
                "refresh_enabled": query_params.get('refresh_enabled', 'true'),
                "refresh_interval": query_params.get('refresh_interval', '60'),
                "selected_cell": selected_cell,
                "selected_family": selected_family
            })

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
    
    # Obtener TOP 3 partes críticas con lock de secuencia Kanban
    top_3_parts = get_top_3_critical_parts_with_lock(prp_analysis, parts_df, st.session_state)
    
    if not top_3_parts:
        st.success("✅ No hay partes críticas para esta celda en este momento")
        return
    
    # Mostrar TOP 3
    st.markdown("## 🎯 SECUENCIA DE PRODUCCIÓN")
    
    # Indicador de secuencia bloqueada y pull ahead
    if any(part.get('is_pull_ahead', False) for part in top_3_parts):
        st.error("⚡ **PULL AHEAD DETECTADO**: Nueva demanda urgente encontrada. Secuencia recalculada automáticamente. ¡PRIORIDAD MÁXIMA!")
    elif any(part.get('is_sequence_locked', False) for part in top_3_parts):
        st.warning("🔒 **SECUENCIA BLOQUEADA**: Manteniendo orden original del día para evitar cambios innecesarios. La secuencia se recalculará al completar todas las partes del mismo día.")
    
    cols = st.columns(3)
    
    for i, part_info in enumerate(top_3_parts):
        part_number = part_info['part_number']
        containers = part_info['containers']
        deficit = part_info['deficit']
        
        # Obtener color de fondo basado en visual_id
        bg_color = get_visual_color(parts_df, part_number)
        
        # Obtener descripción de la parte
        part_description = get_part_description(parts_df, part_number)
        
        # Indicador de agrupación Kanban (mismo día), bloqueo de secuencia, pull ahead y partes agrupadas
        kanban_indicator = ""
        if part_info.get('is_pull_ahead', False):
            kanban_indicator = "⚡ PULL AHEAD"
        elif part_info.get('is_sequence_locked', False):
            kanban_indicator = "🔒 SECUENCIA BLOQUEADA"
        elif part_info.get('is_grouped', False):
            kanban_indicator = "📦 PARTE AGRUPADA"
        elif part_info.get('is_same_day_group', False):
            kanban_indicator = "🔗 MISMO DÍA"
        
        with cols[i]:
            # Usar componentes nativos de Streamlit en lugar de HTML personalizado
            with st.container():
                # Badge de prioridad y título con indicador Kanban
                priority_text = f"PRIORIDAD #{i+1}"
                if kanban_indicator:
                    priority_text += f"<br><span style='font-size: 10px;'>{kanban_indicator}</span>"
                
                st.markdown(f"<div style='background-color: #d73502; color: white; padding: 5px 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;'><strong>{priority_text}</strong></div>", unsafe_allow_html=True)
                
                # Número de parte y descripción con color de fondo
                part_display = f"<strong>{part_number}</strong>"
                if part_description:
                    part_display += f"<br><span style='font-size: 12px; opacity: 0.8;'>{part_description}</span>"
                
                st.markdown(f"<div style='background-color: {bg_color}; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px; border: 2px solid rgba(0,0,0,0.1);'>{part_display}</div>", unsafe_allow_html=True)
                
                # Número de contenedores grande
                st.markdown(f"<div style='text-align: center; margin: 20px 0;'><div style='font-size: 64px; font-weight: 900; color: #d73502; margin: 0;'>{containers}</div><div style='font-size: 20px; color: #333; font-weight: bold;'>CONTENEDORES</div></div>", unsafe_allow_html=True)
                
                # Información del faltante sin fecha específica
                st.markdown(f"<div style='background-color: rgba(215,53,2,0.1); padding: 10px; border-radius: 10px; text-align: center; border-top: 3px solid #d73502;'><strong style='color: #d73502;'>Faltante: {deficit:,} piezas</strong></div>", unsafe_allow_html=True)

    # Activar auto-refresh HTML al final, después de actualizar todos los params
    if auto_refresh_enabled:
        add_auto_refresh(refresh_interval)

if __name__ == "__main__":
    main()
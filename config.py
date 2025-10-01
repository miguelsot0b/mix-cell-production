# Configuración de Google Drive
# ============================================

# ID del archivo prp.csv en Google Drive
# Para obtener el ID:
# 1. Ve a tu archivo prp.csv en Google Drive
# 2. Haz clic derecho → "Obtener enlace" o "Get link"
# 3. El enlace se verá así: https://drive.google.com/file/d/[ID_DEL_ARCHIVO]/view?usp=sharing
# 4. Copia el ID_DEL_ARCHIVO (la parte entre /d/ y /view)

GOOGLE_DRIVE_PRP_ID = "1TxKmxwy8QnUnTQTee77LgyooR_Fq1AGu"

# Configuración de actualización
AUTO_UPDATE_INTERVAL = 1800  # 30 minutos en segundos
CACHE_TTL = 300  # 5 minutos para el cache de Streamlit

# Configuración de archivos
DATA_FOLDER = "data"
PRP_FILE_PATH = "data/prp.csv"
PARTS_FILE_PATH = "data/parts_data.csv"

# Mensajes del sistema
MESSAGES = {
    "updating": "📡 Actualizando datos desde Google Drive...",
    "updated": "✅ Datos actualizados correctamente desde Google Drive",
    "update_failed": "⚠️ No se pudo actualizar desde Google Drive, usando datos locales",
    "no_id": "⚠️ ID de Google Drive no configurado, usando datos locales",
    "last_update": "📅 Última actualización: ",
    "file_not_found": "❌ No se encontró el archivo: ",
    "error_loading": "❌ Error al cargar datos: "
}
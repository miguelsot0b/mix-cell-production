# Sistema de Actualización Automática desde Google Drive

## 📋 Configuración Rápida

### Paso 1: Obtener el ID del archivo de Google Drive

1. Ve a tu archivo `prp.csv` en Google Drive
2. Haz clic derecho en el archivo → **"Obtener enlace"** o **"Get link"**
3. Asegúrate de que esté configurado como **"Cualquier persona con el enlace"**
4. Copia el enlace, se verá así:
   ```
   https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view?usp=sharing
   ```
5. Extrae solo el ID: `1A2B3C4D5E6F7G8H9I0J` (la parte entre `/d/` y `/view`)

### Paso 2: Configurar el sistema

1. Abre el archivo `config.py`
2. Reemplaza `TU_ID_DEL_ARCHIVO_AQUI` con tu ID real:
   ```python
   GOOGLE_DRIVE_PRP_ID = "1A2B3C4D5E6F7G8H9I0J"
   ```
3. Guarda el archivo

### Paso 3: ¡Listo!

La aplicación ahora:
- ✅ Verificará automáticamente cada 30 minutos si hay nuevos datos
- ✅ Descargará el archivo actualizado desde Google Drive
- ✅ Mostrará la fecha de última actualización en la barra lateral
- ✅ Tendrá un botón para forzar actualización manual

## 🔧 Configuración Avanzada

### Cambiar intervalo de actualización
En `config.py`, modifica:
```python
AUTO_UPDATE_INTERVAL = 1800  # 30 minutos en segundos
```

### Cambiar tiempo de cache
En `config.py`, modifica:
```python
CACHE_TTL = 300  # 5 minutos para el cache de Streamlit
```

## 🚀 Uso

### Actualización Automática
- La aplicación verifica automáticamente cada 30 minutos
- Si encuentra cambios, descarga la nueva versión
- Los operadores verán un mensaje de actualización

### Actualización Manual
- Usa el botón **"🔄 Actualizar Datos Ahora"** en la barra lateral
- Fuerza la descarga inmediata desde Google Drive
- Útil para actualizaciones urgentes

## 📊 Información del Sistema

La barra lateral mostrará:
- 📅 Fecha y hora de última actualización
- 🔧 Controles de actualización
- 📡 Estado del sistema de actualización

## ⚠️ Solución de Problemas

### Si no funciona la descarga:
1. Verifica que el archivo esté compartido públicamente
2. Confirma que el ID sea correcto
3. Revisa la conexión a internet

### Fallback automático:
- Si falla la descarga, usa el archivo local existente
- Los operadores verán una advertencia pero podrán trabajar

## 🔒 Seguridad

- El archivo debe estar configurado como "Cualquier persona con el enlace"
- No se requieren credenciales de Google
- Solo descarga, no modifica archivos en Drive
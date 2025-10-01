# Configuración UptimeRobot para mantener la app activa

## 🎯 **Objetivo**
Mantener la aplicación Streamlit Cloud activa 24/7 sin hibernación usando UptimeRobot (servicio externo gratuito).

## 🚀 **Pasos de configuración (5 minutos)**

### **Paso 1: Registrarse en UptimeRobot**
1. Ve a: [uptimerobot.com/signUp](https://uptimerobot.com/signUp)
2. Registrate con tu email
3. Verifica tu cuenta

### **Paso 2: Agregar monitor**
1. En el dashboard, haz clic en **"+ Add New Monitor"**
2. Configura:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Mix Cell Production App
   - **URL**: `[TU_URL_DE_STREAMLIT_CLOUD]` (obtener después del deploy)
   - **Monitoring Interval**: 5 minutes
   - **Monitor Timeout**: 30 seconds
3. Haz clic en **"Create Monitor"**

### **Paso 3: Configurar alertas (opcional)**
1. Ve a **"Alert Contacts"**
2. Agrega tu email para recibir notificaciones si la app falla
3. Configura el monitor para enviar alertas

## ✅ **Resultado**
- ✅ **Ping cada 5 minutos** (mantiene app despierta)
- ✅ **Monitoreo 24/7** sin costo
- ✅ **Alertas automáticas** si hay problemas
- ✅ **Estadísticas de uptime**
- ✅ **Cero configuración en tu código**

## 📊 **Después del deploy**
Una vez que tengas la URL de Streamlit Cloud:
1. Actualiza el monitor en UptimeRobot con la URL real
2. ¡Listo! Tu app nunca se dormirá

## 🔧 **Ventajas vs scripts locales**
- 🌐 **Externo**: No depende de tu PC o GitHub Actions
- 🆓 **Gratuito**: Plan gratuito suficiente para 1 app
- 🔄 **Confiable**: Servicio especializado en uptime monitoring
- 📱 **Dashboard**: Puedes ver estadísticas desde cualquier lugar
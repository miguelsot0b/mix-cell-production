# 🏭 Sistema de Planificación de Producción

Una aplicación web sencilla desarrollada en Streamlit para ayudar a operadores de producción a planificar y calcular requerimientos de contenedores y piezas basado en demanda y fechas de embarque.

## 📋 Características

- **Interfaz Simple**: Diseñada especialmente para operadores sin estudios profesionales
- **Cálculos Automáticos**: Determina automáticamente:
  - Cantidad de contenedores necesarios
  - Tiempo de producción requerido
  - Factibilidad de cumplir con la fecha de embarque
- **Visualización Clara**: Gráficos y métricas fáciles de entender
- **Cronograma Visual**: Muestra el plan de producción día a día

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clona o descarga el proyecto**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd mix-cell-production
   ```

2. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta la aplicación**
   ```bash
   streamlit run app.py
   ```

4. **Abre tu navegador**
   - La aplicación se abrirá automáticamente en `http://localhost:8501`
   - Si no se abre automáticamente, ve a esa dirección en tu navegador

## 📁 Estructura del Proyecto

```
mix-cell-production/
├── app.py                  # Aplicación principal de Streamlit
├── data/
│   └── parts_data.csv     # Datos de números de parte y rates
├── requirements.txt       # Dependencias de Python
└── README.md             # Este archivo
```

## 📊 Archivo de Datos

El archivo `data/parts_data.csv` contiene la información de los números de parte:

| Campo | Descripción |
|-------|-------------|
| `part_number` | Número único de la parte |
| `description` | Descripción de la parte |
| `rate_per_hour` | Piezas que se pueden producir por hora |
| `pieces_per_container` | Cantidad de piezas por contenedor |
| `family` | Familia de la parte (Panel, Bracket, etc.) |
| `setup_time_hours` | Tiempo de preparación en horas |

### Ejemplo de datos:
```csv
part_number,description,rate_per_hour,pieces_per_container,family,setup_time_hours
HEN-001,Panel Frontal Izquierdo,25,50,Panel,0.5
HEN-002,Panel Frontal Derecho,25,50,Panel,0.5
```

## 🎯 Uso de la Aplicación

### Paso 1: Seleccionar Número de Parte
- En el panel lateral izquierdo, selecciona el número de parte que necesitas producir
- La aplicación mostrará automáticamente la información de rate y piezas por contenedor

### Paso 2: Ingresar Requerimientos
- **Cantidad Total**: Ingresa cuántas piezas necesitas producir
- **Fecha de Embarque**: Selecciona cuándo debe estar lista la producción

### Paso 3: Calcular
- Haz clic en "🔄 Calcular Producción"
- La aplicación te mostrará:
  - ⏰ Tiempo necesario (días y horas)
  - 📅 Tiempo disponible hasta la fecha de embarque
  - 📦 Cantidad de contenedores necesarios
  - ✅/❌ Si es factible cumplir con la fecha

### Paso 4: Revisar Cronograma
- Ve el gráfico de cronograma para entender la distribución diaria de producción
- Identifica días de producción vs. días disponibles

## 🔧 Personalización

### Agregar Nuevos Números de Parte
1. Abre el archivo `data/parts_data.csv`
2. Agrega una nueva línea con la información de la parte:
   ```csv
   HEN-021,Nueva Parte,40,60,Familia,0.3
   ```
3. Guarda el archivo
4. Reinicia la aplicación para que los cambios tomen efecto

### Modificar Rates o Información
1. Edita directamente el archivo `data/parts_data.csv`
2. Asegúrate de mantener el formato CSV correcto
3. Reinicia la aplicación

## 🚨 Solución de Problemas

### Error: "No se encontró el archivo de datos"
- Verifica que el archivo `data/parts_data.csv` existe
- Asegúrate de estar ejecutando la aplicación desde el directorio correcto

### Error: "ModuleNotFoundError"
- Instala las dependencias: `pip install -r requirements.txt`
- Verifica que estás usando Python 3.8 o superior

### La aplicación no se abre en el navegador
- Ve manualmente a `http://localhost:8501`
- Verifica que no hay otras aplicaciones usando el puerto 8501

## 📈 Futuras Mejoras

- [ ] Agregar múltiples turnos de trabajo
- [ ] Incluir tiempo de setup en los cálculos
- [ ] Permitir planificación de múltiples partes simultáneamente
- [ ] Exportar cronogramas a Excel
- [ ] Agregar alertas de materiales y herramientas

## 🆘 Soporte

Para soporte técnico o preguntas sobre la aplicación, contacta al equipo de desarrollo.

---

**Versión**: 1.0  
**Desarrollado para**: Operadores de Producción  
**Tecnología**: Python + Streamlit
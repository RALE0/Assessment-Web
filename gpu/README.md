# Sistema de Recomendación de Cultivos con Deep Learning

Este proyecto implementa un sistema de recomendación de cultivos utilizando tres arquitecturas diferentes de redes neuronales para comparar su rendimiento en la clasificación de cultivos basada en características del suelo y condiciones climáticas.

## 📋 Descripción del Proyecto

El sistema analiza las siguientes características para recomendar el cultivo más adecuado:
- **N**: Contenido de nitrógeno en el suelo
- **P**: Contenido de fósforo en el suelo  
- **K**: Contenido de potasio en el suelo
- **Temperature**: Temperatura promedio (°C)
- **Humidity**: Humedad relativa (%)
- **pH**: Nivel de pH del suelo
- **Rainfall**: Precipitación (mm)

## 🏗️ Arquitecturas de Modelos Implementadas

### 1. DropClassifier (Baseline)
- **Descripción**: Red neuronal simple con 2 capas ocultas
- **Arquitectura**: 
  - Input (7) → Hidden (64) → Hidden (64) → Output (22)
  - Activación: ReLU
  - Sin regularización

### 2. DeepDropoutClassifier
- **Descripción**: Red neuronal profunda con regularización avanzada
- **Arquitectura**:
  - Input (7) → Hidden (128) → Hidden (256) → Hidden (128) → Hidden (64) → Output (22)
  - Batch Normalization en cada capa
  - Dropout (30%) para prevenir overfitting
  - Activación: ReLU

### 3. Conv1DClassifier
- **Descripción**: Red neuronal con capas convolucionales 1D
- **Arquitectura**:
  - Capas convolucionales: 1 → 16 → 32 → 64 canales
  - Kernel size: 3 con padding
  - Batch Normalization y Dropout (20%) en capas conv
  - Global Average Pooling
  - Capas FC finales con Dropout (30%)

## 📊 Características del Sistema

### Preprocesamiento de Datos
- ✅ Normalización con StandardScaler
- ✅ Codificación de etiquetas
- ✅ División train/validation (60%/40%)
- ✅ Shuffle de datos para mejor generalización

### Entrenamiento
- ✅ **Early Stopping Avanzado** con múltiples criterios
- ✅ Monitoreo de val_loss, val_accuracy y val_f1
- ✅ Patience adaptativo (20+ épocas)
- ✅ Detección de plateau y overfitting
- ✅ Optimizador Adam (lr=0.001)
- ✅ Cross-entropy loss
- ✅ Restauración automática del mejor modelo

### Evaluación
- ✅ Métricas por clase: Precision, Recall, F1-Score, Accuracy
- ✅ Métricas globales
- ✅ Matriz de confusión
- ✅ Análisis de tiempo de inferencia
- ✅ Comparación de complejidad (número de parámetros)

## 🚀 Uso del Sistema

### Instalación de Dependencias
```bash
pip install torch pandas scikit-learn matplotlib seaborn numpy
```

### Hacer Predicciones
```python
# Ejemplo de predicción
features = [90, 42, 43, 20.87, 82.00, 6.50, 202.93]  # N, P, K, temp, humidity, pH, rainfall
resultado = predict_crop_recommendation(features)

print(f"Cultivo recomendado: {resultado['predicted_crop']}")
print(f"Confianza: {resultado['confidence']:.3f}")
```

## 📈 Resultados y Comparación

El sistema genera automáticamente:

1. **Gráficas de Entrenamiento**: Curvas de loss para train/validation
2. **Comparación de Métricas**: Accuracy, Precision, Recall, F1-Score
3. **Análisis de Tiempo**: Tiempo de inferencia por modelo
4. **Matriz de Confusión**: Del mejor modelo
5. **Distribución por Clase**: F1-Score por tipo de cultivo
6. **Radar Chart**: Comparación visual de métricas

## 📁 Estructura del Proyecto

```
├── Recomendador.ipynb          # Script principal con los 3 modelos
├── docs  # Documentación detallada
│   ├── early_stopping.md
├── Crop_recommendation.csv  # Dataset original
├── Crop_recommendation_normalized.csv  # Dataset normalizado
├── saved_models/            # Modelos entrenados guardados
│   ├── DropClassifier.pth
│   ├── DeepDropoutClassifier.pth
│   └── Conv1DClassifier.pth
├── checkpoints_*/           # Checkpoints del Early Stopping avanzado
├── training_log_*.json      # Logs detallados de entrenamiento
├── training_history_*.png   # Gráficas de evolución de métricas
└── README.md               # Este archivo
```

## 🔧 Funciones Principales

### `train_model(model, model_name, train_loader, val_loader, device)`
Entrena un modelo con early stopping y guarda el mejor checkpoint.

### `evaluate_model(model, val_loader, device, n_classes, label_mapping)`
Evalúa un modelo y calcula todas las métricas de rendimiento.

### `predict_crop(model, features, label_mapping, device)`
Hace predicciones individuales con un modelo entrenado.

### `predict_crop_recommendation(features, model_name='best')`
Función mejorada que incluye top-3 predicciones y normalización automática.

## 📊 Métricas de Evaluación

- **Accuracy Global**: Porcentaje de predicciones correctas
- **Precision Global**: Promedio de precision por clase
- **Recall Global**: Promedio de recall por clase  
- **F1-Score Global**: Media armónica de precision y recall
- **Tiempo de Inferencia**: Milisegundos por predicción
- **Complejidad**: Número de parámetros entrenables

## 🎯 Cultivos Soportados

El sistema puede recomendar entre 22 tipos de cultivos diferentes:
- Arroz, Maíz, Trigo, Cebada, etc.
- Legumbres: Frijoles, Lentejas, Garbanzos
- Frutas: Manzana, Banana, Uva, Naranja, etc.
- Otros: Algodón, Jute, Coco, Café

## 🔍 Análisis Avanzado

El sistema incluye utilidades avanzadas para:
- Análisis de rendimiento por clase
- Identificación de mejores/peores cultivos predichos
- Benchmark de tiempo de inferencia
- Comparación de complejidad de modelos
- Generación de reportes automáticos

## 📝 Notas Técnicas

- **Dataset**: Crop Recommendation Dataset con 2200 muestras
- **Clases**: 22 tipos de cultivos balanceados (100 muestras cada uno)
- **Features**: 7 características numéricas normalizadas
- **Validación**: 40% del dataset para evaluación
- **Early Stopping**: Paciencia de 10 épocas con ventana móvil de 5

## 🆕 Sistema de Early Stopping Avanzado

### Características Mejoradas
- **Múltiples Criterios**: Monitoreo simultáneo de val_loss, val_accuracy y val_f1
- **Patience Adaptativo**: Ajuste dinámico de 20+ épocas según el progreso
- **Detección Inteligente**: Identificación de plateau y overfitting
- **Logging Completo**: Registro detallado de todas las decisiones
- **Visualizaciones**: Gráficas automáticas de evolución de métricas
- **Restauración Automática**: Carga del mejor modelo al finalizar

### Parámetros Optimizados
```python
patience = 20          # Épocas sin mejora (vs 10 anterior)
min_delta = 1e-5       # Sensibilidad alta (vs 1e-4 anterior)
window_size = 10       # Ventana móvil (vs 5 anterior)
monitor_metrics = ['val_loss', 'val_accuracy', 'val_f1']  # Múltiples métricas
```

### Archivos Generados
- `training_log_{model}.json`: Log completo de decisiones
- `training_history_{model}.png`: Gráficas de evolución
- `checkpoints_{model}/`: Mejores modelos guardados

## 👥 Contribuciones

Este proyecto fue desarrollado como parte de un sistema de recomendación de cultivos utilizando técnicas de deep learning y comparación de arquitecturas para la clase TC3002B.502 (Desarrollo de aplicaciones avanzadas de ciencias computacionales Grupo 502) impartida por el profesor Gerardo Jesús Camacho González en el Instituto Tecnológico y de Estudios Superiores de Monterrey.

## 📄 Licencia
Este proyecto está disponible bajo licencia MIT para uso educativo y de investigación.

## 📧 Contacto
Para preguntas, sugerencias o colaboraciones, contactar al equipo de desarrollo: 
- Alan Anthony Hernandez Perez: a01783347@tec.mx
- Luis Carlos Rico Almada: a01252831@tec.mx

---

**Versión del Documento**: 1.1  
**Fecha de Última Actualización**: Mayo de 2025  
**Autores**: Alan Anthony Hernandez Perez y Luis Carlos Rico Almada

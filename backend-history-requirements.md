# Requisitos del Backend para Funcionalidad de Historial de Predicciones

Este documento describe los cambios necesarios en el backend para implementar la funcionalidad de historial de predicciones para usuarios.

## Nuevas Tablas de Base de Datos

### 1. Tabla `prediction_logs`

```sql
CREATE TABLE prediction_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    input_features JSON NOT NULL,
    predicted_crop VARCHAR(255) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    top_predictions JSON NOT NULL,
    status ENUM('success', 'error') DEFAULT 'success',
    processing_time INT NULL COMMENT 'Tiempo de procesamiento en milisegundos',
    error_message TEXT NULL,
    session_id VARCHAR(255) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_status (status),
    INDEX idx_predicted_crop (predicted_crop),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 2. Tabla `prediction_statistics` (opcional para métricas)

```sql
CREATE TABLE prediction_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    total_predictions INT DEFAULT 0,
    successful_predictions INT DEFAULT 0,
    failed_predictions INT DEFAULT 0,
    most_predicted_crop VARCHAR(255) NULL,
    avg_confidence DECIMAL(5,4) NULL,
    avg_processing_time INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_date (user_id, date),
    INDEX idx_user_id (user_id),
    INDEX idx_date (date),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Nuevos Endpoints de API

### 1. Guardar Log de Predicción

**POST** `/api/prediction-logs`

```json
{
  "userId": "string",
  "inputFeatures": {
    "N": 90,
    "P": 42,
    "K": 43,
    "temperature": 20.87,
    "humidity": 82.00,
    "ph": 6.50,
    "rainfall": 202.93
  },
  "prediction": {
    "predicted_crop": "rice",
    "confidence": 0.987,
    "top_predictions": [
      {"crop": "rice", "probability": 0.987},
      {"crop": "maize", "probability": 0.012},
      {"crop": "chickpea", "probability": 0.001}
    ],
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "processingTime": 150,
  "sessionId": "session-123",
  "ipAddress": "192.168.1.1",
  "userAgent": "Mozilla/5.0..."
}
```

**Respuesta:**
```json
{
  "success": true,
  "logId": "log-uuid-123",
  "message": "Prediction log saved successfully"
}
```

### 2. Obtener Logs de Usuario

**GET** `/api/users/{userId}/prediction-logs`

**Parámetros de consulta opcionales:**
- `limit`: Número de registros (default: 50, max: 100)
- `offset`: Desplazamiento para paginación (default: 0)
- `dateFrom`: Fecha desde (formato: YYYY-MM-DD)
- `dateTo`: Fecha hasta (formato: YYYY-MM-DD)
- `crop`: Filtrar por cultivo específico
- `status`: Filtrar por estado (success/error)
- `orderBy`: Campo de ordenamiento (timestamp, confidence, crop)
- `orderDirection`: Dirección (asc/desc, default: desc)

**Ejemplo de request:**
```
GET /api/users/user-123/prediction-logs?limit=20&dateFrom=2024-01-01&crop=rice&orderBy=timestamp&orderDirection=desc
```

**Respuesta:**
```json
{
  "logs": [
    {
      "id": "log-uuid-123",
      "userId": "user-123",
      "timestamp": "2024-01-15T10:30:00Z",
      "inputFeatures": {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.87,
        "humidity": 82.00,
        "ph": 6.50,
        "rainfall": 202.93
      },
      "predictedCrop": "rice",
      "confidence": 0.987,
      "topPredictions": [
        {"crop": "rice", "probability": 0.987},
        {"crop": "maize", "probability": 0.012}
      ],
      "status": "success",
      "processingTime": 150
    }
  ],
  "pagination": {
    "total": 245,
    "limit": 20,
    "offset": 0,
    "hasMore": true
  },
  "filters": {
    "dateFrom": "2024-01-01",
    "crop": "rice"
  }
}
```

### 3. Estadísticas de Usuario

**GET** `/api/users/{userId}/prediction-statistics`

**Parámetros opcionales:**
- `period`: Período de tiempo (7d, 30d, 90d, 1y, all)
- `groupBy`: Agrupación (day, week, month)

**Respuesta:**
```json
{
  "statistics": {
    "totalPredictions": 245,
    "successfulPredictions": 242,
    "failedPredictions": 3,
    "successRate": 98.8,
    "avgConfidence": 0.932,
    "avgProcessingTime": 145,
    "mostPredictedCrop": "rice",
    "mostPredictedCropCount": 89,
    "firstPrediction": "2023-12-01T08:15:00Z",
    "lastPrediction": "2024-01-15T10:30:00Z"
  },
  "timeline": [
    {
      "date": "2024-01-15",
      "predictions": 12,
      "avgConfidence": 0.945
    }
  ],
  "cropDistribution": [
    {"crop": "rice", "count": 89, "percentage": 36.3},
    {"crop": "maize", "count": 67, "percentage": 27.3}
  ]
}
```

### 4. Exportar Logs en CSV

**GET** `/api/users/{userId}/prediction-logs/export`

**Parámetros:** Los mismos que el endpoint de obtener logs

**Respuesta:** Archivo CSV descargable

## Modificaciones al Endpoint de Predicción Existente

### Modificar POST `/predict`

El endpoint existente debe ser modificado para guardar automáticamente el log cuando un usuario autenticado hace una predicción.

**Cambios necesarios:**

1. **Detectar usuario autenticado:** Verificar si hay un token de autorización válido
2. **Medir tiempo de procesamiento:** Registrar el tiempo que toma la predicción
3. **Guardar log automáticamente:** Después de una predicción exitosa/fallida
4. **Manejar errores:** Guardar logs incluso cuando la predicción falla

**Ejemplo de flujo modificado:**

```python
@app.route('/predict', methods=['POST'])
def predict():
    start_time = time.time()
    user_id = None
    
    # Verificar si hay usuario autenticado
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)  # Función para verificar JWT
    
    try:
        # Lógica de predicción existente
        prediction_result = make_prediction(request.json)
        processing_time = int((time.time() - start_time) * 1000)
        
        # Guardar log si hay usuario autenticado
        if user_id:
            save_prediction_log({
                'user_id': user_id,
                'input_features': request.json,
                'prediction': prediction_result,
                'processing_time': processing_time,
                'status': 'success',
                'session_id': request.headers.get('X-Session-ID'),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            })
        
        return jsonify(prediction_result)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Guardar log de error si hay usuario autenticado
        if user_id:
            save_prediction_log({
                'user_id': user_id,
                'input_features': request.json,
                'status': 'error',
                'error_message': str(e),
                'processing_time': processing_time,
                'session_id': request.headers.get('X-Session-ID'),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent')
            })
        
        return jsonify({'error': str(e)}), 500
```

## Consideraciones de Seguridad

1. **Autorización:** Solo los usuarios autenticados pueden ver sus propios logs
2. **Validación:** Validar que `userId` en la URL coincida con el usuario del token JWT
3. **Limites de velocidad:** Implementar rate limiting en los endpoints de consulta
4. **Sanitización:** Limpiar y validar todos los parámetros de entrada
5. **Logs de auditoría:** Registrar accesos a datos sensibles

## Configuración y Variables de Entorno

```env
# Configuración de logs de predicción
ENABLE_PREDICTION_LOGGING=true
MAX_LOGS_PER_USER=10000
LOG_RETENTION_DAYS=365
ENABLE_LOG_COMPRESSION=true

# Configuración de exportación
MAX_EXPORT_RECORDS=5000
EXPORT_RATE_LIMIT=5  # Exportaciones por hora por usuario
```

## Scripts de Migración

### 1. Script para crear tablas

```sql
-- migration_001_create_prediction_logs.sql
CREATE TABLE prediction_logs (
    -- (Ver definición completa arriba)
);

CREATE TABLE prediction_statistics (
    -- (Ver definición completa arriba)
);
```

### 2. Script para índices adicionales

```sql
-- migration_002_add_prediction_logs_indexes.sql
CREATE INDEX idx_prediction_logs_user_timestamp ON prediction_logs(user_id, timestamp DESC);
CREATE INDEX idx_prediction_logs_crop_confidence ON prediction_logs(predicted_crop, confidence DESC);
CREATE INDEX idx_prediction_logs_status_timestamp ON prediction_logs(status, timestamp DESC);
```

## Métricas y Monitoreo

Se recomienda implementar métricas para monitorear:

1. **Volumen de logs:** Cantidad de logs generados por día/hora
2. **Tamaño de base de datos:** Crecimiento de la tabla de logs
3. **Rendimiento:** Tiempo de respuesta de consultas de logs
4. **Uso por usuario:** Usuarios más activos, patrones de uso
5. **Errores:** Tasa de fallos en predicciones por usuario

## Tareas de Mantenimiento

1. **Limpieza periódica:** Script para eliminar logs antiguos según `LOG_RETENTION_DAYS`
2. **Compresión:** Comprimir logs antiguos para ahorrar espacio
3. **Archivado:** Mover logs antiguos a almacenamiento frío
4. **Estadísticas agregadas:** Job diario para calcular estadísticas por usuario
5. **Backup:** Incluir tablas de logs en estrategia de backup

## Ejemplo de Implementación en Python/Flask

```python
# models/prediction_log.py
class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    input_features = db.Column(db.JSON, nullable=False)
    predicted_crop = db.Column(db.String(255), nullable=False)
    confidence = db.Column(db.Numeric(5,4), nullable=False)
    top_predictions = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum('success', 'error'), default='success')
    processing_time = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    session_id = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# services/prediction_log_service.py
def save_prediction_log(log_data):
    log = PredictionLog(
        user_id=log_data['user_id'],
        input_features=log_data['input_features'],
        predicted_crop=log_data.get('prediction', {}).get('predicted_crop'),
        confidence=log_data.get('prediction', {}).get('confidence'),
        top_predictions=log_data.get('prediction', {}).get('top_predictions', []),
        status=log_data.get('status', 'success'),
        processing_time=log_data.get('processing_time'),
        error_message=log_data.get('error_message'),
        session_id=log_data.get('session_id'),
        ip_address=log_data.get('ip_address'),
        user_agent=log_data.get('user_agent')
    )
    db.session.add(log)
    db.session.commit()
    return log

def get_user_prediction_logs(user_id, filters=None, pagination=None):
    query = PredictionLog.query.filter_by(user_id=user_id)
    
    # Aplicar filtros
    if filters:
        if filters.get('date_from'):
            query = query.filter(PredictionLog.timestamp >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(PredictionLog.timestamp <= filters['date_to'])
        if filters.get('crop'):
            query = query.filter(PredictionLog.predicted_crop.ilike(f"%{filters['crop']}%"))
        if filters.get('status'):
            query = query.filter(PredictionLog.status == filters['status'])
    
    # Ordenamiento
    order_by = filters.get('order_by', 'timestamp')
    order_direction = filters.get('order_direction', 'desc')
    
    if order_direction == 'desc':
        query = query.order_by(getattr(PredictionLog, order_by).desc())
    else:
        query = query.order_by(getattr(PredictionLog, order_by).asc())
    
    # Paginación
    if pagination:
        return query.paginate(
            page=pagination.get('page', 1),
            per_page=pagination.get('per_page', 50),
            error_out=False
        )
    
    return query.all()
```

Este documento proporciona una guía completa para implementar la funcionalidad de historial de predicciones en el backend de la plataforma AgriAI.
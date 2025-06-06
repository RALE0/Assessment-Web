# Backend User Token Specifications

## Resumen
Este documento especifica cómo el backend debe manejar los tokens de usuario para devolver información específica del usuario en lugar de información general del modelo/sistema.

## Endpoints que Requieren Autenticación de Usuario

### 1. Analytics Endpoints

#### 1.1 Response Time Data
- **Endpoint**: `GET /api/analytics/user/response-time-data`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Comportamiento Esperado**: 
  - Extraer `user_id` del token JWT
  - Devolver únicamente los tiempos de respuesta de las predicciones realizadas por ese usuario específico
  - Formato de respuesta:
  ```json
  {
    "data": [
      {
        "timestamp": "2025-01-01T10:00:00Z",
        "responseTime": 0.234
      }
    ],
    "timestamp": "2025-01-01T10:00:00Z"
  }
  ```

#### 1.2 User Predictions
- **Endpoint**: `GET /api/analytics/user/predictions`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Comportamiento Esperado**: 
  - Extraer `user_id` del token JWT
  - Devolver únicamente las predicciones realizadas por ese usuario específico
  - Formato de respuesta:
  ```json
  {
    "predictions": [
      {
        "date": "2025-01-01",
        "user": "username",
        "recommendedCrop": "Maíz",
        "confidence": 95.2
      }
    ],
    "timestamp": "2025-01-01T10:00:00Z"
  }
  ```

#### 1.3 Model Metrics (User-Specific)
- **Endpoint**: `GET /api/analytics/user/model-metrics`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Comportamiento Esperado**: 
  - Extraer `user_id` del token JWT
  - Calcular métricas del modelo basadas únicamente en las predicciones de ese usuario
  - Devolver métricas como precisión, recall, etc. específicas para ese usuario
  - Formato de respuesta:
  ```json
  {
    "metrics": [
      {
        "name": "Precisión del Modelo",
        "value": 97.8,
        "target": 95.0,
        "status": "excellent"
      }
    ],
    "timestamp": "2025-01-01T10:00:00Z"
  }
  ```

#### 1.4 Performance Metrics (User-Specific)
- **Endpoint**: `GET /api/analytics/user/performance-metrics`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Comportamiento Esperado**: 
  - Extraer `user_id` del token JWT
  - Calcular métricas de rendimiento basadas únicamente en las predicciones de ese usuario
  - Formato de respuesta:
  ```json
  {
    "average_response_time": 0.245,
    "p95_response_time": 0.456,
    "p99_response_time": 0.789,
    "timestamp": "2025-01-01T10:00:00Z"
  }
  ```

### 2. Dashboard Endpoints (Ya Implementados)

#### 2.1 User Dashboard Metrics
- **Endpoint**: `GET /api/dashboard/user/{userId}/metrics`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Validación Requerida**: 
  - Verificar que el `user_id` del token coincida con el `{userId}` en la URL
  - Si no coincide, devolver error 403 Forbidden

#### 2.2 User Monthly Predictions
- **Endpoint**: `GET /api/dashboard/user/{userId}/monthly-predictions`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Validación Requerida**: 
  - Verificar que el `user_id` del token coincida con el `{userId}` en la URL

#### 2.3 User Crop Distribution
- **Endpoint**: `GET /api/dashboard/user/{userId}/crop-distribution`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Validación Requerida**: 
  - Verificar que el `user_id` del token coincida con el `{userId}` en la URL

### 3. History Endpoints (Ya Implementados)

#### 3.1 User Prediction Logs
- **Endpoint**: `GET /api/users/{userId}/prediction-logs`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Validación Requerida**: 
  - Verificar que el `user_id` del token coincida con el `{userId}` en la URL

#### 3.2 User Prediction Statistics
- **Endpoint**: `GET /api/users/{userId}/prediction-statistics`
- **Headers Requeridos**: `Authorization: Bearer <token>`
- **Validación Requerida**: 
  - Verificar que el `user_id` del token coincida con el `{userId}` en la URL

## Especificaciones del Token JWT

### Payload Requerido del Token
El token JWT debe contener al menos los siguientes campos:

```json
{
  "user_id": "567ab65a-486e-486d-89de-c06aa6fee544",
  "username": "ian",
  "email": "ian@hotmail.com",
  "session_token": "XUn8sgZ1NQgjZyxop_Rj7107n0u_NWST4JGt25D89lc",
  "iat": 1749169726,
  "exp": 1749256126
}
```

### Extracción del User ID
- El backend debe extraer el `user_id` del payload del token JWT
- Usar este `user_id` para filtrar todos los datos devueltos
- **Nunca** confiar en parámetros de URL o body para el `user_id` - siempre usar el token

## Validaciones de Seguridad Requeridas

### 1. Verificación del Token
- Validar la firma del JWT
- Verificar que el token no haya expirado
- Verificar que el token sea válido y no esté en una lista negra

### 2. Autorización de Usuario
- Para endpoints con `{userId}` en la URL: verificar que el `user_id` del token coincida
- Para endpoints sin `{userId}`: usar automáticamente el `user_id` del token
- Devolver `403 Forbidden` si el usuario intenta acceder a datos de otro usuario

### 3. Manejo de Errores
- `401 Unauthorized`: Token inválido, expirado o ausente
- `403 Forbidden`: Usuario válido pero sin permisos para acceder al recurso
- `404 Not Found`: Endpoint no implementado
- `500 Internal Server Error`: Error del servidor

## Storage Token en Frontend

### Obtención del Token
```javascript
const token = localStorage.getItem('authToken');
```

### Envío del Token
```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
};
```

## Endpoints que NO Requieren User-Specific Data

Los siguientes endpoints pueden seguir devolviendo información general del sistema:

- `GET /health` - Status del sistema
- `GET /crops` - Lista de cultivos disponibles
- `GET /features` - Características del modelo
- `POST /predict` - Predicción (pero debe loggear con user_id si está autenticado)
- `GET /api/about/metrics` - Métricas generales para la página "About"

## Migración Requerida

### Endpoints a Crear/Modificar
1. **Crear**: `/api/analytics/user/response-time-data`
2. **Crear**: `/api/analytics/user/predictions` 
3. **Crear**: `/api/analytics/user/model-metrics`
4. **Crear**: `/api/analytics/user/performance-metrics`

### Endpoints Existentes a Mantener
- Los endpoints generales (`/api/analytics/*`) pueden mantenerse para uso administrativo
- Los endpoints user-specific (`/api/dashboard/user/*`, `/api/users/*`) ya están implementados correctamente

## Notas Importantes

1. **Consistencia**: Todos los endpoints user-specific deben usar el mismo patrón de autenticación
2. **Performance**: Asegurar que las consultas filtradas por `user_id` estén optimizadas con índices apropiados
3. **Logs**: Registrar todos los accesos a datos de usuario para auditoría
4. **Rate Limiting**: Implementar rate limiting por usuario para prevenir abuso
5. **Data Privacy**: Nunca incluir datos de otros usuarios en las respuestas
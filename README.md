# 🌾 Crop Recommendation Platform

> Porque sembrar a ciegas ya no es opción en 2025

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Model Accuracy](https://img.shields.io/badge/accuracy-97.8%25-brightgreen.svg)]()

## 🚀 ¿Qué es esto?

Una plataforma que le dice a los agricultores qué cultivar basándose en datos reales de su terreno. Nada de suposiciones, pura ciencia de datos aplicada al campo mexicano.

## 🎯 El Problema

Los agricultores mexicanos pierden millones cada año por:
- Elegir cultivos que no van con su tipo de suelo
- No considerar los niveles de pH y nutrientes
- Sembrar sin analizar las condiciones climáticas
- Básicamente, jugarle al adivino con sus cosechas

## 💡 La Solución

Metemos los datos del terreno → La IA hace su magia → Sale la recomendación perfecta

**Así de simple, así de poderoso.**

## ✨ Features que la rompen

### Para el Agricultor
- **Análisis instantáneo** - Mete tus datos, recibe recomendaciones en segundos
- **Predicciones confiables** - 97.8% de precisión (no es broma)
- **Histórico completo** - Todas tus consultas guardadas y organizadas
- **100% personalizado** - Cada recomendación es única para tu terreno

### Para los Datos
- **Dashboard en tiempo real** - Métricas que importan, cuando importan
- **Análisis por región** - Centro, Norte, Sur... sabemos qué funciona donde
- **Tendencias y patrones** - Ve cómo cambian las condiciones con el tiempo
- **Exporta todo** - Tus datos son tuyos, llévatelos en CSV

## 🛠️ Tech Stack

```
Frontend:       React.js + Tailwind CSS
Backend:        Node.js + Express 
Database:       PostgreSQL
ML Model:       Python + scikit-learn + torch
Infra:          OpenStack instances + Nginx
```

## 🚦 Instalación

### Prerequisitos
- Node.js 16+
- PostgreSQL 14+
- Python 3.8+

### 1. Clona el repo
```bash
git clone https://github.com/tu-usuario/crop-recommendation.git
cd crop-recommendation
```

### 2. Base de datos
```bash
psql -U postgres -f database/schema.sql
psql -U postgres -f database/seeds.sql  # Datos de prueba
```

### 3. Backend
```bash
cd backend
npm install
npm run dev
```

### 4. Frontend
```bash
cd frontend
npm install
npm start
```

## 🎮 Cómo usar

### API Endpoints

#### Hacer una predicción
```bash
POST /api/predict
{
  "location": { "lat": 19.4326, "lng": -99.1332 },
  "soilType": "loamy",
  "phLevel": 6.5,
  "nitrogen": 140,
  "phosphorus": 62,
  "potassium": 200,
  "temperature": 22.5,
  "humidity": 82.3,
  "rainfall": 202.9
}
```

#### Ver histórico
```bash
GET /api/predictions/history?page=1&limit=10
```

#### Analytics
```bash
GET /api/analytics/dashboard
```

## 📁 Estructura del Proyecto

```
crop-recommendation/
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── pages/          # Vistas principales
│   │   └── services/       # Llamadas API
│   └── public/
├── backend/
│   ├── routes/             # Endpoints API
│   ├── controllers/        # Lógica de negocio
│   ├── models/             # Modelos de datos
│   └── middleware/         # Auth, validación, etc
├── ml-model/
│   ├── notebooks/          # Jupyter notebooks
│   ├── data/              # Datasets
│   └── models/            # Modelos entrenados
└── database/
    ├── schema.sql         # Estructura DB
    └── migrations/        # Cambios
```

## 🤝 Contribuir

¿Quieres mejorar la agricultura? ¡Dale!

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: algo bien chido'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 👥 El Equipo

Somos estudiantes del Tec que queremos cambiar la forma de cultivar:

- **[Luis Rico]** - ML Engineer - *"Los datos no mienten"*
- **[Ian Holender]** - Backend Dev - *"Si funciona, no lo toques"*
- **[David Vieyra]** - Frontend Dev - *"Que se vea bonito Y funcione"*
- **[Omar Rivera]** - Full Stack - *"Siembro bugs en desarrollo, cosecho features en producción"*

## 📜 Licencia

MIT License - úsalo como quieras, pero invítanos un café si te hace millonario.

## 🙏 Agradecimientos

- A los agricultores que confían en la tecnología
- Al profe Octavio por aguantarnos
- Al café por mantenernos despiertos

---

<p align="center">
  <br>
  <sub>Y sí, funciona con maíz 🌽</sub>
</p>

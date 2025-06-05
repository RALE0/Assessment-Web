# Frontend - Production Deployment

**Server IP:** 172.28.69.200  
**Port:** 80 (HTTP)  
**Framework:** React 18 + TypeScript + Vite

## Quick Installation

```bash
sudo ./install.sh
```

## Application Features

### Core Functionality
- **Crop Prediction:** Interactive form with 7 soil/climate parameters
- **Batch Processing:** CSV upload for multiple predictions
- **Results Display:** Confidence scores and alternative recommendations
- **Real-time Validation:** Input validation with range checking

### User Interface
- **Responsive Design:** Works on desktop, tablet, and mobile
- **Modern UI:** Tailwind CSS with shadcn/ui components
- **Accessibility:** WCAG 2.1 AA compliant

### Integration
- **API Communication:** Direct connection to backend (172.28.69.96)
- **Health Monitoring:** Real-time API status indicators
- **Error Handling:** Graceful degradation and user feedback

## API Configuration

The frontend connects to the backend API at:
- **Base URL:** `http://172.28.69.96`
- **Health Check:** `http://172.28.69.96/health`
- **Prediction:** `POST http://172.28.69.96/predict`

## Management

### Updates
```bash
# Automated update
sudo /usr/local/bin/update-crop-frontend
```

### Nginx Management
```bash
sudo systemctl restart nginx
sudo nginx -t  # Test configuration
```

## Testing

```bash
# Test frontend
curl http://172.28.69.200/
curl http://172.28.69.200/health
```
EOF < /dev/null
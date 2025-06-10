# Reporte de Comparación de Modelos
==================================================

## 📊 Resumen Ejecutivo

**Modelo Recomendado:** Conv1DClassifier
**Razón:** Mejor score compuesto (0.919); Accuracy: 0.978; F1-Score: 0.978; Overfitting: Bajo; Fortalezas: Excelente accuracy, Excelente F1-score balanceado, Inferencia rápida, Sin overfitting

## 📈 Tabla Comparativa

| Modelo                |   Accuracy |   F1-Score (Macro) |   F1-Score (Weighted) |   Val Loss |   Tiempo Entrenamiento (s) |   Épocas |   Tiempo/Época (s) |   Tiempo Inferencia (ms) | Overfitting Level   |   Gap Train-Val |   Épocas a Convergencia |   Estabilidad Val |
|:----------------------|-----------:|-------------------:|----------------------:|-----------:|---------------------------:|---------:|-------------------:|-------------------------:|:--------------------|----------------:|------------------------:|------------------:|
| DropClassifier        |     0.9864 |             0.9862 |                0.9864 |     0.0436 |                     2.9961 |      113 |             0.0265 |                   0.026  | Moderado            |          0.0331 |                      29 |            0.0025 |
| DeepDropoutClassifier |     0.9818 |             0.9818 |                0.9818 |     0.0428 |                     6.8659 |      100 |             0.0687 |                   0.1509 | Bajo                |         -0.1625 |                      45 |            0.0035 |
| Conv1DClassifier      |     0.9784 |             0.9782 |                0.9784 |     0.0533 |                    36.8151 |      242 |             0.1521 |                   1.1425 | Bajo                |         -0.0794 |                     nan |            0.0036 |

## 🏆 Ranking de Modelos

### 1. Conv1DClassifier
- **Score:** 0.919
- **Fortalezas:** Excelente accuracy, Excelente F1-score balanceado, Inferencia rápida, Sin overfitting

### 2. DeepDropoutClassifier
- **Score:** 0.914
- **Fortalezas:** Excelente accuracy, Excelente F1-score balanceado, Inferencia muy rápida, Sin overfitting

### 3. DropClassifier
- **Score:** 0.702
- **Fortalezas:** Excelente accuracy, Excelente F1-score balanceado, Inferencia muy rápida, Overfitting mínimo

## 🎯 Mejores Modelos por Criterio

- **Accuracy:** DropClassifier
- **F1 Score:** DropClassifier
- **Inference Speed:** DropClassifier
- **Generalization:** DeepDropoutClassifier

## 💼 Recomendaciones por Caso de Uso

- **Producción (balance accuracy/velocidad):** DropClassifier
- **Investigación (máxima accuracy):** DropClassifier
- **Tiempo real (mínima latencia):** DropClassifier
- **Recursos limitados (eficiencia):** DropClassifier

## 📊 Estadísticas Resumen

- **Accuracy promedio:** 0.982 ± 0.004
- **F1-Score promedio:** 0.982 ± 0.004
- **Tiempo de entrenamiento promedio:** 15.6s
- **Tiempo de inferencia promedio:** 0.44 ms
- **Modelos con bajo overfitting:** 3/3
- **Modelos con alta accuracy (>90%):** 3/3

## 🎯 Conclusiones

1. ✅ **Excelente rendimiento general:** Todos los modelos muestran alta accuracy (>95%)
2. ✅ **Sin problemas de overfitting:** Todos los modelos generalizan bien
3. ⚡ **Excelente eficiencia:** Todos los modelos son rápidos para inferencia
4. 🏆 **Recomendación final:** Conv1DClassifier ofrece el mejor balance general
5.    - Destacado en: Excelente accuracy, Excelente F1-score balanceado, Inferencia rápida, Sin overfitting
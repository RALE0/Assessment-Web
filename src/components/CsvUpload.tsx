
import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, X, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { api, PredictionRequest } from "@/services/api";

interface CsvRow {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
  [key: string]: any;
}

interface CsvUploadProps {
  onPredictionsGenerated: (predictions: any[]) => void;
}

export const CsvUpload = ({ onPredictionsGenerated }: CsvUploadProps) => {
  const [csvData, setCsvData] = useState<CsvRow[]>([]);
  const [fileName, setFileName] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const requiredColumns = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall'];

  const validateCsvData = (data: any[]): { valid: CsvRow[], errors: string[] } => {
    const validRows: CsvRow[] = [];
    const errorMessages: string[] = [];

    data.forEach((row, index) => {
      const missingColumns = requiredColumns.filter(col => 
        row[col] === undefined || row[col] === null || row[col] === ''
      );

      if (missingColumns.length > 0) {
        errorMessages.push(`Fila ${index + 1}: Faltan columnas - ${missingColumns.join(', ')}`);
        return;
      }

      // Validar rangos
      const numericRow: CsvRow = {
        N: Number(row.N),
        P: Number(row.P),
        K: Number(row.K),
        temperature: Number(row.temperature),
        humidity: Number(row.humidity),
        ph: Number(row.ph),
        rainfall: Number(row.rainfall)
      };

      // Validaciones de rango
      if (numericRow.N < 0 || numericRow.N > 140) {
        errorMessages.push(`Fila ${index + 1}: N debe estar entre 0-140`);
      }
      if (numericRow.P < 5 || numericRow.P > 145) {
        errorMessages.push(`Fila ${index + 1}: P debe estar entre 5-145`);
      }
      if (numericRow.K < 5 || numericRow.K > 205) {
        errorMessages.push(`Fila ${index + 1}: K debe estar entre 5-205`);
      }
      if (numericRow.temperature < 8.8 || numericRow.temperature > 43.7) {
        errorMessages.push(`Fila ${index + 1}: Temperatura debe estar entre 8.8-43.7°C`);
      }
      if (numericRow.humidity < 14.3 || numericRow.humidity > 99.9) {
        errorMessages.push(`Fila ${index + 1}: Humedad debe estar entre 14.3-99.9%`);
      }
      if (numericRow.ph < 3.5 || numericRow.ph > 9.9) {
        errorMessages.push(`Fila ${index + 1}: pH debe estar entre 3.5-9.9`);
      }
      if (numericRow.rainfall < 20.2 || numericRow.rainfall > 298.6) {
        errorMessages.push(`Fila ${index + 1}: Lluvia debe estar entre 20.2-298.6mm`);
      }

      if (errorMessages.length === 0 || !errorMessages.some(err => err.includes(`Fila ${index + 1}`))) {
        validRows.push(numericRow);
      }
    });

    return { valid: validRows, errors: errorMessages };
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast({
        title: "Error",
        description: "Por favor selecciona un archivo CSV válido",
        variant: "destructive"
      });
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const lines = text.split('\n').filter(line => line.trim());
        const headers = lines[0].split(',').map(h => h.trim());
        
        // Verificar headers requeridos
        const missingHeaders = requiredColumns.filter(col => !headers.includes(col));
        if (missingHeaders.length > 0) {
          setErrors([`Faltan columnas requeridas: ${missingHeaders.join(', ')}`]);
          return;
        }

        const data = lines.slice(1).map(line => {
          const values = line.split(',');
          const row: any = {};
          headers.forEach((header, index) => {
            row[header] = values[index]?.trim();
          });
          return row;
        });

        const { valid, errors: validationErrors } = validateCsvData(data);
        setCsvData(valid);
        setErrors(validationErrors);

        if (valid.length > 0) {
          toast({
            title: "CSV Cargado",
            description: `${valid.length} filas válidas cargadas ${validationErrors.length > 0 ? `(${validationErrors.length} errores)` : ''}`,
          });
        }
      } catch (error) {
        setErrors(['Error al procesar el archivo CSV']);
        toast({
          title: "Error",
          description: "Error al procesar el archivo CSV",
          variant: "destructive"
        });
      }
    };

    reader.readAsText(file);
  };

  const handleProcessCsv = async () => {
    if (csvData.length === 0) return;

    setIsProcessing(true);
    
    try {
      // Convert CSV data to prediction requests
      const predictionRequests: PredictionRequest[] = csvData.map(row => ({
        N: row.N,
        P: row.P,
        K: row.K,
        temperature: row.temperature,
        humidity: row.humidity,
        ph: row.ph,
        rainfall: row.rainfall
      }));

      // Make batch predictions using the API
      const results = await api.predictBatch(predictionRequests);
      
      // Format results for the UI
      const formattedPredictions = results.map((result, index) => ({
        id: index + 1,
        inputs: predictionRequests[index],
        prediction: result.predicted_crop,
        confidence: Math.round(result.confidence * 100),
        date: result.timestamp,
        topPredictions: result.top_predictions
      }));

      onPredictionsGenerated(formattedPredictions);
      
      toast({
        title: "Predicciones Generadas",
        description: `${formattedPredictions.length} predicciones completadas via API`,
      });
      
    } catch (error) {
      console.error('Batch prediction error:', error);
      toast({
        title: "Error en Predicciones",
        description: error instanceof Error ? error.message : "Error desconocido al procesar las predicciones",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const clearData = () => {
    setCsvData([]);
    setFileName("");
    setErrors([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <Card className="border-blue-100">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Upload className="h-5 w-5 text-blue-600" />
          <span>Carga Masiva por CSV</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="csv-upload">Archivo CSV</Label>
          <Input
            ref={fileInputRef}
            id="csv-upload"
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="cursor-pointer"
          />
          <p className="text-xs text-gray-500">
            Columnas requeridas: N, P, K, temperature, humidity, ph, rainfall
          </p>
        </div>

        {fileName && (
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium">{fileName}</span>
              <Badge variant="outline">{csvData.length} filas válidas</Badge>
            </div>
            <Button variant="ghost" size="sm" onClick={clearData}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {errors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Errores encontrados:</span>
            </div>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {errors.slice(0, 5).map((error, index) => (
                <p key={index} className="text-xs text-red-600 bg-red-50 p-2 rounded">
                  {error}
                </p>
              ))}
              {errors.length > 5 && (
                <p className="text-xs text-gray-500">... y {errors.length - 5} errores más</p>
              )}
            </div>
          </div>
        )}

        {csvData.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Vista previa (primeras 3 filas):</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    {requiredColumns.map(col => (
                      <th key={col} className="p-1 text-left font-medium">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {csvData.slice(0, 3).map((row, index) => (
                    <tr key={index} className="border-b">
                      {requiredColumns.map(col => (
                        <td key={col} className="p-1">{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <Button 
          onClick={handleProcessCsv} 
          disabled={csvData.length === 0 || isProcessing}
          className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
        >
          {isProcessing ? "Procesando..." : `Generar ${csvData.length} Predicciones`}
        </Button>
      </CardContent>
    </Card>
  );
};

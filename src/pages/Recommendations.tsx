import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Leaf, Target, TrendingUp, Upload, MessageCircle, AlertCircle, Wifi, WifiOff } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { CsvUpload } from "@/components/CsvUpload";
import { ChatBot } from "@/components/ChatBot";
import { api, PredictionRequest, PredictionResponse } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";

interface FormData {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

interface Recommendation {
  name: string;
  confidence: number;
  expectedYield: string;
  profitability: string;
  description: string;
  alternatives?: Array<{
    crop: string;
    probability: number;
  }>;
}

const Recommendations = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [csvPredictions, setCsvPredictions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [supportedCrops, setSupportedCrops] = useState<string[]>([]);
  const { user } = useAuth();
  
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<FormData>();

  // Check API status on component mount
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        await api.checkHealth();
        setApiStatus('online');
        
        // Load supported crops
        const cropsResponse = await api.getCrops();
        setSupportedCrops(cropsResponse.crops);
      } catch (error) {
        setApiStatus('offline');
        console.error('API health check failed:', error);
      }
    };

    checkApiStatus();
  }, []);

  const getExpectedYield = (cropName: string): string => {
    const yieldData: { [key: string]: string } = {
      'rice': '6.2 ton/ha',
      'maize': '8.5 ton/ha',
      'cotton': '2.1 ton/ha',
      'wheat': '4.8 ton/ha',
      'chickpea': '2.5 ton/ha',
      'kidneybeans': '3.2 ton/ha',
      'pigeonpeas': '1.8 ton/ha',
      'mothbeans': '1.5 ton/ha',
      'mungbean': '1.2 ton/ha',
      'blackgram': '1.1 ton/ha',
      'lentil': '1.8 ton/ha',
      'pomegranate': '15-20 ton/ha',
      'banana': '25-35 ton/ha',
      'mango': '8-12 ton/ha',
      'grapes': '12-18 ton/ha',
      'watermelon': '20-30 ton/ha',
      'muskmelon': '15-25 ton/ha',
      'apple': '20-25 ton/ha',
      'orange': '15-20 ton/ha',
      'papaya': '40-60 ton/ha',
      'coconut': '80-120 nuts/palm',
      'jute': '2.5-3.5 ton/ha',
      'coffee': '800-1200 kg/ha'
    };
    return yieldData[cropName.toLowerCase()] || '2-4 ton/ha';
  };

  const getProfitability = (confidence: number): string => {
    if (confidence >= 95) return 'Muy Alta';
    if (confidence >= 85) return 'Alta';
    if (confidence >= 75) return 'Media-Alta';
    if (confidence >= 65) return 'Media';
    return 'Baja';
  };

  const getCropDescription = (cropName: string, confidence: number): string => {
    const descriptions: { [key: string]: string } = {
      'rice': 'Excelente adaptación a condiciones de alta humedad y temperatura moderada.',
      'maize': 'Buen potencial de rendimiento con los niveles de NPK disponibles.',
      'cotton': 'Viable con manejo adecuado de irrigación y nutrientes.',
      'wheat': 'Adaptado a condiciones de clima templado con buen drenaje.',
      'chickpea': 'Leguminosa que mejora la fertilidad del suelo.',
      'coffee': 'Requiere condiciones específicas de altitud y clima.',
      'jute': 'Fibra natural que se adapta bien a suelos húmedos.'
    };
    
    const baseDescription = descriptions[cropName.toLowerCase()] || 'Cultivo viable para las condiciones especificadas.';
    const confidenceText = confidence >= 90 ? ' Predicción muy confiable.' : confidence >= 80 ? ' Predicción confiable.' : ' Considere análisis adicional.';
    
    return baseDescription + confidenceText;
  };

  const onSubmit = async (data: FormData) => {
    if (apiStatus === 'offline') {
      toast({
        title: "API No Disponible",
        description: "No se puede conectar con el servidor de predicciones.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    
    try {
      const predictionRequest: PredictionRequest = {
        N: data.N,
        P: data.P,
        K: data.K,
        temperature: data.temperature,
        humidity: data.humidity,
        ph: data.ph,
        rainfall: data.rainfall
      };

      const token = localStorage.getItem('authToken');
      const startTime = Date.now();
      const result: PredictionResponse = await api.predictCrop(predictionRequest, token || undefined);
      const processingTime = Date.now() - startTime;
      
      // Save prediction log if user is authenticated
      if (user) {
        try {
          const token = localStorage.getItem('authToken');
          await api.savePredictionLog({
            userId: user.id,
            inputFeatures: predictionRequest,
            prediction: result,
            processingTime: processingTime
          }, token || undefined);
          console.log('Prediction log saved successfully');
        } catch (logError) {
          console.error('Failed to save prediction log:', logError);
          // Don't show error to user, as the prediction itself was successful
        }
      }
      
      // Convert API response to UI recommendations
      const mainRecommendation: Recommendation = {
        name: result.predicted_crop,
        confidence: Math.round(result.confidence * 100),
        expectedYield: getExpectedYield(result.predicted_crop),
        profitability: getProfitability(result.confidence * 100),
        description: getCropDescription(result.predicted_crop, result.confidence * 100),
        alternatives: result.top_predictions
      };

      // Create additional recommendations from top predictions
      const alternativeRecommendations = result.top_predictions
        .slice(1, 3) // Skip first one as it's the main prediction
        .map(pred => ({
          name: pred.crop,
          confidence: Math.round(pred.probability * 100),
          expectedYield: getExpectedYield(pred.crop),
          profitability: getProfitability(pred.probability * 100),
          description: getCropDescription(pred.crop, pred.probability * 100)
        }));

      setRecommendations([mainRecommendation, ...alternativeRecommendations]);
      
      toast({
        title: "Predicción Generada",
        description: `${result.predicted_crop} recomendado con ${Math.round(result.confidence * 100)}% de confianza`,
      });
      
      if (result.warnings) {
        toast({
          title: "Advertencias",
          description: result.warnings,
          variant: "destructive"
        });
      }
      
    } catch (error) {
      console.error('Prediction error:', error);
      toast({
        title: "Error en Predicción",
        description: error instanceof Error ? error.message : "Error desconocido al procesar la predicción",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCsvPredictions = (predictions: any[]) => {
    setCsvPredictions(predictions);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "bg-green-500";
    if (confidence >= 80) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getProfitabilityColor = (profitability: string) => {
    if (profitability.includes("Muy Alta")) return "text-green-700 bg-green-100";
    if (profitability.includes("Alta")) return "text-emerald-700 bg-emerald-100";
    if (profitability.includes("Media")) return "text-yellow-700 bg-yellow-100";
    return "text-gray-700 bg-gray-100";
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl font-bold text-gray-900">Recomendaciones de Cultivos</h1>
            <div className="flex items-center space-x-2">
              {apiStatus === 'checking' && (
                <div className="flex items-center space-x-2 text-yellow-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
                  <span className="text-sm">Verificando API...</span>
                </div>
              )}
              {apiStatus === 'online' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <Wifi className="h-4 w-4" />
                  <span className="text-sm">API Conectada</span>
                </div>
              )}
              {apiStatus === 'offline' && (
                <div className="flex items-center space-x-2 text-red-600">
                  <WifiOff className="h-4 w-4" />
                  <span className="text-sm">API Desconectada</span>
                </div>
              )}
            </div>
          </div>
          <p className="text-gray-600">
            Obtén recomendaciones personalizadas usando nuestro modelo de IA
          </p>
          {supportedCrops.length > 0 && (
            <p className="text-sm text-gray-500 mt-2">
              Cultivos soportados: {supportedCrops.length} tipos diferentes
            </p>
          )}
        </div>

        <Tabs defaultValue="manual" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="manual" className="flex items-center space-x-2">
              <Leaf className="h-4 w-4" />
              <span>Predicción Manual</span>
            </TabsTrigger>
            <TabsTrigger value="csv" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Carga Masiva CSV</span>
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center space-x-2">
              <MessageCircle className="h-4 w-4" />
              <span>Asistente IA</span>
            </TabsTrigger>
          </TabsList>

          {/* Manual Prediction Tab */}
          <TabsContent value="manual" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Formulario Manual */}
              <Card className="border-green-100">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Leaf className="h-5 w-5 text-green-600" />
                    <span>Parámetros del Cultivo</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="N">Nitrógeno (N)</Label>
                        <Input
                          id="N"
                          type="number"
                          step="0.1"
                          placeholder="0-140"
                          {...register("N", { required: "N es requerido", min: 0, max: 140 })}
                        />
                        {errors.N && <p className="text-xs text-red-600">{errors.N.message}</p>}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="P">Fósforo (P)</Label>
                        <Input
                          id="P"
                          type="number"
                          step="0.1"
                          placeholder="5-145"
                          {...register("P", { required: "P es requerido", min: 5, max: 145 })}
                        />
                        {errors.P && <p className="text-xs text-red-600">{errors.P.message}</p>}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="K">Potasio (K)</Label>
                        <Input
                          id="K"
                          type="number"
                          step="0.1"
                          placeholder="5-205"
                          {...register("K", { required: "K es requerido", min: 5, max: 205 })}
                        />
                        {errors.K && <p className="text-xs text-red-600">{errors.K.message}</p>}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="temperature">Temperatura (°C)</Label>
                        <Input
                          id="temperature"
                          type="number"
                          step="0.1"
                          placeholder="8.8-43.7"
                          {...register("temperature", { required: "Temperatura requerida", min: 8.8, max: 43.7 })}
                        />
                        {errors.temperature && <p className="text-xs text-red-600">{errors.temperature.message}</p>}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="humidity">Humedad (%)</Label>
                        <Input
                          id="humidity"
                          type="number"
                          step="0.1"
                          placeholder="14.3-99.9"
                          {...register("humidity", { required: "Humedad requerida", min: 14.3, max: 99.9 })}
                        />
                        {errors.humidity && <p className="text-xs text-red-600">{errors.humidity.message}</p>}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="ph">pH del Suelo</Label>
                        <Input
                          id="ph"
                          type="number"
                          step="0.1"
                          placeholder="3.5-9.9"
                          {...register("ph", { required: "pH requerido", min: 3.5, max: 9.9 })}
                        />
                        {errors.ph && <p className="text-xs text-red-600">{errors.ph.message}</p>}
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="rainfall">Lluvia (mm)</Label>
                        <Input
                          id="rainfall"
                          type="number"
                          step="0.1"
                          placeholder="20.2-298.6"
                          {...register("rainfall", { required: "Lluvia requerida", min: 20.2, max: 298.6 })}
                        />
                        {errors.rainfall && <p className="text-xs text-red-600">{errors.rainfall.message}</p>}
                      </div>
                    </div>

                    <Button 
                      type="submit" 
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      disabled={isLoading || apiStatus === 'offline'}
                    >
                      {isLoading ? "Analizando..." : apiStatus === 'offline' ? "API No Disponible" : "Generar Predicción IA"}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              {/* Resultados */}
              <div className="space-y-6">
                {isLoading && (
                  <Card className="border-green-100">
                    <CardContent className="p-8 text-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
                      <p className="text-gray-600">Procesando con modelo de IA...</p>
                    </CardContent>
                  </Card>
                )}

                {recommendations.length > 0 && !isLoading && (
                  <>
                    <h3 className="text-xl font-semibold text-gray-900">Cultivos Recomendados</h3>
                    {recommendations.map((rec, index) => (
                      <Card key={index} className="border-green-100 hover:shadow-lg transition-shadow">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-lg">{rec.name}</CardTitle>
                            <div className="flex items-center space-x-2">
                              <div className={`w-2 h-2 rounded-full ${getConfidenceColor(rec.confidence)}`}></div>
                              <span className="text-sm font-medium">{rec.confidence}% confianza</span>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="flex items-center space-x-2">
                              <Target className="h-4 w-4 text-blue-600" />
                              <div>
                                <p className="text-sm text-gray-600">Rendimiento</p>
                                <p className="font-medium">{rec.expectedYield}</p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <TrendingUp className="h-4 w-4 text-green-600" />
                              <div>
                                <p className="text-sm text-gray-600">Rentabilidad</p>
                                <Badge className={getProfitabilityColor(rec.profitability)}>
                                  {rec.profitability}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          <p className="text-gray-700 mb-3">{rec.description}</p>
                          {rec.alternatives && index === 0 && (
                            <div className="border-t pt-3">
                              <p className="text-sm text-gray-600 mb-2">Alternativas detectadas:</p>
                              <div className="flex flex-wrap gap-2">
                                {rec.alternatives.slice(1, 4).map((alt, altIndex) => (
                                  <Badge key={altIndex} variant="outline" className="text-xs">
                                    {alt.crop} ({Math.round(alt.probability * 100)}%)
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </>
                )}

                {recommendations.length === 0 && !isLoading && (
                  <Card className="border-green-100">
                    <CardContent className="p-8 text-center">
                      <Leaf className="h-12 w-12 text-green-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Listo para Analizar
                      </h3>
                      <p className="text-gray-600">
                        Completa los parámetros para obtener una predicción de cultivo
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </TabsContent>

          {/* CSV Upload Tab */}
          <TabsContent value="csv" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <CsvUpload onPredictionsGenerated={handleCsvPredictions} />
              
              {/* CSV Results */}
              <div className="space-y-4">
                {csvPredictions.length > 0 && (
                  <>
                    <h3 className="text-xl font-semibold text-gray-900">
                      Resultados CSV ({csvPredictions.length} predicciones)
                    </h3>
                    <div className="max-h-96 overflow-y-auto space-y-3">
                      {csvPredictions.slice(0, 10).map((pred, index) => (
                        <Card key={pred.id} className="border-blue-100">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium capitalize">{pred.prediction}</h4>
                              <Badge variant="outline">{pred.confidence}% confianza</Badge>
                            </div>
                            <div className="text-xs text-gray-600 grid grid-cols-4 gap-2">
                              <span>N: {pred.inputs.N}</span>
                              <span>P: {pred.inputs.P}</span>
                              <span>K: {pred.inputs.K}</span>
                              <span>T: {pred.inputs.temperature}°C</span>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                      {csvPredictions.length > 10 && (
                        <p className="text-center text-gray-500 text-sm">
                          ... y {csvPredictions.length - 10} predicciones más
                        </p>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Chatbot Tab */}
          <TabsContent value="chat">
            <div className="max-w-4xl mx-auto">
              <ChatBot />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Recommendations;


import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  Legend
} from "recharts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TrendingUp, Target, BarChart3, Clock } from "lucide-react";
import { api } from "@/services/api";
import { toast } from "@/hooks/use-toast";

interface ResponseTimeData {
  timestamp: string;
  responseTime: number;
}

interface UserPrediction {
  date: string;
  user: string;
  recommendedCrop: string;
  confidence: number;
}

interface ModelMetric {
  name: string;
  value: number;
  target: number;
  status: "excellent" | "good" | "warning" | "poor";
}

interface PerformanceMetrics {
  average_response_time: number;
  p95_response_time: number;
  p99_response_time: number;
  timestamp: string;
}

const Analytics = () => {
  const [responseTimeData, setResponseTimeData] = useState<ResponseTimeData[]>([]);
  const [userPredictions, setUserPredictions] = useState<UserPrediction[]>([]);
  const [modelMetrics, setModelMetrics] = useState<ModelMetric[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    average_response_time: 0,
    p95_response_time: 0,
    p99_response_time: 0,
    timestamp: ""
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
    
    // Auto-refresh every 30 seconds
    const refreshInterval = setInterval(() => {
      fetchAnalyticsData();
    }, 30000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  const fetchAnalyticsData = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken'); // Fixed: use 'authToken' instead of 'token'
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Fetch all analytics data in parallel
      const [
        responseTimeResponse,
        userPredictionsResponse, 
        metricsResponse,
        performanceResponse
      ] = await Promise.all([
        api.getResponseTimeData(token),
        api.getUserPredictions(token),
        api.getModelMetrics(token),
        api.getPerformanceMetrics(token)
      ]);

      // Process and set the real data
      setResponseTimeData(responseTimeResponse.data || []);
      setUserPredictions(userPredictionsResponse.predictions || []);
      setModelMetrics(metricsResponse.metrics || []);
      setPerformanceMetrics({
        average_response_time: performanceResponse.average_response_time || 0,
        p95_response_time: performanceResponse.p95_response_time || 0,
        p99_response_time: performanceResponse.p99_response_time || 0,
        timestamp: performanceResponse.timestamp || new Date().toISOString()
      });

    } catch (error) {
      console.error('Error fetching analytics data:', error);
      toast({
        title: "Error de Conexión",
        description: "No se pudo conectar con el servidor. Los datos no están disponibles.",
        variant: "destructive"
      });
      
      // Keep empty states - no fallback mock data
      setResponseTimeData([]);
      setUserPredictions([]);
      setModelMetrics([]);
      setPerformanceMetrics({
        average_response_time: 0,
        p95_response_time: 0,
        p99_response_time: 0,
        timestamp: ""
      });
    } finally {
      setIsLoading(false);
    }
  };
  const getStatusColor = (status: string) => {
    switch (status) {
      case "excellent": return "text-green-700 bg-green-100";
      case "good": return "text-blue-700 bg-blue-100";
      case "warning": return "text-yellow-700 bg-yellow-100";
      default: return "text-gray-700 bg-gray-100";
    }
  };

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analítica</h1>
          <p className="text-gray-600">
            Análisis detallado del rendimiento y métricas del modelo de IA
          </p>
        </div>

        {/* Model Performance Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {modelMetrics.map((metric, index) => (
            <Card key={index} className="border-green-100 hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {metric.name}
                </CardTitle>
                <Target className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900 mb-2">
                  {isLoading ? "..." : metric.value > 0 ? `${metric.value}%` : "N/A"}
                </div>
                {metric.value > 0 ? (
                  <>
                    <Progress value={metric.value} className="mb-2" />
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Meta: {metric.target}%</span>
                      <Badge className={getStatusColor(metric.status)}>
                        {metric.status === "excellent" ? "Excelente" : "Bueno"}
                      </Badge>
                    </div>
                  </>
                ) : (
                  <div className="text-sm text-gray-500">
                    Datos no disponibles
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Response Time Chart */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Tiempo de Respuesta</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : responseTimeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={responseTimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="timestamp" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => [`${value}s`, 'Tiempo']}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="responseTime" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    name="Tiempo de Respuesta (s)"
                  />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="text-gray-500 text-center">
                    <p className="text-lg mb-2">Datos no disponibles</p>
                    <p className="text-sm">No se pudieron cargar los datos del servidor</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* User Predicted Metrics Table */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                <span>Métricas de Predicción de Usuarios</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : userPredictions.length > 0 ? (
                <div className="h-[300px] overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Cultivo Recomendado</TableHead>
                        <TableHead>Confianza</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {userPredictions.slice(0, 10).map((prediction, index) => (
                        <TableRow key={index}>
                          <TableCell>{prediction.date}</TableCell>
                          <TableCell>{prediction.user}</TableCell>
                          <TableCell>{prediction.recommendedCrop}</TableCell>
                          <TableCell>
                            <span className={`font-medium ${
                              prediction.confidence >= 90 ? 'text-green-600' : 
                              prediction.confidence >= 70 ? 'text-yellow-600' : 
                              'text-red-600'
                            }`}>
                              {prediction.confidence}%
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="text-gray-500 text-center">
                    <p className="text-lg mb-2">Datos no disponibles</p>
                    <p className="text-sm">No se pudieron cargar los datos del servidor</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Performance Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Average Response Time Card */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-purple-600" />
                <span>Tiempo Promedio</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : performanceMetrics.average_response_time > 0 ? `${performanceMetrics.average_response_time}s` : "N/A"}
              </div>
              <p className="text-sm text-gray-600">Tiempo de respuesta promedio</p>
            </CardContent>
          </Card>

          {/* P95 Response Time Card */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-blue-600" />
                <span>Tiempo de respuesta (95%)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : performanceMetrics.p95_response_time > 0 ? `${performanceMetrics.p95_response_time}s` : "N/A"}
              </div>
              <p className="text-sm text-gray-600">Percentil 95 del tiempo de respuesta</p>
            </CardContent>
          </Card>

          {/* P99 Response Time Card */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-orange-600" />
                <span>Tiempo de respuesta (99%)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : performanceMetrics.p99_response_time > 0 ? `${performanceMetrics.p99_response_time}s` : "N/A"}
              </div>
              <p className="text-sm text-gray-600">Percentil 99 del tiempo de respuesta</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Analytics;

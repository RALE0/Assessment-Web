
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
  PieChart,
  Pie,
  Cell
} from "recharts";
import { TrendingUp, Target, BarChart3, Users } from "lucide-react";
import { api } from "@/services/api";
import { toast } from "@/hooks/use-toast";

interface AccuracyData {
  month: string;
  accuracy: number;
}

interface RegionData {
  name: string;
  value: number;
  color: string;
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
  user_satisfaction_score: number;
  total_reviews: number;
  positive_percentage: number;
  average_roi_increase: number;
  vs_traditional_farming: string;
  last_harvest_date: string;
}

const Analytics = () => {
  const [accuracyData, setAccuracyData] = useState<AccuracyData[]>([]);
  const [regionData, setRegionData] = useState<RegionData[]>([]);
  const [modelMetrics, setModelMetrics] = useState<ModelMetric[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics>({
    average_response_time: 0,
    p95_response_time: 0,
    p99_response_time: 0,
    user_satisfaction_score: 0,
    total_reviews: 0,
    positive_percentage: 0,
    average_roi_increase: 0,
    vs_traditional_farming: "",
    last_harvest_date: ""
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    setIsLoading(true);
    try {
      // Fetch accuracy trend data
      const accuracyResponse = await api.getAccuracyTrend();
      setAccuracyData(accuracyResponse.data);

      // Fetch regional distribution
      const regionResponse = await api.getRegionalDistribution();
      setRegionData(regionResponse.data);

      // Fetch model metrics
      const metricsResponse = await api.getModelMetrics();
      setModelMetrics(metricsResponse.metrics);

      // Fetch performance metrics
      const performanceResponse = await api.getPerformanceMetrics();
      setPerformanceMetrics(performanceResponse);

    } catch (error) {
      console.error('Error fetching analytics data:', error);
      toast({
        title: "Error",
        description: "No se pudieron cargar los datos de analytics",
        variant: "destructive"
      });
      // Use default data if API fails
      setAccuracyData([
        { month: "Ene", accuracy: 94.2 },
        { month: "Feb", accuracy: 95.1 },
        { month: "Mar", accuracy: 96.3 },
        { month: "Abr", accuracy: 97.1 },
        { month: "May", accuracy: 97.8 },
        { month: "Jun", accuracy: 97.8 },
      ]);
      setRegionData([
        { name: "Centro México", value: 35, color: "#10b981" },
        { name: "Sur México", value: 25, color: "#059669" },
        { name: "Norte México", value: 20, color: "#047857" },
        { name: "Colombia", value: 12, color: "#065f46" },
        { name: "Otros", value: 8, color: "#064e3b" },
      ]);
      setModelMetrics([
        { name: "Precisión General", value: 97.8, target: 95, status: "excellent" },
        { name: "Recall", value: 94.2, target: 90, status: "good" },
        { name: "F1-Score", value: 95.9, target: 92, status: "excellent" },
        { name: "Especificidad", value: 96.4, target: 93, status: "excellent" },
      ]);
      setPerformanceMetrics({
        average_response_time: 1.2,
        p95_response_time: 2.1,
        p99_response_time: 3.4,
        user_satisfaction_score: 4.8,
        total_reviews: 2847,
        positive_percentage: 96,
        average_roi_increase: 23,
        vs_traditional_farming: "vs cultivos tradicionales",
        last_harvest_date: "Última cosecha"
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics</h1>
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
                  {isLoading ? "..." : `${metric.value}%`}
                </div>
                <Progress value={metric.value} className="mb-2" />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Meta: {metric.target}%</span>
                  <Badge className={getStatusColor(metric.status)}>
                    {metric.status === "excellent" ? "Excelente" : "Bueno"}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Accuracy Trend */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>Evolución de Precisión del Modelo</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={accuracyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis domain={[90, 100]} stroke="#6b7280" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }}
                    formatter={(value) => [`${value}%`, 'Precisión']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="accuracy" 
                    stroke="#10b981" 
                    fill="url(#colorAccuracy)"
                    strokeWidth={2}
                  />
                  <defs>
                    <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Regional Distribution */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5 text-blue-600" />
                <span>Distribución por Región</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                  <Pie
                    data={regionData}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {regionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Porcentaje']}
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }}
                  />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Additional Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5 text-purple-600" />
                <span>Tiempo de Respuesta</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : `${performanceMetrics.average_response_time}s`}
              </div>
              <p className="text-sm text-gray-600">Promedio por consulta</p>
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>P95: {performanceMetrics.p95_response_time}s</span>
                  <span>P99: {performanceMetrics.p99_response_time}s</span>
                </div>
                <Progress value={85} className="h-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-orange-600" />
                <span>Satisfacción Usuario</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : `${performanceMetrics.user_satisfaction_score}/5`}
              </div>
              <p className="text-sm text-gray-600">Calificación promedio</p>
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{performanceMetrics.total_reviews.toLocaleString()} reseñas</span>
                  <span>{performanceMetrics.positive_percentage}% positivas</span>
                </div>
                <Progress value={performanceMetrics.positive_percentage} className="h-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <span>ROI Promedio</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 mb-2">
                {isLoading ? "..." : `+${performanceMetrics.average_roi_increase}%`}
              </div>
              <p className="text-sm text-gray-600">Incremento en rendimiento</p>
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{performanceMetrics.vs_traditional_farming}</span>
                  <span>{performanceMetrics.last_harvest_date}</span>
                </div>
                <Progress value={78} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Analytics;

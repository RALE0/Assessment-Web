
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { TrendingUp, Users, Target, Leaf } from "lucide-react";
import { api } from "@/services/api";
import { toast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

interface DashboardMetrics {
  predictions_generated: number;
  predictions_change: number;
  model_accuracy: number;
  accuracy_change: number;
  crops_analyzed: number;
  new_crops: number;
  active_users: number;
  users_change: number;
}

interface MonthlyPrediction {
  month: string;
  predictions: number;
}

interface CropDistribution {
  crop: string;
  count: number;
  color: string;
}

const Dashboard = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    predictions_generated: 0,
    predictions_change: 0,
    model_accuracy: 0,
    accuracy_change: 0,
    crops_analyzed: 0,
    new_crops: 0,
    active_users: 0,
    users_change: 0
  });
  const [monthlyPredictions, setMonthlyPredictions] = useState<MonthlyPrediction[]>([]);
  const [cropDistribution, setCropDistribution] = useState<CropDistribution[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      
      // Fetch user-specific dashboard metrics
      const metricsResponse = await api.getUserDashboardMetrics(user?.id, token);
      setMetrics(metricsResponse);

      // Fetch user-specific monthly predictions data
      const monthlyResponse = await api.getUserMonthlyPredictions(user?.id, token);
      setMonthlyPredictions(monthlyResponse.data);

      // Fetch user-specific crop distribution data
      const cropResponse = await api.getUserCropDistribution(user?.id, token);
      setCropDistribution(cropResponse.data);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        title: "Error",
        description: "No se pudieron cargar los datos del dashboard",
        variant: "destructive"
      });
      // Use empty data if API fails - metrics will populate as user makes predictions
      setMetrics({
        predictions_generated: 0,
        predictions_change: 0,
        model_accuracy: 0,
        accuracy_change: 0,
        crops_analyzed: 0,
        new_crops: 0,
        active_users: 0,
        users_change: 0
      });
      setMonthlyPredictions([]);
      setCropDistribution([]);
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Métricas y análisis de la plataforma AgriAI</p>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="border-green-100 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Predicciones Generadas
              </CardTitle>
              <Target className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? "..." : metrics.predictions_generated?.toLocaleString() || "0"}
              </div>
              <p className="text-xs text-green-600">
                {(metrics.predictions_change || 0) > 0 ? "+" : ""}{metrics.predictions_change || 0}% vs mes anterior
              </p>
            </CardContent>
          </Card>

          <Card className="border-green-100 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Precisión del Modelo
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? "..." : `${metrics.model_accuracy || 0}%`}
              </div>
              <p className="text-xs text-blue-600">
                {(metrics.accuracy_change || 0) > 0 ? "+" : ""}{metrics.accuracy_change || 0}% vs trimestre anterior
              </p>
            </CardContent>
          </Card>

          <Card className="border-green-100 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Cultivos Analizados
              </CardTitle>
              <Leaf className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? "..." : metrics.crops_analyzed || 0}
              </div>
              <p className="text-xs text-emerald-600">
                +{metrics.new_crops || 0} nuevos cultivos
              </p>
            </CardContent>
          </Card>

          <Card className="border-green-100 hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Usuarios Activos
              </CardTitle>
              <Users className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {isLoading ? "..." : metrics.active_users?.toLocaleString() || "0"}
              </div>
              <p className="text-xs text-purple-600">
                {(metrics.users_change || 0) > 0 ? "+" : ""}{metrics.users_change || 0}% vs mes anterior
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Line Chart */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Predicciones Mensuales
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={monthlyPredictions}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="predictions" 
                    stroke="#10b981" 
                    strokeWidth={3}
                    dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                  />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Bar Chart */}
          <Card className="border-green-100">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-gray-900">
                Distribución de Cultivos Recomendados
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="h-[300px] flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={cropDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="crop" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #d1d5db',
                      borderRadius: '8px'
                    }} 
                  />
                  <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

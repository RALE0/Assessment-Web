import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Filter, Calendar, Download, ChevronLeft, ChevronRight, History as HistoryIcon, TrendingUp, BarChart3 } from "lucide-react";
import { api } from "@/services/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";

interface PredictionLog {
  id: string;
  userId: string;
  timestamp: string;
  inputFeatures: {
    N: number;
    P: number;
    K: number;
    temperature: number;
    humidity: number;
    ph: number;
    rainfall: number;
  };
  predictedCrop: string;
  confidence: number;
  topPredictions: {
    crop: string;
    probability: number;
  }[];
  status: 'success' | 'error';
  processingTime?: number;
}

interface LogFilters {
  dateFrom: string;
  dateTo: string;
  crop: string;
  status: string;
  search: string;
}

const History = () => {
  const { user } = useAuth();
  const [logs, setLogs] = useState<PredictionLog[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<PredictionLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const logsPerPage = 10;

  const [filters, setFilters] = useState<LogFilters>({
    dateFrom: '',
    dateTo: '',
    crop: 'all',
    status: 'all',
    search: ''
  });

  const [availableCrops, setAvailableCrops] = useState<string[]>([]);

  useEffect(() => {
    if (user) {
      fetchUserLogs();
      fetchAvailableCrops();
    }
  }, [user]);

  useEffect(() => {
    applyFilters();
  }, [logs, filters]);

  useEffect(() => {
    const startIndex = (currentPage - 1) * logsPerPage;
    const endIndex = startIndex + logsPerPage;
    setTotalPages(Math.ceil(filteredLogs.length / logsPerPage));
  }, [filteredLogs, currentPage]);

  const fetchUserLogs = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      const userLogs = await api.getUserPredictionLogs(user.id, token || undefined);
      
      // Transform the backend response to match the frontend interface
      const transformedLogs = userLogs.map((log: any) => ({
        id: log.id,
        userId: log.userId,
        timestamp: log.timestamp,
        inputFeatures: {
          N: log.inputFeatures.N,
          P: log.inputFeatures.P,
          K: log.inputFeatures.K,
          temperature: log.inputFeatures.temperature,
          humidity: log.inputFeatures.humidity,
          ph: log.inputFeatures.ph,
          rainfall: log.inputFeatures.rainfall
        },
        predictedCrop: log.predictedCrop,
        confidence: log.confidence,
        topPredictions: log.topPredictions || [],
        status: log.status || 'success',
        processingTime: log.processingTime
      }));
      
      setLogs(transformedLogs || []);
    } catch (error: any) {
      console.error('Error fetching user logs:', error);
      
      // More specific error messages based on the error type
      if (error.message?.includes('404') || error.message?.includes('not found')) {
        toast({
          title: "Historial no disponible",
          description: "El servicio de historial aún no está implementado en el servidor. Por favor, contacta al administrador.",
          variant: "destructive"
        });
      } else if (error.message?.includes('401') || error.message?.includes('unauthorized')) {
        toast({
          title: "No autorizado",
          description: "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.",
          variant: "destructive"
        });
      } else {
        toast({
          title: "Error del servidor",
          description: "No se pudo cargar el historial. Intenta de nuevo más tarde.",
          variant: "destructive"
        });
      }
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableCrops = async () => {
    try {
      const cropsResponse = await api.getCrops();
      setAvailableCrops(cropsResponse.crops);
    } catch (error) {
      console.error('Error fetching crops:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...logs];

    // Date range filter
    if (filters.dateFrom) {
      filtered = filtered.filter(log => 
        new Date(log.timestamp) >= new Date(filters.dateFrom)
      );
    }
    if (filters.dateTo) {
      filtered = filtered.filter(log => 
        new Date(log.timestamp) <= new Date(filters.dateTo)
      );
    }

    // Crop filter
    if (filters.crop && filters.crop !== 'all') {
      filtered = filtered.filter(log => 
        log.predictedCrop.toLowerCase().includes(filters.crop.toLowerCase())
      );
    }

    // Status filter
    if (filters.status && filters.status !== 'all') {
      filtered = filtered.filter(log => log.status === filters.status);
    }

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(log => 
        log.predictedCrop.toLowerCase().includes(searchTerm) ||
        log.id.toLowerCase().includes(searchTerm)
      );
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    setFilteredLogs(filtered);
    setCurrentPage(1);
  };

  const exportLogs = () => {
    const csvData = filteredLogs.map(log => ({
      'Fecha': new Date(log.timestamp).toLocaleString('es-ES'),
      'Cultivo Predicho': log.predictedCrop,
      'Confianza': `${(log.confidence * 100).toFixed(1)}%`,
      'N': log.inputFeatures.N,
      'P': log.inputFeatures.P,
      'K': log.inputFeatures.K,
      'Temperatura': log.inputFeatures.temperature,
      'Humedad': log.inputFeatures.humidity,
      'pH': log.inputFeatures.ph,
      'Precipitación': log.inputFeatures.rainfall,
      'Estado': log.status,
      'Tiempo de Procesamiento': log.processingTime ? `${log.processingTime}ms` : 'N/A'
    }));

    const csvContent = [
      Object.keys(csvData[0]).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predicciones_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCurrentPageLogs = () => {
    const startIndex = (currentPage - 1) * logsPerPage;
    const endIndex = startIndex + logsPerPage;
    return filteredLogs.slice(startIndex, endIndex);
  };

  if (!user) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Card className="w-96">
          <CardContent className="pt-6">
            <p className="text-center text-gray-600">
              Debes iniciar sesión para ver tu historial de predicciones
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Historial de Predicciones</h1>
            <p className="text-gray-600">Consulta y analiza tu historial de predicciones de cultivos</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card className="border-green-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Predicciones</p>
                    <p className="text-3xl font-bold text-green-600">{logs.length}</p>
                  </div>
                  <div className="bg-green-100 p-3 rounded-full">
                    <BarChart3 className="h-6 w-6 text-green-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-blue-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Predicciones Exitosas</p>
                    <p className="text-3xl font-bold text-blue-600">
                      {logs.filter(log => log.status === 'success').length}
                    </p>
                  </div>
                  <div className="bg-blue-100 p-3 rounded-full">
                    <TrendingUp className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-purple-200">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Tasa de Éxito</p>
                    <p className="text-3xl font-bold text-purple-600">
                      {logs.length > 0 ? Math.round((logs.filter(log => log.status === 'success').length / logs.length) * 100) : 0}%
                    </p>
                  </div>
                  <div className="bg-purple-100 p-3 rounded-full">
                    <Calendar className="h-6 w-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filtros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Buscar
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="ID, cultivo..."
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Desde
                </label>
                <Input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Hasta
                </label>
                <Input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Cultivo
                </label>
                <Select value={filters.crop} onValueChange={(value) => setFilters(prev => ({ ...prev, crop: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todos los cultivos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos los cultivos</SelectItem>
                    {availableCrops.map(crop => (
                      <SelectItem key={crop} value={crop}>{crop}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex flex-wrap gap-4 items-center">
              <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos los estados</SelectItem>
                  <SelectItem value="success">Exitoso</SelectItem>
                  <SelectItem value="error">Error</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                onClick={() => setFilters({
                  dateFrom: '',
                  dateTo: '',
                  crop: 'all',
                  status: 'all',
                  search: ''
                })}
              >
                Limpiar Filtros
              </Button>

              <Button
                variant="outline"
                onClick={exportLogs}
                disabled={filteredLogs.length === 0}
                className="ml-auto"
              >
                <Download className="h-4 w-4 mr-2" />
                Exportar CSV
              </Button>
            </div>
          </CardContent>
        </Card>

          {/* Results Summary */}
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Mostrando {getCurrentPageLogs().length} de {filteredLogs.length} predicciones
              {logs.length !== filteredLogs.length && ` (filtrado de ${logs.length} total)`}
            </p>
          </div>

          {/* Logs Table */}
          <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="h-96 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
              </div>
            ) : filteredLogs.length === 0 ? (
              <div className="h-96 flex items-center justify-center">
                <div className="text-center">
                  <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No se encontraron predicciones</p>
                  <p className="text-sm text-gray-400">Intenta ajustar los filtros o realiza una nueva predicción</p>
                </div>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Cultivo Predicho</TableHead>
                      <TableHead>Confianza</TableHead>
                      <TableHead>Parámetros</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead>Tiempo</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {getCurrentPageLogs().map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="font-medium">
                          {formatDate(log.timestamp)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{log.predictedCrop}</span>
                            {log.topPredictions.length > 1 && (
                              <Badge variant="secondary" className="text-xs">
                                +{log.topPredictions.length - 1} más
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={log.confidence > 0.8 ? "default" : log.confidence > 0.6 ? "secondary" : "outline"}
                          >
                            {(log.confidence * 100).toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="text-sm text-gray-600">
                            N:{log.inputFeatures.N} P:{log.inputFeatures.P} K:{log.inputFeatures.K}
                            <br />
                            T:{log.inputFeatures.temperature}° H:{log.inputFeatures.humidity}% pH:{log.inputFeatures.ph}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={log.status === 'success' ? 'default' : 'destructive'}>
                            {log.status === 'success' ? 'Exitoso' : 'Error'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {log.processingTime ? `${log.processingTime}ms` : 'N/A'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between p-4 border-t">
                    <div className="text-sm text-gray-600">
                      Página {currentPage} de {totalPages}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
          </Card>
        </div>
    </div>
  );
};

export default History;
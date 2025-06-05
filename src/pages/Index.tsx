
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Leaf, TrendingUp, Cpu, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Plataforma de{" "}
              <span className="bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                AI para Agricultura
              </span>{" "}
              Inteligente
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
              Revoluciona tu producción agrícola con nuestro sistema de inteligencia artificial 
              que analiza suelo, clima y condiciones regionales para recomendar los cultivos más rentables.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                asChild 
                size="lg" 
                className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-8 py-3 text-lg"
              >
                <Link to="/recommendations">
                  Obtener Recomendación
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button 
                asChild 
                variant="outline" 
                size="lg"
                className="border-green-600 text-green-600 hover:bg-green-50 px-8 py-3 text-lg"
              >
                <Link to="/dashboard">Ver Demo</Link>
              </Button>
            </div>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-20">
            <Card className="group hover:shadow-xl transition-all duration-300 border-green-100 hover:border-green-200">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Leaf className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Análisis de Suelo</h3>
                <p className="text-gray-600">
                  Evaluación inteligente de la composición del suelo para determinar 
                  los nutrientes disponibles y las necesidades específicas.
                </p>
              </CardContent>
            </Card>

            <Card className="group hover:shadow-xl transition-all duration-300 border-green-100 hover:border-green-200">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                  <TrendingUp className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">Predicción Climática</h3>
                <p className="text-gray-600">
                  Análisis avanzado de patrones climáticos y estacionales para 
                  optimizar los tiempos de siembra y cosecha.
                </p>
              </CardContent>
            </Card>

            <Card className="group hover:shadow-xl transition-all duration-300 border-green-100 hover:border-green-200">
              <CardContent className="p-8 text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                  <Cpu className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">IA Avanzada</h3>
                <p className="text-gray-600">
                  Algoritmos de machine learning entrenados con cientos de datos 
                  agrícolas para precisión superior al 95%.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* CTA Section */}
          <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-8 md:p-12 text-center text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              ¿Listo para revolucionar tu agricultura?
            </h2>
            <p className="text-xl text-green-100 mb-8 max-w-2xl mx-auto">
              Únete a los agricultores que ya están optimizando sus cultivos con AgriAI.
            </p>
            <Button 
              asChild 
              size="lg" 
              className="bg-white text-green-600 hover:bg-gray-100 px-8 py-3 text-lg"
            >
              <Link to="/recommendations">
                Comenzar Ahora
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Index;

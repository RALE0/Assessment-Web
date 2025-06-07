
import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Upload, Send, Leaf } from "lucide-react";
import { api } from "@/services/api";
import { toast } from "@/hooks/use-toast";

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  suggestions?: string[];
}

export const ChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: '¡Hola! Soy tu asistente agrícola con IA. Puedo ayudarte con recomendaciones de cultivos, análisis de suelo, clima y mucho más. ¿En qué puedo ayudarte hoy?',
      timestamp: new Date(),
      suggestions: [
        '¿Qué cultivo me recomiendas?',
        'Analiza mi suelo',
        '¿Cuál es el mejor momento para sembrar?',
        'Problemas con plagas'
      ]
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");
    setIsTyping(true);

    try {
      // Send message to backend API
      const response = await api.sendChatMessage(message, conversationId);
      
      // Update conversation ID if this is the first message
      if (!conversationId && response.conversationId) {
        setConversationId(response.conversationId);
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.response,
        timestamp: new Date(),
        suggestions: response.suggestions
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback to local response if API fails
      const botResponse = generateBotResponse(message);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: botResponse.content,
        timestamp: new Date(),
        suggestions: botResponse.suggestions
      };

      setMessages(prev => [...prev, botMessage]);
      
      toast({
        title: "Advertencia",
        description: "Usando respuestas offline. La conexión con el servidor no está disponible.",
        variant: "destructive"
      });
    } finally {
      setIsTyping(false);
    }
  };

  const generateBotResponse = (userMessage: string): { content: string, suggestions?: string[] } => {
    const lowerMessage = userMessage.toLowerCase();

    if (lowerMessage.includes('cultivo') || lowerMessage.includes('recomienda')) {
      return {
        content: 'Para darte la mejor recomendación, necesito conocer algunos datos de tu terreno. ¿Podrías decirme qué tipo de suelo tienes (arcilloso, arenoso, limoso), tu ubicación y la temporada de siembra?',
        suggestions: [
          'Tengo suelo arcilloso en México',
          'Suelo arenoso, temporada seca',
          'Necesito más información sobre tipos de suelo'
        ]
      };
    }

    if (lowerMessage.includes('suelo')) {
      return {
        content: 'El análisis de suelo es fundamental. Los principales tipos son:\n\n🟤 **Arcilloso**: Retiene agua, rico en nutrientes\n🟡 **Arenoso**: Buen drenaje, requiere más riego\n🟫 **Limoso**: Equilibrado, ideal para muchos cultivos\n\n¿Qué tipo de suelo tienes o necesitas más información sobre alguno específico?',
        suggestions: [
          'Tengo suelo arcilloso',
          'Mi suelo es arenoso',
          '¿Cómo identifico mi tipo de suelo?'
        ]
      };
    }

    if (lowerMessage.includes('clima') || lowerMessage.includes('temporada') || lowerMessage.includes('sembrar')) {
      return {
        content: 'El timing es crucial en agricultura. Las temporadas principales son:\n\n🌧️ **Temporada de lluvia**: Ideal para cultivos que requieren mucha agua\n☀️ **Temporada seca**: Mejor para cultivos resistentes a sequía\n\n¿En qué temporada planeas sembrar y en qué región te encuentras?',
        suggestions: [
          'Temporada de lluvia en Colombia',
          'Temporada seca en México',
          '¿Cuál es la mejor época para maíz?'
        ]
      };
    }

    if (lowerMessage.includes('plaga') || lowerMessage.includes('enfermedad')) {
      return {
        content: 'Las plagas son un desafío común. Para ayudarte mejor, ¿podrías describir:\n\n🐛 ¿Qué síntomas observas en las plantas?\n🌱 ¿Qué cultivo está afectado?\n📍 ¿En qué etapa de crecimiento están?\n\nMientras tanto, te recomiendo inspección regular y métodos de control integrado.',
        suggestions: [
          'Hojas amarillas en tomate',
          'Insectos en maíz joven',
          'Manchas en hojas de frijol'
        ]
      };
    }

    // Respuesta por defecto
    return {
      content: 'Entiendo tu consulta. Puedo ayudarte con recomendaciones de cultivos, análisis de suelo, timing de siembra, manejo de plagas y optimización de rendimientos. ¿Podrías ser más específico sobre lo que necesitas?',
      suggestions: [
        '¿Qué cultivo me recomiendas?',
        'Análisis de mi suelo',
        'Problemas con plagas',
        'Mejor época de siembra'
      ]
    };
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  return (
    <Card className="border-purple-100 h-[500px] flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center space-x-2">
          <MessageCircle className="h-5 w-5 text-purple-600" />
          <span>Asistente Agrícola IA</span>
          <Badge variant="outline" className="text-xs">Online</Badge>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-4 min-h-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg p-3 break-words overflow-hidden ${
                message.type === 'user' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                <p className="text-sm whitespace-pre-line break-words">{message.content}</p>
                <p className="text-xs mt-1 opacity-70">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {/* Suggestions */}
          {messages.length > 0 && messages[messages.length - 1].type === 'bot' && messages[messages.length - 1].suggestions && (
            <div className="flex flex-wrap gap-2 mt-2">
              {messages[messages.length - 1].suggestions!.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs h-7 px-2 border-purple-200 hover:border-purple-400"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          )}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="flex space-x-2 flex-shrink-0">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Escribe tu pregunta sobre agricultura..."
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(inputMessage)}
            className="flex-1"
          />
          <Button 
            onClick={() => handleSendMessage(inputMessage)}
            disabled={!inputMessage.trim() || isTyping}
            size="icon"
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

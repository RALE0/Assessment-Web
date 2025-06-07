from flask import Blueprint, jsonify, request
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import uuid
import json
from auth_utils import require_auth_optional, get_client_info
from dashboard_endpoints import get_db_connection, log_api_request

logger = logging.getLogger(__name__)

# Create Blueprint
chat_bp = Blueprint('chat', __name__)

# Simple AI response generator for crop recommendations
class CropChatBot:
    def __init__(self):
        self.crop_knowledge = {
            "maiz": {
                "conditions": "Suelo franco, pH 6.0-7.0, temperatura 15-30°C",
                "season": "Primavera-verano",
                "care": "Riego regular, fertilización rica en nitrógeno"
            },
            "frijol": {
                "conditions": "Suelo bien drenado, pH 6.0-7.5, temperatura 18-25°C",
                "season": "Primavera",
                "care": "Riego moderado, no requiere mucho fertilizante"
            },
            "arroz": {
                "conditions": "Suelo arcilloso, pH 5.5-6.5, abundante agua",
                "season": "Todo el año en clima tropical",
                "care": "Inundación controlada, fertilización balanceada"
            },
            "cafe": {
                "conditions": "Suelo volcánico, pH 6.0-6.5, altitud 1000-2000m",
                "season": "Todo el año",
                "care": "Sombra parcial, riego constante, fertilización orgánica"
            },
            "tomate": {
                "conditions": "Suelo franco, pH 6.0-6.8, temperatura 18-25°C",
                "season": "Primavera-verano",
                "care": "Riego regular, soporte para plantas, fertilización balanceada"
            }
        }
        
        self.common_responses = {
            "greeting": [
                "¡Hola! Soy tu asistente agrícola inteligente. ¿En qué puedo ayudarte hoy?",
                "¡Bienvenido! Estoy aquí para ayudarte con recomendaciones de cultivos. ¿Qué necesitas saber?",
                "¡Saludos! ¿Te gustaría obtener recomendaciones sobre qué cultivo es mejor para tu terreno?"
            ],
            "soil_questions": [
                "Para darte la mejor recomendación, necesito conocer algunos datos de tu terreno:",
                "Cuéntame sobre tu suelo y ubicación para poder ayudarte mejor:",
                "¿Podrías proporcionarme información sobre las condiciones de tu terreno?"
            ],
            "recommendations": [
                "Basado en las condiciones que describes, te recomiendo:",
                "Para tu tipo de suelo y clima, los mejores cultivos serían:",
                "Considerando tus condiciones, estas son mis recomendaciones:"
            ]
        }
        
        self.suggestions = [
            "Tengo suelo arcilloso en México",
            "Suelo arenoso, temporada seca",
            "Necesito más información sobre tipos de suelo",
            "¿Qué cultivo es más rentable?",
            "¿Cuándo debo plantar?",
            "¿Qué fertilizantes necesito?"
        ]

    def generate_response(self, message, conversation_history=None):
        """Generate AI response based on user message."""
        message_lower = message.lower()
        
        # Detect intent
        if any(word in message_lower for word in ["hola", "buenos", "saludos", "hi", "hello"]):
            response = self.common_responses["greeting"][0]
            topic = "greeting"
            confidence = 0.95
        elif any(word in message_lower for word in ["suelo", "terreno", "tierra", "soil"]):
            response = self._handle_soil_question(message_lower)
            topic = "soil_analysis"
            confidence = 0.90
        elif any(word in message_lower for word in ["recomiendas", "cultivo", "plantar", "sembrar"]):
            response = self._handle_crop_recommendation(message_lower)
            topic = "crop_recommendation"
            confidence = 0.85
        elif any(word in message_lower for word in ["maiz", "frijol", "arroz", "cafe", "tomate"]):
            response = self._handle_specific_crop(message_lower)
            topic = "crop_information"
            confidence = 0.80
        else:
            response = "Interesante pregunta. ¿Podrías ser más específico sobre qué tipo de información agrícola necesitas? Puedo ayudarte con recomendaciones de cultivos, análisis de suelo, y consejos de siembra."
            topic = "general"
            confidence = 0.60
        
        return {
            "response": response,
            "topic": topic,
            "confidence": confidence,
            "suggestions": self._get_relevant_suggestions(topic)
        }
    
    def _handle_soil_question(self, message):
        if "arcilloso" in message:
            return "El suelo arcilloso retiene bien el agua y es excelente para cultivos como arroz y algunos tipos de maíz. Sin embargo, puede necesitar mejor drenaje para otros cultivos."
        elif "arenoso" in message:
            return "El suelo arenoso tiene buen drenaje pero necesita más riego y fertilización. Es ideal para cultivos como frijol y algunos vegetales de raíz."
        elif "franco" in message:
            return "¡Excelente! El suelo franco es ideal para la mayoría de cultivos. Tiene buen balance de drenaje y retención de nutrientes."
        else:
            return self.common_responses["soil_questions"][0]
    
    def _handle_crop_recommendation(self, message):
        if any(word in message for word in ["seco", "temporal", "lluvia"]):
            return "Para zonas secas o de temporal, te recomiendo cultivos resistentes como frijol, sorgo o maíz criollo. Estos requieren menos agua y se adaptan mejor a condiciones variables."
        elif any(word in message for word in ["riego", "agua", "humedo"]):
            return "Con disponibilidad de riego, tienes más opciones: maíz híbrido, tomate, chile, o incluso arroz si tienes suficiente agua. ¿Qué tipo de riego tienes disponible?"
        else:
            return self.common_responses["recommendations"][0] + " maíz, frijol o calabaza, dependiendo de tus condiciones específicas."
    
    def _handle_specific_crop(self, message):
        for crop, info in self.crop_knowledge.items():
            if crop in message:
                return f"Sobre {crop}: {info['conditions']}. Temporada ideal: {info['season']}. Cuidados: {info['care']}"
        return "¿Sobre qué cultivo específico te gustaría saber más? Tengo información detallada sobre maíz, frijol, arroz, café y tomate."
    
    def _get_relevant_suggestions(self, topic):
        if topic == "greeting":
            return [
                "¿Qué cultivo me recomiendas?",
                "Tengo una hectárea de terreno",
                "Necesito análisis de mi suelo"
            ]
        elif topic == "soil_analysis":
            return [
                "Tengo suelo arcilloso",
                "Mi terreno es arenoso",
                "¿Cómo mejoro mi suelo?"
            ]
        elif topic == "crop_recommendation":
            return [
                "Tengo sistema de riego",
                "Cultivo de temporal",
                "¿Qué es más rentable?"
            ]
        else:
            return self.suggestions[:3]

# Initialize chatbot
chatbot = CropChatBot()

@chat_bp.route('/api/chat', methods=['POST'])
@require_auth_optional
def chat_endpoint():
    """Handle AI-powered chat conversations."""
    start_time = datetime.now()
    
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_id = data.get('conversationId')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Generate new conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Get user info
        user_id = None
        if hasattr(request, 'current_user') and request.current_user:
            user_id = request.current_user['id']
        
        # Generate AI response
        ai_response = chatbot.generate_response(message)
        
        # Save conversation to database
        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        save_chat_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message=message,
            response=ai_response['response'],
            suggestions=ai_response['suggestions'],
            context={
                'topic': ai_response['topic'],
                'confidence': ai_response['confidence']
            },
            response_time_ms=response_time_ms
        )
        
        # Prepare response
        response = {
            'response': ai_response['response'],
            'conversationId': conversation_id,
            'suggestions': ai_response['suggestions'],
            'context': {
                'topic': ai_response['topic'],
                'confidence': ai_response['confidence']
            }
        }
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/chat', 'POST', 200, response_time)
        
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request('/api/chat', 'POST', 500, response_time, str(e))
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def save_chat_message(conversation_id, user_id, message, response, suggestions, context, response_time_ms):
    """Save chat message to database."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("No database connection available for chat storage")
            return False
        
        cursor = conn.cursor()
        
        # Ensure conversation exists
        cursor.execute("""
            INSERT INTO chat_conversations (id, conversation_id, user_id)
            VALUES (gen_random_uuid(), %s, %s)
            ON CONFLICT (conversation_id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
        """, (conversation_id, user_id))
        
        # Get the conversation record ID
        cursor.execute("SELECT id FROM chat_conversations WHERE conversation_id = %s", (conversation_id,))
        conversation_record = cursor.fetchone()
        
        if conversation_record:
            conversation_record_id = conversation_record[0]
            
            # Save the message
            cursor.execute("""
                INSERT INTO chat_messages (
                    conversation_id, message_type, message, response, 
                    suggestions, context, response_time_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                conversation_record_id, 'user', message, response,
                json.dumps(suggestions), json.dumps(context), response_time_ms
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Chat message saved for conversation {conversation_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving chat message: {e}")
        return False

@chat_bp.route('/api/chat/conversations/<conversation_id>', methods=['GET'])
@require_auth_optional
def get_conversation_history(conversation_id):
    """Get conversation history."""
    start_time = datetime.now()
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get conversation messages
        cursor.execute("""
            SELECT 
                cm.message_type,
                cm.message,
                cm.response,
                cm.suggestions,
                cm.context,
                cm.created_at,
                cm.response_time_ms
            FROM chat_messages cm
            JOIN chat_conversations cc ON cm.conversation_id = cc.id
            WHERE cc.conversation_id = %s
            ORDER BY cm.created_at ASC
        """, (conversation_id,))
        
        messages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'type': msg['message_type'],
                'message': msg['message'],
                'response': msg['response'],
                'suggestions': json.loads(msg['suggestions']) if msg['suggestions'] else [],
                'context': json.loads(msg['context']) if msg['context'] else {},
                'timestamp': msg['created_at'].isoformat() if msg['created_at'] else None,
                'responseTime': msg['response_time_ms']
            })
        
        response = {
            'conversationId': conversation_id,
            'messages': formatted_messages,
            'messageCount': len(formatted_messages)
        }
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/chat/conversations/{conversation_id}', 'GET', 200, response_time)
        
        return jsonify(response), 200
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        log_api_request(f'/api/chat/conversations/{conversation_id}', 'GET', 500, response_time, str(e))
        logger.error(f"Get conversation error: {e}", exc_info=True)
        
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
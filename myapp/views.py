from django.shortcuts import render

import re
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client
import logging
from twilio.rest import Client
import json
import os
from datetime import datetime
import openai 
from django.conf import settings
from twilio.rest import Client
from rest_framework import status
logger = logging.getLogger(__name__)
import os
from openai import OpenAI
import tempfile
from word2number import w2n


datos_personas = [
  {
    "nombres": "Juan Carlos Pérez Gómez",
    "tipo_documento": "CC",
    "cedula": "1017234567",
    "estado_afiliacion": "Activo",
    "tipo": "CC"
  },
  {
    "nombres": "Ana María Rodríguez Silva",
    "tipo_documento": "CC",
    "cedula": "52876543",
    "estado_afiliacion": "Inactivo",
    "tipo": "CC"
  },
  {
    "nombres": "Michael Smith Johnson",
    "tipo_documento": "CE",
    "cedula": "345678",
    "estado_afiliacion": "Activo",
    "tipo": "CE"
  },
  {
    "nombres": "Carlos Alberto Ramírez López",
    "tipo_documento": "CC",
    "cedula": "79876123",
    "estado_afiliacion": "Activo",
    "tipo": "CC"
  },
  {
    "nombres": "David Chen",
    "tipo_documento": "PAS",
    "cedula": "G12345678",
    "estado_afiliacion": "Inactivo",
    "tipo": "PAS"
  }
]

"""
Conversion de texto a numeros
"""
def convertir_numeros_en_texto(texto):
    numeros = {
        "cero": "0", "uno": "1", "una": "1", "dos": "2", "tres": "3",
        "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7",
        "ocho": "8", "nueve": "9", "diez": "10", "once": "11",
        "doce": "12", "trece": "13", "catorce": "14", "quince": "15",
        "dieciséis": "16", "diecisiete": "17", "dieciocho": "18",
        "diecinueve": "19", "veinte": "20", "veintiuno": "21",
        "veintidós": "22", "veintitrés": "23", "veinticuatro": "24",
        "treinta": "30", "cuarenta": "40", "cincuenta": "50",
        "sesenta": "60", "setenta": "70", "ochenta": "80",
        "noventa": "90", "cien": "100", "mil": "1000"
    }

    palabras = texto.lower().split()
    resultado = []
    buffer_numerico = []

    def flush_buffer():
        if buffer_numerico:
            resultado.append("".join(buffer_numerico))
            buffer_numerico.clear()

    for palabra in palabras:
        palabra_limpia = re.sub(r'[^\wñáéíóúü]', '', palabra)

        if palabra_limpia in numeros:
            buffer_numerico.append(numeros[palabra_limpia])
        elif palabra_limpia.isdigit():
            buffer_numerico.append(palabra_limpia)
        else:
            flush_buffer()
            resultado.append(palabra)

    flush_buffer()
    return " ".join(resultado)

def consultar_por_documento(tipo_doc, numero_doc):
    """
    Busca una persona en una lista por su tipo y número de documento.

    Args:
        lista_personas (list): La lista de diccionarios de personas.
        tipo_doc (str): El tipo de documento a buscar (ej. "CC", "CE", "PAS").
        numero_doc (str): El número de documento a buscar.

    Returns:
        dict: El diccionario completo de la persona si se encuentra.
        None: Si no se encuentra ninguna persona con esos datos.
    """
    for persona in datos_personas:
        # Comprueba si el tipo y el número del documento coinciden
        if persona.get("tipo_documento") == tipo_doc and persona.get("cedula") == numero_doc:
            return persona  # Devuelve el diccionario de la persona encontrada
    
    return None

def transcribe_audio(audio_path):
    # Cliente OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Abrir el archivo de audio
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=audio_file
        )

    raw_text = transcription.text
    print("Texto original:", raw_text)

    # Convertir texto con números en palabras a números reales
    normalized_text = convertir_numeros_en_texto(raw_text)
    print("Texto normalizado:", normalized_text)

    return normalized_text 
    
    
    
def process_ia(message):
         
        openai.api_key = settings.OPENAI_API_KEY
        
        user_message = message
        
        if not user_message:
            return Response({"error": "No se proporcionó mensaje"}, status=status.HTTP_400_BAD_REQUEST)

        # Definir funciones disponibles
        tools = [
            
            {      
             "type": "file_search",      
             "vector_store_ids": [ "vs_6859cd05f36081919a108187f6fe1af4"]    
                },
            {
                "type": "function",
                "name": "consultar_estado_afiliado",
                "description": "Busca en la BD el estado de afiliación y beneficios de una persona.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "required": [
                    "tipo_id",
                    "num_id"
                    ],
                    "properties": {
                    "tipo_id": {
                        "type": "string",
                        "enum": [
                        "CC",
                        "CE",
                        "PAS"
                        ],
                        "description": "Tipo de documento (CC: Cédula, CE: Cédula de extranjería, PAS: Pasaporte)"
                    },
                    "num_id": {
                        "type": "string",
                        "description": "Número de documento sin espacios ni separadores."
                    }
                    },
                    "additionalProperties": False
                }
            }
            
        ]

        messages = [{"role": "user", "content": user_message}]

        try:
            
            response = openai.responses.create(
                
                model="gpt-4.1",
                prompt={
                "id": settings.PROMPT_ID,
                "version": settings.PROMPT_VERSION
                },
                input=messages,
                tool_choice="auto",
                tools=tools,
                store=True
            )



            choice = response.output[0]
            resultado = ''
                
            if hasattr(choice, 'content') and choice.content and hasattr(choice.content[0], 'text'):
                resultado = choice.content[0].text
                return resultado

            # ✅ Si no tiene texto, asumimos que es una llamada a función
            if hasattr(choice, 'arguments'):
                arguments = json.loads(choice.arguments)
                tipo = arguments.get("tipo_id")
                cedula = arguments.get("num_id")
                
                resultado = consultar_por_documento(tipo, cedula)

                # Agregamos el mensaje original (la llamada a la función)
                messages.append(choice)

                # Agregamos el resultado de la función
                messages.append({
                    "type": "function_call_output",
                    "call_id": choice.call_id,
                    "output": str(resultado)
                })

                # Llamamos nuevamente a la API con el resultado
                response_2 = openai.responses.create(
                    model="gpt-4.1",
                    input=messages,
                    tools=tools,
                )

                print(response_2.output_text)
                return response_2.output_text

            
        except Exception as e:
            print(e)
            return Response({"error": str(e)}, status=500)
        
    
    

class ChatbotFunctionCallingView(APIView):

    def post(self, request):
        
        logger.info("📥 ChatbotVoiceView POST request received")
        print(request.POST)
        
        
        user_number = request.POST.get("From")  # Ej: 'whatsapp:+573203624329'
        media_url = request.POST.get("MediaUrl0")
        media_type = request.POST.get("MediaContentType0")  # ej: 'audio/ogg'
        if not media_url or 'audio' not in media_type:
            return Response({"error": "No se recibió una nota de voz válida."}, status=400)

        logger.info(f"📡 Audio recibido de {user_number}: {media_url} ({media_type})")
        
        # Descargar el archivo de audio
        audio_response = requests.get(media_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TOKEN_TWILIO))

        if audio_response.status_code != 200:
            print(f"❌ Error al descargar el audio: {audio_response.status_code} - {audio_response.text}")
            return Response({"error": "No se pudo descargar el audio."}, status=500)

        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, "audio.ogg")
        
        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        

        # Transcribir el audio (aquí usamos OpenAI Whisper como ejemplo)
        transcription_text = transcribe_audio(audio_path)
        json_file = "mensajes_audio.json"
        data_to_save = {
            "from": user_number,
            "media_url": media_url,
            "transcription": transcription_text,
            "timestamp": datetime.now().isoformat()
        }

        if os.path.exists(json_file):
           with open(json_file, "r", encoding="utf-8") as f:
               existing_data = json.load(f)
        else:
           existing_data = []

        existing_data.append(data_to_save)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
            
            
        
        
        answer = process_ia(transcription_text)
        print(answer)
        

         
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TOKEN_TWILIO)
        
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=f"{answer}",
            to=user_number
        )
        
        print(message)
        
        print("Mensaje enviado con SID:", message.sid)
        

        return Response({"response": "works",})
    
    
    def put(self, request):
        message = request.data.get('message')

        answer = process_ia(message)
        print(answer)
 
        return Response({"response": answer,})
        
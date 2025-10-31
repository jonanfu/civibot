# actions/actions.py
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests

class ActionGetAllPokemon(Action):
    """Acción para obtener la lista de los primeros 20 Pokémon."""

    def name(self) -> Text:
        return "action_get_all_pokemon"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Hacer la petición a la PokeAPI
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=20")
        
        if response.status_code == 200:
            data = response.json()
            # Crear una lista de nombres
            pokemon_list = [pokemon['name'] for pokemon in data['results']]
            # Formatear la respuesta
            message = "¡Aquí tienes una lista de Pokémon:\n" + "\n".join(f"- {name.title()}" for name in pokemon_list)
        else:
            message = "Lo siento, no pude obtener la información en este momento."
        
        dispatcher.utter_message(text=message)
        return []

class ActionGetPokemonDetail(Action):
    """Acción para obtener detalles de un Pokémon específico."""

    def name(self) -> Text:
        return "action_get_pokemon_detail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extraer la entidad 'pokemon_name' del mensaje del usuario
        pokemon_name = next(tracker.get_latest_entity_values("pokemon_name"), None)
        
        if not pokemon_name:
            dispatcher.utter_message(text="Por favor, dime de qué Pokémon quieres saber.")
            return []
        
        # Hacer la petición a la PokeAPI para el Pokémon específico
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}")
        
        if response.status_code == 200:
            data = response.json()
            # Extraer información específica
            name = data['name'].title()
            abilities = [ability['ability']['name'] for ability in data['abilities']]
            types = [type_data['type']['name'] for type_data in data['types']]
            
            message = f"**{name}**\n"
            message += f"**Tipo(s):** {', '.join(types)}\n"
            message += f"**Habilidades:** {', '.join(abilities[:3])}" # Muestra las 3 primeras
        else:
            message = f"No pude encontrar información para {pokemon_name}. ¿Estás seguro de que ese es un Pokémon?"
        
        dispatcher.utter_message(text=message)
        return []

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, AllSlotsReset, ConversationPaused
from typing import Text, List, Any, Dict
from .gcba_faqs_db import faqs_database # Python ve el archivo y la lista
import random
import re
import json

faqs_database = []

try:
    from .gcba_faqs_db import faqs_database as loaded_faqs
    faqs_database = loaded_faqs
    print(f"DEBUG: FAQs cargadas exitosamente. Total: {len(faqs_database)}")
except ImportError:
    print("ADVERTENCIA CRÍTICA: No se pudo importar el módulo gcba_faqs_db. Busque el archivo en la carpeta de actions.")


class ActionSubmitAppointmentForm(Action):
    def name(self) -> Text:
        return "action_submit_appointment_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        cita_fecha = tracker.get_slot('date')
        
        # Aquí iría el código para llamar a una API/DB para crear la cita.
        # Simulamos una falla/éxito
        success = random.choice([True, True, True, False]) 
        
        if success:
            print(f"DEBUG: Cita creada con éxito para {cita_fecha}.")
            return [SlotSet("action_result", "success")] 
        else:
            print("DEBUG: Falla al crear la cita. Razón: [Simulación].")
            return [SlotSet("action_result", "failure")]


class ActionRescheduleAppointment(Action):
    def name(self) -> Text:
        return "action_reschedule_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        cita_id = tracker.get_slot('appointment_id')
        nueva_fecha = tracker.get_slot('date') 
        
        # Aquí iría el código para llamar a una API/DB para reagendar.
        success = (cita_id is not None) and (random.random() > 0.3)
        
        if success:
            print(f"DEBUG: Cita {cita_id} reagendada para {nueva_fecha}.")
            return [SlotSet("action_result", "success")]
        else:
            print("DEBUG: Falla en el reagendamiento.")
            return [SlotSet("action_result", "failure")]

class ActionCancelAppointment(Action):
    def name(self) -> Text:
        return "action_cancel_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Lógica para obtener el ID de la cita y llamar a la API de cancelación
        print("DEBUG: Procesando cancelación de cita...")
        
        # Simulación de éxito
        dispatcher.utter_message(text="Tu cita ha sido cancelada exitosamente.")
        return [AllSlotsReset()] # Limpia el historial para una nueva conversación

class ActionAskNewRescheduleDate(Action):
    def name(self) -> Text:
        return "action_ask_new_reschedule_date"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Por favor, indicame la **nueva fecha y hora** para la que deseas reagendar tu cita.")
        return []

class ActionCheckAppointment(Action):
    def name(self) -> Text:
        return "action_check_appointment"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Por favor, dame el ID de la cita que deseas consultar.")
        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # El bot indica que no entendió y ofrece opciones
        dispatcher.utter_message(response="utter_ask_rephrase")
        return [SlotSet("action_result", None), FollowupAction("action_listen")]

class ActionSearchFAQ(Action):

    def name(self) -> Text:
        return "action_search_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_text = tracker.latest_message['text'].lower()
        
        categoria_filtrada = tracker.get_slot('process_category') 

        best_match = None
        max_score = 0
        
 
        if categoria_filtrada:
            search_pool = [
                faq for faq in faqs_database 
                if faq.get('categoria', '').lower() == categoria_filtrada.lower()
            ]
            print(f"DEBUG: Buscando en categoría filtrada: {categoria_filtrada}. Pool size: {len(search_pool)}")
        else:
            search_pool = faqs_database
            print(f"DEBUG: Buscando en TODAS las FAQs. Pool size: {len(search_pool)}")

        user_words = set(re.findall(r'\b\w{3,}\b', user_text))

        for faq in search_pool:
            
            faq_terms = " ".join(faq.get('keywords', [])).lower() + " " + faq.get('pregunta', '').lower()
            
            score = 0
            for word in user_words:
                if word in faq_terms:
                    score += 1

            if score > max_score:
                max_score = score
                best_match = faq

        if best_match and max_score >= 2:
            
            respuesta_final = (
                f"**{best_match['pregunta']}**\n\n"
                f"{best_match['respuesta']} "
                f"\n\n👉 Más información aquí: {best_match['url_referencia']}."
            )
            dispatcher.utter_message(text=respuesta_final)
            
        else:
            dispatcher.utter_message(response="utter_faq_not_found")
        return [SlotSet("process_category", None)]

class ValidateAppointmentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_appointment_form"

    async def validate_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return {"date": slot_value}

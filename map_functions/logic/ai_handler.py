import json
import os
import requests
from google import genai
from google.genai import types

def get_api_key():
    """Helper to dynamically fetch the saved key."""
    if os.path.exists("data/json/settings_config.json"):
        try:
            with open("data/json/settings_config.json", "r") as f:
                data = json.load(f)
                key = data.get("api_key", "")
                if key: return key
        except: pass
    # Provide your default fallback key here if desired
    return "AIzaSyAJlAkHmBTmSODDZSbrWOuKWDC_4le8Y9o"

def get_ai_mode():
    """Reads the settings config to see which AI is active."""
    if os.path.exists("data/json/settings_config.json"):
        try:
            with open("data/json/settings_config.json", "r") as f:
                data = json.load(f)
                return data.get("ai_mode", "GEMINI")
        except: pass
    return "GEMINI"

def get_world_context(nation_data, ai_nation, target_nation=None):
    ai_stats = nation_data.get(ai_nation, {})
    manpower = ai_stats.get("manpower", 0)
    materials = ai_stats.get("materials", 0)
    at_war_with = ai_stats.get("at_war_with", [])
    allies = ai_stats.get("allied_with", [])
    
    context = f"You are the leader of {ai_nation}. "
    context += f"Your economy: {manpower} Manpower, {materials} Materials. "
    
    if at_war_with:
        context += f"You are currently AT WAR with: {', '.join(at_war_with)}. "
    if allies:
        context += f"Your allies are: {', '.join(allies)}. "
        
    if target_nation:
        context += f"You are currently evaluating relations with {target_nation}. "
        
    return context

def call_ollama(system_prompt, user_prompt):
    """Helper to hit local Ollama instance."""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3", # Make sure this matches exactly what you downloaded!
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "format": "json",
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=45)
        
        # --- NEW: Print the actual error message from Ollama ---
        if response.status_code != 200:
            print(f"Ollama Server Replied: {response.text}")
            
        response.raise_for_status()
        data = response.json()
        return json.loads(data["message"]["content"])
    except Exception as e:
        print(f"Ollama Python Error: {e}")
        return None

def evaluate_diplomatic_proposal(nation_data, ai_nation, sender_nation, action_type):
    mode = get_ai_mode()
    
    if mode == "OFF":
        return False, "Our diplomats are currently unavailable (AI is OFF)."

    context = get_world_context(nation_data, ai_nation, sender_nation)
    system_prompt = (
        "You are an AI playing a grand strategy game. You act as the leader of your nation. "
        "Evaluate the diplomatic proposal based on your current war status, economy, and logic. "
        "Reply ONLY with a valid JSON object matching this schema: "
        '{"accepted": true or false, "message": "In-character dialogue responding to the proposal"}'
    )
    user_prompt = f"{context}\n{sender_nation} has proposed a {action_type}. Do you accept?"

    if mode == "OLLAMA":
        result = call_ollama(system_prompt, user_prompt)
        if result:
            return result.get("accepted", False), result.get("message", "We decline.")
        return False, "Ollama server error or timeout."

    # Fallback to Gemini
    try:
        # --- Instantiated dynamically so it catches key updates! ---
        client = genai.Client(api_key=get_api_key())
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        reply_json = json.loads(response.text)
        return reply_json.get("accepted", False), reply_json.get("message", "We decline.")
    except Exception as e:
        print(f"Gemini Error: {e}")
        return False, "API Error."

def process_custom_message(nation_data, ai_nation, sender_nation, message_content):
    mode = get_ai_mode()
    if mode == "OFF":
        return "Message received (AI is OFF)."

    context = get_world_context(nation_data, ai_nation, sender_nation)
    system_prompt = (
        "You are an AI leader in a grand strategy game. Respond to the incoming diplomatic message in character. "
        "Keep your response under 2 sentences. "
        "Reply ONLY with a valid JSON object matching this schema: "
        '{"message": "Your in-character response here"}'
    )
    user_prompt = f"{context}\nMessage from {sender_nation}: '{message_content}'"
    
    if mode == "OLLAMA":
        result = call_ollama(system_prompt, user_prompt)
        if result:
            return result.get("message", "Message received.")
        return "Ollama server error."

    try:
        # --- Instantiated dynamically so it catches key updates! ---
        client = genai.Client(api_key=get_api_key())
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        reply_json = json.loads(response.text)
        return reply_json.get("message", "Message received.")
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Message received."
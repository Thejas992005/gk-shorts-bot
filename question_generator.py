import requests
import json
import os
import random
import time

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

TOPICS = [
    # GK
    "World Geography", "Indian History", "Famous Personalities",
    "Current Affairs", "World History", "Sports",
    # Science
    "Physics", "Chemistry", "Biology", "Space & Universe",
    "Human Body", "Animals & Nature", "Inventions & Discoveries",
    # Math
    "Basic Arithmetic", "Geometry", "Number Theory",
    "Mathematical Puzzles", "Algebra", "Statistics"
]

CATEGORY_PROMPTS = {
    "GK": "Generate an interesting General Knowledge MCQ question about {topic}.",
    "Science": "Generate a fascinating Science MCQ question about {topic}. Make it educational and mind-blowing.",
    "Math": "Generate a fun Math MCQ question about {topic}. Include actual numbers. Make it challenging but solvable in 10 seconds."
}

def get_category(topic):
    gk = ["World Geography","Indian History","Famous Personalities","Current Affairs","World History","Sports"]
    science = ["Physics","Chemistry","Biology","Space & Universe","Human Body","Animals & Nature","Inventions & Discoveries"]
    if topic in gk: return "GK"
    if topic in science: return "Science"
    return "Math"

FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2-7b-instruct:free",
]

def generate_question(retries=5):
    topic = random.choice(TOPICS)
    category = get_category(topic)
    base_prompt = CATEGORY_PROMPTS[category].format(topic=topic)

    prompt = f"""{base_prompt}
Return ONLY a JSON object in this exact format, no extra text, no markdown:
{{
  "question": "Your question here?",
  "options": {{
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  }},
  "answer": "A",
  "explanation": "Brief explanation in one sentence.",
  "topic": "{topic}",
  "category": "{category}"
}}"""

    for model in FREE_MODELS:
        for attempt in range(3):
            try:
                time.sleep(2)
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://gk-shorts-bot.railway.app",
                        "X-Title": "GK Shorts Bot"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.8,
                        "max_tokens": 500
                    }
                )
                if response.status_code == 404:
                    break
                if response.status_code != 200:
                    raise Exception(f"API error {response.status_code}")

                text = response.json()["choices"][0]["message"]["content"].strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    text = text[start:end]
                result = json.loads(text)
                print(f"✅ [{category}] Question generated: {result['question'][:50]}...")
                return result
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                time.sleep(10)

    raise Exception("All models failed")

if __name__ == "__main__":
    q = generate_question()
    print(json.dumps(q, indent=2))

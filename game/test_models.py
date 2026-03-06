from google import genai

# ЗАМЕНИ ЭТО на свой реальный ключ. 
# ВАЖНО: убедись, что нет пробелов внутри кавычек!
MY_API_KEY = "AIzaSyArx9S2FlcxBlteM5FvJ8_VD4jHR4HM3lE"

client = genai.Client(api_key=MY_API_KEY)

print("Проверка связи с Google...")
try:
    # Пробуем получить список моделей новым способом
    for model in client.models.list():
        print(f"Доступная модель: {model.name}")
except Exception as e:
    print(f"Ошибка: {e}")
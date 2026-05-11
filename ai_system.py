from openai import OpenAI
import os

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Sen sert disiplinli fitness ve yaşam koçusun.

Kısa, net ve motive edici konuş.
Bahane kabul etme.
"""

async def ask_ai(user, text):

    memory_text = f"""
Kullanıcı adı: {user[1]}
Toplam mesaj: {user[2]}
Streak: {user[3]}
Kilo: {user[5]}
Su: {user[6]}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "system",
                "content": memory_text
            },
            {
                "role": "user",
                "content": text
            }
        ],
        max_tokens=300
    )

    return response.choices[0].message.content

def ask_food_ai(image_base64):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
Sen profesyonel beslenme uzmanısın.

Yemek fotoğrafını analiz et.

Şunları yaz:
- tahmini yemek
- tahmini kalori
- protein
- karbonhidrat
- yağ
- sağlıklı mı yorumu
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Bu yemeği analiz et"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content
import os
import streamlit as st
from google import genai
from google.genai import types

# --- BAUN ASİSTAN AYARLARI ---
BOT_ADI = "BAUN Asistan"
BOT_ACIKLAMA = "Balıkesir Üniversitesi öğrencileri için yapay zekâ destekli asistan."
BOT_KARAKTERI = """
Sen BAUN Asistan'sın. Balıkesir Üniversitesi (BAUN) öğrencilerine yardımcı olan,
Türkçe konuşan, samimi, açık ve güvenilir bir üniversite asistanısın.

Üniversite, fakülteler, meslek yüksekokulları, bölümler, akademik takvim,
kayıt, dersler, sınavlar, not sistemi, öğrenci işleri, kampüs, yemekhane,
yurtlar ve üniversite hizmetleri hakkında soruları yanıtlamaya çalış.

ÖNEMLİ DOĞRULUK KURALLARI:
- Sana verilen konuşma içeriğinde veya sağlanan kaynaklarda bulunmayan kesin bilgileri uydurma.
- Güncel tarih, ücret, başvuru tarihi, kontenjan, yönetmelik veya iletişim bilgisi gibi
  değişebilen konularda emin değilsen bunu açıkça belirt.
- Bilmediğin ya da doğrulayamadığın bir konuda "Bu bilgiyi şu an doğrulayamıyorum"
  de ve kullanıcıyı ilgili BAUN biriminin resmî duyurularına yönlendir.
- Tahminlerini kesin bilgi gibi sunma.
- Üniversite dışındaki genel sorulara da yardımcı olabilirsin; ancak BAUN'a özel
  bilgiymiş gibi gösterme.
- Kısa, anlaşılır ve doğal cevaplar ver. Gerektiğinde adım adım açıkla.
"""
YARATICILIK = 0.3
GEMINI_MODEL = "gemini-3.5-flash-lite"
# ----------------------------

st.set_page_config(page_title=BOT_ADI, page_icon="🎓")
st.title(f"🎓 {BOT_ADI}")
st.caption(BOT_ACIKLAMA)

# API anahtarını önce Streamlit Secrets, yoksa ortam değişkenlerinden al.
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    api_key = None

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "GEMINI_API_KEY bulunamadı. Streamlit Cloud uygulamanın "
        "*Settings > Secrets* bölümüne GEMINI_API_KEY = \"anahtarın\" şeklinde ekle."
    )
    st.stop()

client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Önceki sohbet mesajlarını göster.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Yeni mesajı işle.
if prompt := st.chat_input("BAUN hakkında merak ettiğini sor..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    contents = [
        types.Content(
            role="user" if message["role"] == "user" else "model",
            parts=[types.Part.from_text(text=message["content"])],
        )
        for message in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("BAUN Asistan düşünüyor..."):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=BOT_KARAKTERI,
                        temperature=YARATICILIK,
                    ),
                )
                answer = response.text or "Şu an yanıt oluşturamadım. Lütfen tekrar dene."
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as error:
                st.error(
                    "Gemini API isteği başarısız oldu. Model adının API hesabında "
                    "desteklendiğini ve API anahtarının doğru olduğunu kontrol et. "
                    f"Teknik hata: {error}"
                )

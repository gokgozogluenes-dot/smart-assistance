
    quick_cols = st.columns(4)
    quick_questions = [
        ("📅 Akademik takvim", "Balıkesir Üniversitesi güncel akademik takvimini bul."),
        ("🏫 Bölümler ve programlar", "Balıkesir Üniversitesi'ndeki fakülteleri, MYO'ları ve programları göster."),
        ("👩‍🏫 Akademik kadro", "Balıkesir Üniversitesi akademik kadrosunu resmî kaynaklardan nasıl bulabilirim?"),
        ("🧑‍🎓 Öğrenci işleri", "Balıkesir Üniversitesi öğrenci işleri ve önemli öğrenci işlemleri hakkında bilgi ver."),
    ]
    for col, (label, question) in zip(quick_cols, quick_questions):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.pending_prompt = question
                st.rerun()

# =========================================================
# ÖNCEKİ MESAJLARI GÖSTER
# =========================================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("🔎 Kaynaklar"):
                for source in message["sources"]:
                    st.markdown(f"- [{source['title']}]({source['url']})")

# =========================================================
# MESAJI AL VE GEMINI'YE GÖNDER
# =========================================================
prompt = st.chat_input("Mesajını yaz...")

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    contents = []
    for message in st.session_state.messages:
        contents.append(
            types.Content(
                role="user" if message["role"] == "user" else "model",
                parts=[types.Part.from_text(text=message["content"])],
            )
        )

    with st.chat_message("assistant"):
        with st.spinner("Bir saniye, düşünüyorum..."):
            try:
                config_ayarları = {
                    "system_instruction": SISTEM_TALIMATI,
                    "temperature": YARATICILIK,
                }

                # Üniversiteyle ilgili sorularda Google Search grounding aç.
                if universite_sorusu_mu(prompt):
                    config_ayarları["tools"] = [
                        types.Tool(google_search=types.GoogleSearch())
                    ]

                response = client.models.generate_content(
                    model=MODEL_ADI,
                    contents=contents,
                    config=types.GenerateContentConfig(**config_ayarları),
                )

                cevap = response.text or "Şu an düzgün bir cevap oluşturamadım. Bir daha dener misin?"
                st.markdown(cevap)

                # Google Search kaynaklarını yanıtın altına ekle.
                kaynaklar = []
                try:
                    adaylar = response.candidates or []
                    if adaylar and adaylar[0].grounding_metadata:
                        parcalar = adaylar[0].grounding_metadata.grounding_chunks or []
                        gorulen_url = set()
                        for parca in parcalar:
                            web_kaynagi = getattr(parca, "web", None)
                            if web_kaynagi:
                                url = getattr(web_kaynagi, "uri", None)
                                baslik = getattr(web_kaynagi, "title", None) or "Kaynak"
                                if url and url not in gorulen_url:
                                    kaynaklar.append({"title": baslik, "url": url})
                                    gorulen_url.add(url)
                except Exception:
                    kaynaklar = []

                if kaynaklar:
                    with st.expander("🔎 Kaynaklar"):
                        for kaynak in kaynaklar:
                            st.markdown(f"- [{kaynak['title']}]({kaynak['url']})")
                elif universite_sorusu_mu(prompt):
                    st.info(
                        "Bu cevap için arama kaynağı alınamadı. Özellikle akademik "
                        "personel bilgilerini üniversitenin resmî sayfasından kontrol et."
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": cevap,
                        "sources": kaynaklar,
                    }
                )

            except Exception as hata:
                st.error("Bir hata oluştu. Biraz sonra tekrar deneyebilir misin?")
                with st.expander("Teknik hata ayrıntısı"):
                    st.code(str(hata))

import os
import tempfile
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types

# ============================================================
# My AI Platform
# ============================================================

st.set_page_config(
    page_title="My AI Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: "Cairo", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(70,90,180,.18), transparent 30%),
        radial-gradient(circle at 85% 20%, rgba(130,60,180,.15), transparent 30%),
        #090b12;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 28px;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(35,42,70,.96), rgba(18,20,35,.96));
    border: 1px solid rgba(255,255,255,.08);
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 40px;
    margin: 0 0 6px 0;
}

.hero p {
    color: #b9bfd4;
    font-size: 17px;
    margin: 0;
}

.badge {
    display: inline-block;
    padding: 5px 11px;
    margin: 8px 5px 0 0;
    border-radius: 18px;
    background: rgba(100,120,255,.15);
    border: 1px solid rgba(100,120,255,.25);
    color: #d7dbff;
}

div[data-testid="stChatMessage"] {
    border-radius: 18px;
    margin-bottom: 8px;
}

.api-box {
    padding: 16px;
    border-radius: 16px;
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ------------------------------------------------------------
# API key
# ------------------------------------------------------------

secret_key = None
try:
    secret_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    secret_key = None

api_key = (
    secret_key
    or os.environ.get("GEMINI_API_KEY")
    or st.session_state.api_key
)

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------

with st.sidebar:
    st.markdown("# 🤖 My AI")
    st.caption("منصة ذكاء اصطناعي متعددة الأدوات")

    if st.button("➕ محادثة جديدة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    if not secret_key and not os.environ.get("GEMINI_API_KEY"):
        key_input = st.text_input(
            "🔑 Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="ألصقي مفتاح Gemini هنا",
            help="يمكنك وضع المفتاح هنا أو إضافته في Streamlit Secrets.",
        )
        if key_input:
            st.session_state.api_key = key_input
            api_key = key_input

    st.divider()

    temperature = st.slider(
        "🎨 مستوى الإبداع",
        min_value=0.0,
        max_value=1.5,
        value=0.7,
        step=0.1,
    )

    language = st.selectbox(
        "🌐 لغة الرد",
        ["تلقائي", "العربية", "English"],
    )

    st.caption("Gemini 3.8 Flash")

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

st.markdown("""
<div class="hero">
    <h1>🤖 My AI Platform</h1>
    <p>مساعدك الذكي للمحادثة وتحليل الملفات والصور والصوت والفيديو.</p>
    <span class="badge">💬 محادثة</span>
    <span class="badge">📎 ملفات</span>
    <span class="badge">🖼️ صور</span>
    <span class="badge">🎙️ صوت</span>
    <span class="badge">🎬 فيديو</span>
</div>
""", unsafe_allow_html=True)

SYSTEM = (
    "أنت My AI، مساعد ذكاء اصطناعي مفيد وودود. "
    "أجب بوضوح وبشكل عملي. "
    "إذا كان السؤال بالعربية فأجب بالعربية. "
    "لا تدّعي أنك نفذت شيئاً لم تنفذه فعلياً."
)

# ------------------------------------------------------------
# Tabs
# ------------------------------------------------------------

tab_chat, tab_files, tab_image, tab_audio, tab_video = st.tabs(
    ["💬 الشات", "📎 الملفات", "🖼️ الصور", "🎙️ الصوت", "🎬 الفيديو"]
)

# ============================================================
# CHAT
# ============================================================

with tab_chat:
    st.subheader("💬 المحادثة الذكية")

    if not api_key:
        st.markdown(
            '<div class="api-box">🔑 <b>للبدء:</b> ضعي Gemini API Key في القائمة الجانبية، ثم اكتبي رسالتك في مربع المحادثة بالأسفل.</div>',
            unsafe_allow_html=True,
        )

    # Show conversation
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # IMPORTANT: chat input is always visible
    prompt = st.chat_input("اكتبي رسالتك هنا...")

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if not api_key:
                answer = "🔑 أضيفي Gemini API Key أولاً من القائمة الجانبية، ثم أرسلي رسالتك مرة أخرى."
                st.warning(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )
            else:
                try:
                    client = genai.Client(api_key=api_key)

                    contents = []
                    for msg in st.session_state.messages:
                        role = "user" if msg["role"] == "user" else "model"
                        contents.append(
                            types.Content(
                                role=role,
                                parts=[types.Part(text=msg["content"])],
                            )
                        )

                    instruction = SYSTEM

                    if language == "العربية":
                        instruction += "\nاستخدم العربية في الرد."
                    elif language == "English":
                        instruction += "\nAnswer in English."

                    with st.spinner("🤖 أفكر..."):
                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=contents,
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                system_instruction=instruction,
                            ),
                        )

                    answer = response.text or "لم يصلني نص من النموذج."
                    st.markdown(answer)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                except Exception as e:
                    error_text = str(e)
                    st.error(
                        "تعذر الاتصال بـ Gemini.\n\n"
                        f"التفاصيل: {error_text}"
                    )

# ============================================================
# FILES
# ============================================================

with tab_files:
    st.subheader("📎 تحليل الملفات")

    uploaded = st.file_uploader(
        "ارفعي ملفاً",
        type=[
            "pdf", "png", "jpg", "jpeg", "webp",
            "txt", "csv",
            "mp3", "wav", "m4a", "ogg",
            "mp4", "mov", "avi", "webm"
        ],
        key="general_file",
    )

    if uploaded:
        st.success(f"تم اختيار: {uploaded.name}")

        prompt = st.text_area(
            "ماذا تريدين من الملف؟",
            "حلل الملف واشرح أهم المعلومات الموجودة فيه.",
            key="general_file_prompt",
        )

        if st.button(
            "🧠 تحليل الملف",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.error("أضيفي Gemini API Key أولاً.")
            else:
                path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=Path(uploaded.name).suffix,
                    ) as f:
                        f.write(uploaded.getbuffer())
                        path = f.name

                    client = genai.Client(api_key=api_key)
                    gf = client.files.upload(file=path)

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[prompt, gf],
                    )

                    st.markdown("### النتيجة")
                    st.markdown(response.text or "لم يصل رد.")

                except Exception as e:
                    st.error(f"تعذر تحليل الملف: {e}")

                finally:
                    if path:
                        try:
                            os.remove(path)
                        except OSError:
                            pass

# ============================================================
# IMAGE
# ============================================================

with tab_image:
    st.subheader("🖼️ توليد الصور")

    image_prompt = st.text_area(
        "اكتبي وصف الصورة",
        placeholder="مثال: درون توصيل في مدينة سعودية مستقبلية بأسلوب سينمائي واقعي...",
        key="image_prompt",
    )

    if st.button(
        "🎨 إنشاء الصورة",
        type="primary",
        use_container_width=True,
    ):
        if not api_key:
            st.error("أضيفي Gemini API Key أولاً.")
        elif not image_prompt.strip():
            st.warning("اكتبي وصف الصورة أولاً.")
        else:
            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=image_prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE", "TEXT"]
                    ),
                )

                found = False

                for part in response.parts:
                    if part.inline_data is not None:
                        st.image(
                            part.as_image(),
                            use_container_width=True,
                        )
                        found = True

                if not found:
                    st.warning("لم يتم إرجاع صورة من النموذج.")

            except Exception as e:
                st.error(f"تعذر إنشاء الصورة: {e}")

# ============================================================
# AUDIO
# ============================================================

with tab_audio:
    st.subheader("🎙️ تحليل الصوت")

    audio = st.file_uploader(
        "ارفعي تسجيلًا صوتيًا",
        type=["mp3", "wav", "m4a", "ogg"],
        key="audio_file",
    )

    if audio:
        st.audio(audio)

        prompt = st.text_area(
            "المطلوب",
            "فرغ الكلام الموجود في التسجيل ثم لخص أهم النقاط.",
            key="audio_prompt",
        )

        if st.button(
            "🎙️ تحليل الصوت",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.error("أضيفي Gemini API Key أولاً.")
            else:
                path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=Path(audio.name).suffix,
                    ) as f:
                        f.write(audio.getbuffer())
                        path = f.name

                    client = genai.Client(api_key=api_key)
                    af = client.files.upload(file=path)

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[prompt, af],
                    )

                    st.markdown("### 📝 النتيجة")
                    st.markdown(response.text or "لم يصل رد.")

                except Exception as e:
                    st.error(f"تعذر تحليل الصوت: {e}")

                finally:
                    if path:
                        try:
                            os.remove(path)
                        except OSError:
                            pass

# ============================================================
# VIDEO
# ============================================================

with tab_video:
    st.subheader("🎬 تحليل الفيديو")

    video = st.file_uploader(
        "ارفعي فيديو",
        type=["mp4", "mov", "avi", "webm"],
        key="video_file",
    )

    if video:
        st.video(video)

        prompt = st.text_area(
            "المطلوب",
            "حلل الفيديو، صف أهم المشاهد، واكتب ملخصاً احترافياً.",
            key="video_prompt",
        )

        if st.button(
            "🎬 تحليل الفيديو",
            type="primary",
            use_container_width=True,
        ):
            if not api_key:
                st.error("أضيفي Gemini API Key أولاً.")
            else:
                path = None
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=Path(video.name).suffix,
                    ) as f:
                        f.write(video.getbuffer())
                        path = f.name

                    client = genai.Client(api_key=api_key)
                    vf = client.files.upload(file=path)

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=[prompt, vf],
                    )

                    st.markdown("### 🎬 النتيجة")
                    st.markdown(response.text or "لم يصل رد.")

                except Exception as e:
                    st.error(f"تعذر تحليل الفيديو: {e}")

                finally:
                    if path:
                        try:
                            os.remove(path)
                        except OSError:
                            pass

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

st.divider()
st.caption("🤖 My AI Platform · Powered by Gemini")

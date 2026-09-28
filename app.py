import os
import tempfile
from pathlib import Path
from uuid import uuid4

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="My AI Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: "Cairo", sans-serif; }
.stApp {
    background:
      radial-gradient(circle at 12% 5%, rgba(91,103,196,.18), transparent 28%),
      radial-gradient(circle at 88% 8%, rgba(147,75,180,.13), transparent 28%),
      #0b0d12;
}
.block-container {
    max-width: 1050px;
    padding-top: 1rem;
    padding-bottom: 7rem;
}
[data-testid="stSidebar"] {
    background: #101218;
    border-right: 1px solid rgba(255,255,255,.07);
}
[data-testid="stChatMessage"] {
    border: 0;
    border-radius: 18px;
    padding: .45rem .7rem;
    margin: .35rem 0;
}
.chat-title {
    text-align: center;
    padding: 12px 0 18px;
}
.chat-title h1 { font-size: 27px; margin: 0; }
.chat-title p { color: #9da4b7; margin: 3px 0 0; }
.welcome {
    max-width: 760px;
    margin: 13vh auto 5vh;
    text-align: center;
}
.welcome h1 { font-size: 40px; margin-bottom: 8px; }
.welcome p { color: #9da4b7; font-size: 17px; }
.pill {
    display: inline-block;
    padding: 6px 12px;
    margin: 5px 3px;
    border: 1px solid rgba(255,255,255,.09);
    border-radius: 999px;
    color: #cdd2df;
    background: rgba(255,255,255,.035);
}
.side-brand {
    font-size: 22px;
    font-weight: 800;
    padding: 4px 0 10px;
}
.small-muted { color: #8e95a8; font-size: 12px; }
</style>
""",
    unsafe_allow_html=True,
)

TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-3.8-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")

SYSTEM_PROMPT = """
You are My AI, a helpful, intelligent and friendly general-purpose AI assistant.
Answer accurately and clearly. Match the user's language.
If the user writes Arabic, answer in natural Arabic unless they ask for English.
Use Markdown when it improves readability.
For code, always use fenced code blocks with the correct language when possible.
Never claim that you performed an action you did not actually perform.
When a file is attached, use it as evidence and explain what you found.
"""

def new_chat():
    return {"title": "محادثة جديدة", "messages": []}

def make_title(text):
    clean = " ".join(text.strip().split())
    return clean[:34] + ("…" if len(clean) > 34 else "")

def get_secret_key():
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None

@st.cache_resource(show_spinner=False)
def make_client(api_key):
    return genai.Client(api_key=api_key)

def build_history(messages):
    history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        history.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])],
            )
        )
    return history

def upload_for_gemini(client, uploaded):
    suffix = Path(uploaded.name).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(uploaded.getbuffer())
        path = f.name
    try:
        return client.files.upload(file=path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

if "chats" not in st.session_state:
    chat_id = str(uuid4())
    st.session_state.chats = {chat_id: new_chat()}
    st.session_state.active_chat = chat_id

if "active_chat" not in st.session_state or st.session_state.active_chat not in st.session_state.chats:
    st.session_state.active_chat = next(iter(st.session_state.chats))

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

secret_key = get_secret_key()
api_key = secret_key or os.environ.get("GEMINI_API_KEY") or st.session_state.api_key

chat = st.session_state.chats[st.session_state.active_chat]
messages = chat["messages"]

with st.sidebar:
    st.markdown('<div class="side-brand">🤖 My AI</div>', unsafe_allow_html=True)
    st.caption("مساعد ذكي متعدد الأدوات")

    if st.button("✚ محادثة جديدة", use_container_width=True, type="primary"):
        new_id = str(uuid4())
        st.session_state.chats[new_id] = new_chat()
        st.session_state.active_chat = new_id
        st.rerun()

    st.divider()
    st.markdown("**محادثاتك**")

    for cid, item in list(st.session_state.chats.items()):
        c1, c2 = st.columns([5, 1])
        with c1:
            if st.button(
                ("● " if cid == st.session_state.active_chat else "") + item["title"],
                key=f"open_{cid}",
                use_container_width=True,
            ):
                st.session_state.active_chat = cid
                st.rerun()
        with c2:
            if len(st.session_state.chats) > 1:
                if st.button("×", key=f"delete_{cid}", help="حذف المحادثة"):
                    del st.session_state.chats[cid]
                    st.session_state.active_chat = next(iter(st.session_state.chats))
                    st.rerun()

    st.divider()

    if not secret_key and not os.environ.get("GEMINI_API_KEY"):
        key_input = st.text_input(
            "🔑 Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="ألصقي المفتاح هنا",
        )
        if key_input != st.session_state.api_key:
            st.session_state.api_key = key_input
            api_key = key_input

    st.divider()

    mode = st.selectbox(
        "الأداة",
        ["🤖 تلقائي / Chat", "🖼️ توليد صورة", "📎 تحليل ملف"],
    )

    temperature = st.slider("الإبداع", 0.0, 1.5, 0.7, 0.1)

    language = st.selectbox(
        "لغة الرد",
        ["تلقائي", "العربية", "English"],
    )

    st.divider()
    st.markdown("**النماذج**")
    st.caption(f"Text: {TEXT_MODEL}")
    st.caption(f"Image: {IMAGE_MODEL}")

    if st.button("🗑️ مسح رسائل المحادثة", use_container_width=True):
        chat["messages"] = []
        chat["title"] = "محادثة جديدة"
        st.rerun()

st.markdown(
    f"""
<div class="chat-title">
  <h1>🤖 {chat["title"]}</h1>
  <p>محادثة ذكية · ملفات · صور · صوت · فيديو</p>
</div>
""",
    unsafe_allow_html=True,
)

if not api_key:
    st.markdown(
        """
        <div style="padding:16px 18px;border:1px solid rgba(255,193,7,.25);
        background:rgba(255,193,7,.08);border-radius:16px;margin:10px 0 16px;">
        <b>🔑 مفتاح Gemini مطلوب</b><br>
        <span style="color:#b9bfd4;">ضعي المفتاح هنا مرة واحدة، وبعدها سيعمل الشات مباشرة.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    main_key = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIza... الصقي المفتاح هنا",
        label_visibility="visible",
    )
    if main_key and main_key != st.session_state.api_key:
        st.session_state.api_key = main_key
        st.rerun()

with st.expander("📎 إرفاق ملفات وصور وصوت وفيديو", expanded=False):
    attachments = st.file_uploader(
        "يمكنك رفع ملف أو أكثر ثم كتابة طلبك في مربع المحادثة",
        type=[
            "pdf", "txt", "csv", "md", "docx",
            "png", "jpg", "jpeg", "webp",
            "mp3", "wav", "m4a", "ogg",
            "mp4", "mov", "avi", "webm",
        ],
        accept_multiple_files=True,
        key="chat_attachments",
    )
    if attachments:
        st.success("تم إرفاق: " + "، ".join(f.name for f in attachments))

if not messages:
    st.markdown(
        """
<div class="welcome">
  <h1>كيف أقدر أساعدك؟</h1>
  <p>اكتبي أي سؤال، ارفعي ملفاً، أو اختاري توليد صورة.</p>
  <span class="pill">💬 أسئلة ومحادثة</span>
  <span class="pill">📄 PDF وملفات</span>
  <span class="pill">🖼️ صور</span>
  <span class="pill">🎙️ صوت</span>
  <span class="pill">🎬 فيديو</span>
  <span class="pill">💻 كود وبرمجة</span>
</div>
""",
        unsafe_allow_html=True,
    )

for msg in messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_bytes"):
            st.image(msg["image_bytes"], use_container_width=True)
        if msg.get("content"):
            st.markdown(msg["content"])
        if msg.get("files"):
            st.caption("📎 " + " · ".join(msg["files"]))

with st.form("message_composer", clear_on_submit=True):
    st.markdown("**💬 رسالتك**")
    prompt = st.text_area(
        "اكتبي رسالتك هنا…",
        height=90,
        placeholder="اكتبي أي شيء تريدين مني مساعدتك فيه...",
        label_visibility="collapsed",
    )
    send = st.form_submit_button("➤ إرسال", use_container_width=True, type="primary")

if send and prompt.strip():

    user_files = attachments if "attachments" in locals() else []

    if not messages:
        chat["title"] = make_title(prompt)

    messages.append({
        "role": "user",
        "content": prompt,
        "files": [f.name for f in user_files],
    })

    with st.chat_message("user"):
        st.markdown(prompt)
        if user_files:
            st.caption("📎 " + " · ".join(f.name for f in user_files))

    if not api_key:
        st.warning("🔑 أضيفي Gemini API Key في المربع الظاهر أعلى المحادثة، ثم أرسلي الرسالة.")
    else:
        client = make_client(api_key)

        if mode == "🖼️ توليد صورة":
            with st.chat_message("assistant"):
                try:
                    with st.spinner("🎨 جاري إنشاء الصورة…"):
                        response = client.models.generate_content(
                            model=IMAGE_MODEL,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_modalities=["TEXT", "IMAGE"],
                            ),
                        )

                    image_bytes = None
                    text_parts = []

                    for part in response.parts:
                        if getattr(part, "inline_data", None) is not None:
                            image_bytes = part.inline_data.data
                        elif getattr(part, "text", None):
                            text_parts.append(part.text)

                    if image_bytes:
                        st.image(image_bytes, use_container_width=True)
                        caption = "\n\n".join(text_parts)
                        if caption:
                            st.markdown(caption)
                        messages.append({
                            "role": "assistant",
                            "content": caption or "تم إنشاء الصورة.",
                            "image_bytes": image_bytes,
                        })
                    else:
                        answer = response.text or "لم يتم إرجاع صورة."
                        st.markdown(answer)
                        messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    answer = f"تعذر إنشاء الصورة: {e}"
                    st.error(answer)
                    messages.append({"role": "assistant", "content": answer})

        else:
            with st.chat_message("assistant"):
                try:
                    contents = build_history(messages[:-1])

                    if user_files:
                        for uploaded in user_files:
                            with st.spinner(f"📎 رفع {uploaded.name}…"):
                                contents.append(upload_for_gemini(client, uploaded))

                    final_prompt = prompt
                    if user_files:
                        final_prompt = (
                            "Analyze the attached files as part of this conversation. "
                            "Use the files as evidence where relevant.\n\n" + prompt
                        )

                    if language == "العربية":
                        instruction = SYSTEM_PROMPT + "\nRespond in Arabic."
                    elif language == "English":
                        instruction = SYSTEM_PROMPT + "\nRespond in English."
                    else:
                        instruction = SYSTEM_PROMPT

                    with st.spinner("🤖 يفكر…"):
                        response = client.models.generate_content(
                            model=TEXT_MODEL,
                            contents=contents + [final_prompt],
                            config=types.GenerateContentConfig(
                                temperature=temperature,
                                system_instruction=instruction,
                            ),
                        )

                    answer = response.text or "لم يصلني رد من النموذج."
                    st.markdown(answer)
                    messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    answer = f"حدث خطأ أثناء الاتصال بالنموذج. التفاصيل: {e}"
                    st.error(answer)
                    messages.append({"role": "assistant", "content": answer})

st.markdown(
    '<div class="small-muted" style="text-align:center;margin-top:30px;">'
    'My AI Platform · Gemini API · المحادثات محفوظة داخل جلسة المتصفح'
    '</div>',
    unsafe_allow_html=True,
)

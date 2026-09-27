import os
import tempfile
from pathlib import Path
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="My AI Platform", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Cairo',sans-serif}
.stApp{background:radial-gradient(circle at 15% 10%,rgba(70,90,180,.18),transparent 30%),radial-gradient(circle at 85% 20%,rgba(130,60,180,.15),transparent 30%),#090b12}
.block-container{max-width:1250px;padding-top:2rem}
.hero{padding:32px;border-radius:24px;background:linear-gradient(135deg,rgba(35,42,70,.96),rgba(18,20,35,.96));border:1px solid rgba(255,255,255,.08);margin-bottom:24px}
.hero h1{font-size:42px;margin-bottom:4px}.hero p{color:#b9bfd4;font-size:18px}
.badge{display:inline-block;padding:6px 12px;border-radius:18px;background:rgba(100,120,255,.15);border:1px solid rgba(100,120,255,.25);color:#c8ceff;margin:3px}
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages=[]

api_key=None
try:
    api_key=st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass
api_key=api_key or os.environ.get("GEMINI_API_KEY")

with st.sidebar:
    st.markdown("# 🤖 My AI")
    st.caption("منصة ذكاء اصطناعي متعددة الأدوات")
    if st.button("➕ محادثة جديدة",use_container_width=True):
        st.session_state.messages=[]; st.rerun()
    if not api_key:
        api_key=st.text_input("Gemini API Key",type="password",placeholder="ضع المفتاح هنا")
    st.divider()
    temperature=st.slider("الإبداع",0.0,1.5,0.7,0.1)
    language=st.selectbox("لغة الرد",["تلقائي","العربية","English"])

if not api_key:
    st.markdown("""<div class="hero"><h1>🤖 My AI Platform</h1><p>منصة ذكاء اصطناعي للمحادثة وتحليل الملفات وتوليد الصور.</p><span class="badge">💬 Chat</span><span class="badge">📎 Files</span><span class="badge">🖼️ Images</span><span class="badge">🎙️ Audio</span><span class="badge">🎬 Video</span></div>""",unsafe_allow_html=True)
    st.info("أضيفي Gemini API Key من القائمة الجانبية لبدء التشغيل.")
    st.stop()

client=genai.Client(api_key=api_key)

st.markdown("""<div class="hero"><h1>🤖 My AI Platform</h1><p>مساعدك الذكي للمحادثة، الملفات، الصور، الصوت والفيديو.</p><span class="badge">💬 محادثة</span><span class="badge">📎 ملفات</span><span class="badge">🖼️ صور</span><span class="badge">🎙️ صوت</span><span class="badge">🎬 فيديو</span></div>""",unsafe_allow_html=True)

tab_chat,tab_files,tab_image,tab_audio,tab_video=st.tabs(["💬 الشات","📎 الملفات","🖼️ الصور","🎙️ الصوت","🎬 الفيديو"])
SYSTEM="أنت مساعد ذكاء اصطناعي مفيد وودود. أجب بوضوح وبشكل عملي. إذا كان السؤال بالعربية فأجب بالعربية. لا تدّعي أنك نفذت شيئاً لم تنفذه فعلياً."

with tab_chat:
    st.subheader("💬 المحادثة الذكية")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    prompt=st.chat_input("اكتبي رسالتك هنا...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                contents=[]
                for msg in st.session_state.messages:
                    role="user" if msg["role"]=="user" else "model"
                    contents.append(types.Content(role=role,parts=[types.Part(text=msg["content"])]))
                instruction=SYSTEM
                if language=="العربية": instruction+="\nاستخدم العربية."
                elif language=="English": instruction+="\nUse English."
                response=client.models.generate_content(model="gemini-3.8-flash",contents=contents,config=types.GenerateContentConfig(temperature=temperature,system_instruction=instruction))
                answer=response.text or "لم يصل رد."
                st.markdown(answer)
                st.session_state.messages.append({"role":"assistant","content":answer})
            except Exception as e: st.error(f"حدث خطأ: {e}")

with tab_files:
    st.subheader("📎 تحليل الملفات")
    uploaded=st.file_uploader("ارفع ملفاً",type=["pdf","png","jpg","jpeg","webp","txt","csv","mp3","wav","m4a","mp4","mov","webm"],key="general_file")
    if uploaded:
        st.success(f"تم اختيار: {uploaded.name}")
        prompt=st.text_area("ماذا تريد من الملف؟","حلل الملف واشرح أهم المعلومات الموجودة فيه.")
        if st.button("🧠 تحليل الملف",type="primary",use_container_width=True):
            path=None
            try:
                with tempfile.NamedTemporaryFile(delete=False,suffix=Path(uploaded.name).suffix) as f:
                    f.write(uploaded.getbuffer()); path=f.name
                gf=client.files.upload(file=path)
                response=client.models.generate_content(model="gemini-3.8-flash",contents=[prompt,gf])
                st.markdown("### النتيجة"); st.markdown(response.text or "لم يصل رد.")
            except Exception as e: st.error(f"تعذر تحليل الملف: {e}")
            finally:
                if path:
                    try: os.remove(path)
                    except OSError: pass

with tab_image:
    st.subheader("🖼️ توليد الصور")
    image_prompt=st.text_area("اكتب وصف الصورة",placeholder="مثال: مدينة سعودية مستقبلية، درون توصيل، أسلوب سينمائي واقعي...")
    aspect=st.selectbox("نسبة الصورة",["1:1","16:9","9:16","4:3","3:4"])
    if st.button("🎨 إنشاء الصورة",type="primary",use_container_width=True):
        if not image_prompt.strip(): st.warning("اكتب وصف الصورة أولاً.")
        else:
            with st.spinner("🎨 جاري إنشاء الصورة..."):
                try:
                    response=client.models.generate_content(model="gemini-3.1-flash-image",contents=image_prompt,config=types.GenerateContentConfig(response_modalities=["IMAGE"],response_format={"image":{"aspect_ratio":aspect}}))
                    found=False
                    for part in response.parts:
                        if part.inline_data is not None:
                            st.image(part.as_image(),use_container_width=True); found=True
                    if not found: st.warning("لم يتم إرجاع صورة.")
                except Exception as e: st.error(f"تعذر إنشاء الصورة: {e}")

with tab_audio:
    st.subheader("🎙️ تحليل الصوت")
    audio=st.file_uploader("ارفع تسجيلًا صوتيًا",type=["mp3","wav","m4a","ogg"],key="audio_file")
    if audio:
        st.audio(audio)
        prompt=st.text_area("المطلوب","فرغ الكلام الموجود في التسجيل ثم لخص أهم النقاط.",key="audio_prompt")
        if st.button("🎙️ تحليل الصوت",type="primary",use_container_width=True):
            path=None
            try:
                with tempfile.NamedTemporaryFile(delete=False,suffix=Path(audio.name).suffix) as f:
                    f.write(audio.getbuffer()); path=f.name
                af=client.files.upload(file=path)
                response=client.models.generate_content(model="gemini-3.8-flash",contents=[prompt,af])
                st.markdown("### 📝 النتيجة"); st.markdown(response.text or "لم يصل رد.")
            except Exception as e: st.error(f"تعذر تحليل الصوت: {e}")
            finally:
                if path:
                    try: os.remove(path)
                    except OSError: pass

with tab_video:
    st.subheader("🎬 تحليل الفيديو")
    video=st.file_uploader("ارفع فيديو",type=["mp4","mov","avi","webm"],key="video_file")
    if video:
        st.video(video)
        prompt=st.text_area("المطلوب","حلل الفيديو، صف أهم المشاهد، واكتب ملخصاً احترافياً.",key="video_prompt")
        if st.button("🎬 تحليل الفيديو",type="primary",use_container_width=True):
            path=None
            try:
                with tempfile.NamedTemporaryFile(delete=False,suffix=Path(video.name).suffix) as f:
                    f.write(video.getbuffer()); path=f.name
                vf=client.files.upload(file=path)
                response=client.models.generate_content(model="gemini-3.8-flash",contents=[prompt,vf])
                st.markdown("### 🎬 النتيجة"); st.markdown(response.text or "لم يصل رد.")
            except Exception as e: st.error(f"تعذر تحليل الفيديو: {e}")
            finally:
                if path:
                    try: os.remove(path)
                    except OSError: pass

st.divider()
st.caption("🤖 My AI Platform · Powered by Gemini")

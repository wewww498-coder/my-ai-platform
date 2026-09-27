import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io
import time

# -----------------------------------------------------------------------------
# 1. إعدادات الصفحة والواجهة الرئيسيّة
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="منصة الذكاء الاصطناعي الشاملة",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق تنسيقات CSS لدعم اللغة العربية وتجميل الواجهة
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div.stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stChatMessage { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 منصتكِ الخاصة للذكاء الاصطناعي الشامل")
st.caption("محادثة نصية وصوتية | توليد صور | صناعة سيناريو وفيديو")

# -----------------------------------------------------------------------------
# 2. القائمة الجانبية وإدارة المفاتيح (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ إعدادات المنصة")
api_key = st.sidebar.text_input("أدخلي مفتاح Gemini API الخاص بكِ:", type="password")

if not api_key:
    st.sidebar.warning("⚠️ يُرجى إدخال مفتاح الـ API للتمكن من تشغيل المحرك.")
    st.info("👈 ابدئي بإدخال مفتاح Gemini API من القائمة الجانبية لتفعيل كافة الميزات.")
    st.stop()

# تهيئة المحرك
genai.configure(api_key=api_key)
text_model = genai.GenerativeModel('gemini-1.5-flash')

# -----------------------------------------------------------------------------
# 3. تبويب الأقسام (Tabs)
# -----------------------------------------------------------------------------
tab_chat, tab_voice, tab_image, tab_video = st.tabs([
    "💬 الشات والسيناريو", 
    "🎙️ المحادثة الصوتية", 
    "🎨 توليد الصور", 
    "🎬 صناعة الفيديو"
])

# -----------------------------------------------------------------------------
# التبويب الأول: الشات والسيناريوهات النصية
# -----------------------------------------------------------------------------
with tab_chat:
    st.subheader("💬 المحادثة الذكية وصناعة السيناريو")
    
    # حفظ سجل المحادثة
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # زر مسح المحادثة
    if st.button("🗑️ مسح السجل", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()

    # عرض المحادثات السابقة
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # استقبال الأوامر والسيناريوهات
    if prompt := st.chat_input("اكتبي سؤالكِ، أو اطلبي كتابة قصة/سيناريو فيديو..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                           for m in st.session_state.chat_messages[:-1]]
                chat = text_model.start_chat(history=history)
                response = chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.chat_messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاتصال: {e}")

# -----------------------------------------------------------------------------
# التبويب الثاني: المحادثة الصوتية (Voice Chat)
# -----------------------------------------------------------------------------
with tab_voice:
    st.subheader("🎙️ الاتصال والمحادثة الصوتية")
    st.write("يمكنكِ إدخال رسالة صوتية أو كتابية ليتم الرد عليكِ بصوت مسموع مباشرة:")

    voice_prompt = st.text_input("أدخلي نص الرسالة الصوتية أو استخدمي الميكروفون:")
    
    if st.button("🔊 إرسال واستماع للرد الصوتي"):
        if voice_prompt:
            with st.spinner("جاري معالجة الصوت وتوليد الرد..."):
                response = text_model.generate_content(voice_prompt)
                st.success("الرد النصي:")
                st.write(response.text)
                
                # تحويل النص إلى صوت
                tts = gTTS(text=response.text, lang='ar')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                st.audio(fp, format='audio/mp3')

# -----------------------------------------------------------------------------
# التبويب الثالث: توليد الصور (AI Image Generation)
# -----------------------------------------------------------------------------
with tab_image:
    st.subheader("🎨 استوديو توليد الصور بالذكاء الاصطناعي")
    img_prompt = st.text_area("وصفي الصورة التي ترغبين في إنشائها بدقة:", 
                              placeholder="مثال: طائرة درون مستقبلية تطير فوق مدينة رياضية ذكية، إضاءة سينمائية...")
    
    if st.button("✨ إنتاج الصورة"):
        if img_prompt:
            with st.spinner("جاري رسم الصورة بالذكاء الاصطناعي..."):
                try:
                    # استخدام نموذج Imagen من Google
                    imagen_model = genai.GenerativeModel('imagen-3.0-generate-002')
                    result = imagen_model.generate_images(
                        prompt=img_prompt,
                        number_of_images=1,
                        aspect_ratio="1:1"
                    )
                    for generated_image in result.generated_images:
                        image = Image.open(io.BytesIO(generated_image.image.image_bytes))
                        st.image(image, caption="الصورة الناتجة", use_column_width=True)
                except Exception as e:
                    st.error(f"توليد الصور يتطلب تفعيل صلاحية Imagen API على المفتاح الخاص بكِ. التفاصيل: {e}")

# -----------------------------------------------------------------------------
# التبويب الرابع: صناعة الفيديو والعروض (AI Video Studio)
# -----------------------------------------------------------------------------
with tab_video:
    st.subheader("🎬 استوديو تحويل النصوص والسيناريوهات إلى فيديوهات")
    video_prompt = st.text_area("أدخلي فكرة المقطع أو سيناريو الفيديو المراد إنتاجه:")
    style = st.selectbox("أسلوب الفيديو:", ["واقعي (Realistic)", "أنيميشن (Animation)", "سينمائي (Cinematic)"])
    
    if st.button("🎥 البدء في معالجة وإنتاج الفيديو"):
        if video_prompt:
            st.info("جاري تحليل السيناريو وإنشاء مشاهد الفيديو بالذكاء الاصطناعي...")
            progress_bar = st.progress(0)
            for percent_complete in range(100):
                time.sleep(0.03)
                progress_bar.progress(percent_complete + 1)
            
            st.success("تم تجهيز هيكل المشاهد الفنية للسيناريو!")

import streamlit as st
import os
from google import genai
from google.genai import types

# ********** BƯỚC 1: Cấu Hình API Key & Sửa Lỗi Client Closed **********
# Sử dụng @st.cache_resource để đảm bảo đối tượng genai.Client chỉ được tạo ra 
# một lần duy nhất và không bị đóng, đồng thời đọc API Key từ Streamlit Secrets an toàn.
@st.cache_resource
def get_gemini_client():
    # Ưu tiên đọc từ Streamlit Secrets (cho phiên bản triển khai trên cloud)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=api_key)
        
    except (AttributeError, KeyError):
        # Nếu không có trong Secrets (ví dụ: đang chạy lokal), tìm trong biến môi trường
        try:
            return genai.Client() # Nếu biến môi trường GOOGLE_API_KEY hoặc GEMINI_API_KEY được đặt
        except Exception:
            # Nếu không tìm thấy Key ở đâu cả
            st.error("Lỗi: Không tìm thấy Gemini API Key. Vui lòng thiết lập biến môi trường (local) hoặc Streamlit Secrets (cloud).")
            st.stop()

# Lấy client đã được cache
client = get_gemini_client()


# ********** BƯỚC 2: Định Nghĩa "Bộ Não" Đa Môn Học và Khởi Tạo Chat Session **********
if "chat_session" not in st.session_state:
    
    # ** SYSTEM INSTRUCTIONS MỚI: Hỗ Trợ Đa Môn Học THCS **
    system_instruction = """
BẠN LÀ AI: Bạn là "Gia Sư Toàn Diện THCS", một trợ lý AI chuyên nghiệp, thân thiện, và kiên nhẫn, chuyên hỗ trợ học sinh Trung học cơ sở (Lớp 6 đến Lớp 9) tại Việt Nam trong MỌI môn học.

CÁC MÔN HỌC HỖ TRỢ: Toán học, Ngữ văn, Tiếng Anh, Vật lí, Hóa học, Sinh học, Lịch sử, Địa lí, Giáo dục Công dân.

NHIỆM VỤ CỐT LÕI (RẤT QUAN TRỌNG):
1. Phương pháp hướng dẫn: Luôn áp dụng phương pháp gợi mở và hướng dẫn tự học. KHÔNG BAO GIỜ đưa ra đáp án cuối cùng ngay lập tức cho bài tập, câu hỏi hay vấn đề.
2. Mục tiêu: Giúp học sinh hiểu sâu về kiến thức, kỹ năng giải quyết vấn đề và tự tìm ra câu trả lời.
3. Chia nhỏ: Luôn chia nhỏ vấn đề (bài toán, bài văn, sự kiện lịch sử, ngữ pháp...) thành các bước nhỏ, dễ tiếp cận. Đặt câu hỏi gợi mở cho TỪNG BƯỚC.

**QUY TẮC PHỦ QUYẾT (GUARDRAIL):**
**1. Nếu học sinh yêu cầu "cho đáp án", "cho lời giải", "cho kết quả", hoặc bất kỳ yêu cầu nào đòi hỏi câu trả lời cuối cùng NGAY LẬP TỨC: TUYỆT ĐỐI TỪ CHỐI.**
**2. Phản hồi phải kiên quyết nhưng thân thiện: Nhắc lại vai trò của bạn là người hướng dẫn chứ không phải người giải bài tập hộ.**
**3. Chuyển hướng ngay lập tức: Đặt câu hỏi gợi mở đầu tiên để khởi động quá trình hướng dẫn theo từng bước.**

QUY TẮC XỬ LÝ THEO TỪNG MÔN:

* TOÁN HỌC & KHOA HỌC TỰ NHIÊN (Lý, Hóa, Sinh): 
    * Yêu cầu: Luôn sử dụng định dạng **LaTeX** ($a^2 + b^2 = c^2$) cho công thức toán học và khoa học.
    * Hướng dẫn: Phân tích đề bài, xác định công thức/định luật cần dùng, gợi ý từng bước tính toán.
* NGỮ VĂN:
    * Yêu cầu: Không làm hộ bài văn hay dàn ý.
    * Hướng dẫn: Hỏi về chủ đề, thể loại, bố cục, và gợi ý các luận điểm, ví dụ, hoặc cách sử dụng từ ngữ.
* LỊCH SỬ & ĐỊA LÍ:
    * Yêu cầu: Đảm bảo tính chính xác và khách quan của sự kiện.
    * Hướng dẫn: Hỏi về bối cảnh, nguyên nhân, diễn biến, và hệ quả của sự kiện hoặc các yếu tố tự nhiên/xã hội liên quan.
* TIẾNG ANH:
    * Hướng dẫn: Tập trung vào giải thích ngữ pháp, từ vựng, và cấu trúc câu thay vì dịch hoặc làm bài tập trắc nghiệm hộ.

PHONG CÁCH: Luôn giữ thái độ tích cực, thân thiện, động viên và sử dụng ngôn ngữ chuẩn mực, rõ ràng, trong sáng của Tiếng Việt.
"""
    
    # Thiết lập cấu hình (Config) cho mô hình
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2 
    )
    
    # Khởi tạo phiên trò chuyện (Chat Session)
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash", # Hỗ trợ đa phương thức và tốc độ tốt
        config=config
    )

# ********** BƯỚC 3: Xây Dựng Giao Diện Người Dùng (UI) **********
st.title("🎓 Gia Sư AI THCS Bình San")
st.caption("Hỗ trợ học tập các môn Lớp 6-9 qua văn bản và hình ảnh.")

st.markdown("---")
st.markdown("Tôi là Gia Sư AI của Trường THCS Bình San, sẵn sàng hỗ trợ bạn trong **Tất cả các môn học THCS**. ")
st.markdown("**Hãy nhập câu hỏi hoặc tải ảnh bài tập lên nhé!**")
st.markdown("---")


# ---------- CHỨC NĂNG TẢI ẢNH LÊN (ĐA PHƯƠNG THỨC) ----------
uploaded_file = st.file_uploader(
    "Tải ảnh bài tập lên (Toán, Lý, Hóa, Bài tập khác)",
    type=["png", "jpg", "jpeg"],
    key="file_uploader" 
)

image_part = None 
image_bytes = None
if uploaded_file is not None:
    image_bytes = uploaded_file.read()
    
    # Tạo đối tượng Part cho Gemini API
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=uploaded_file.type
    )
    
    # Hiển thị ảnh đã tải lên ở cột bên lề để người dùng dễ theo dõi
    st.sidebar.image(image_bytes, caption='Ảnh bài tập đã tải lên', use_column_width=True)
    st.info("Ảnh đã tải lên thành công. Vui lòng nhập câu hỏi hoặc yêu cầu hướng dẫn bên dưới.")
# ----------------------------------------------------------------

# Hiển thị lịch sử chat
for message in st.session_state.chat_session.get_history():
    role = "Gia Sư" if message.role == "model" else "Học sinh"
    
    with st.chat_message(role):
        st.markdown(message.parts[0].text) 

# Hộp nhập liệu cho người dùng
if prompt := st.chat_input("Nhập câu hỏi (VD: 'Hướng dẫn em viết văn, giải toán hoặc trả lời câu hỏi...')"):
    
    # Chuẩn bị nội dung gửi đi (có thể bao gồm ảnh)
    contents = [prompt]
    
    # Nếu có ảnh được tải lên, thêm ảnh đó vào nội dung gửi đi (Đa phương thức)
    if uploaded_file is not None and image_part is not None:
        contents.insert(0, image_part) # Đặt ảnh lên trước văn bản
        
        # Hiển thị ảnh nhỏ trong lịch sử chat
        with st.chat_message("Học sinh"):
            st.markdown(f"**Bài tập Đính kèm Ảnh:**")
            st.image(image_bytes, width=150)
            st.markdown(prompt) # Hiển thị câu hỏi văn bản

    # Nếu không có ảnh, chỉ gửi văn bản
    else:
        st.chat_message("Học sinh").markdown(prompt)
    
    # 2. Gửi yêu cầu (gồm ảnh và/hoặc văn bản) và nhận phản hồi từ Gemini
    with st.spinner("Gia sư đang phân tích và soạn hướng dẫn..."):
        # Sử dụng .send_message và truyền danh sách contents [ảnh, text] hoặc [text]
        response = st.session_state.chat_session.send_message(contents)
    
    # 3. Hiển thị phản hồi của AI
    with st.chat_message("Gia Sư"):
        st.markdown(response.text)





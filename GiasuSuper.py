import streamlit as st
import os
from google import genai
from google.genai import types

# ********** BƯỚC 1: Cấu Hình API Key & Sửa Lỗi Client Closed **********
@st.cache_resource
def get_gemini_client():
    # Ưu tiên đọc từ Streamlit Secrets (cho phiên bản triển khai trên cloud)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=api_key)
        
    except (AttributeError, KeyError):
        # Nếu không có trong Secrets (ví dụ: đang chạy lokal), tìm trong biến môi trường
        try:
            return genai.Client()
        except Exception:
            st.error("Lỗi: Không tìm thấy Gemini API Key. Vui lòng thiết lập biến môi trường (local) hoặc Streamlit Secrets (cloud).")
            st.stop()

# Lấy client đã được cache
client = get_gemini_client()


# ********** BƯỚC 2: Định Nghĩa "Bộ Não" Đa Môn Học và Khởi Tạo Chat Session **********
if "chat_session" not in st.session_state:
    
    # ** SYSTEM INSTRUCTIONS: Gia Sư Toàn Diện THCS **
    system_instruction = """
BẠN LÀ AI: Bạn là "Gia Sư Toàn Diện THCS", một trợ lý AI chuyên nghiệp, thân thiện, và kiên nhẫn, chuyên hỗ trợ học sinh Trung học cơ sở (Lớp 6 đến Lớp 9) tại Việt Nam trong MỌI môn học.

CÁC MÔN HỌC HỖ TRỢ: Toán học, Ngữ văn, Tiếng Anh, Vật lí, Hóa học, Sinh học, Lịch sử, Địa lí, Giáo dục Công dân.

NHIỆM VỤ CỐT LÕI (RẤT QUAN TRỌNG):
1. Phương pháp hướng dẫn: Luôn áp dụng phương pháp gợi mở và hướng dẫn tự học. KHÔNG BAO GIỜ đưa ra đáp án cuối cùng ngay lập tức cho bài tập, câu hỏi hay vấn đề.
2. Mục tiêu: Giúp học sinh hiểu sâu về kiến thức, kỹ năng giải quyết vấn đề và tự tìm ra câu trả lời.
3. Chia nhỏ: Luôn chia nhỏ vấn đề (bài toán, bài văn, sự kiện lịch sử, ngữ pháp...) thành các bước nhỏ, dễ tiếp cận. Đặt câu hỏi gợi mở cho TỪNG BƯỚC.

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

PHONG CÁCH: Luôn giữ thái độ tích cực, thân thiện, động viên và sử dụng ngôn ngữ chuẩn mực, rõ ràng của Tiếng Việt.
"""
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.5 
    )
    
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=config
    )

# ********** BƯỚC 3: Xây Dựng Giao Diện Người Dùng (UI) **********
st.title("🎓 Gia Sư AI - THCS Bình San")
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


# ********** PHẦN ĐÃ SỬA: Gợi Ý Nhập Liệu Tuần Tự **********

# 1. Định nghĩa danh sách các gợi ý (hints)
prompt_hints = [
    "Nhập câu hỏi, VD: Hướng dẫn em giải bài toán phương trình bậc hai.",
    "Nhập câu hỏi, VD: Em cần viết đoạn kết bài văn phân tích nhân vật.",
    "Nhập câu hỏi, VD: Giải thích giúp em cách dùng thì hiện tại hoàn thành trong Tiếng Anh.",
    "Nhập câu hỏi, VD: Tóm tắt giúp em các ý chính về Phong trào Tây Sơn.",
    "Nhập câu hỏi, VD: Công thức tính vận tốc trung bình là gì?"
]

# 2. Khởi tạo hoặc cập nhật chỉ số gợi ý (hint index)
if 'hint_index' not in st.session_state:
    st.session_state.hint_index = 0
else:
    # Tăng chỉ số và dùng toán tử modulo (%) để quay vòng
    st.session_state.hint_index = (st.session_state.hint_index + 1) % len(prompt_hints)

# 3. Lấy gợi ý hiện tại
current_hint = prompt_hints[st.session_state.hint_index]


# Hộp nhập liệu cho người dùng (sử dụng gợi ý động)
if prompt := st.chat_input(current_hint):
    
    # Chuẩn bị nội dung gửi đi (có thể bao gồm ảnh)
    contents = [prompt]
    
    # Xử lý nội dung đa phương thức
    if uploaded_file is not None and image_part is not None:
        contents.insert(0, image_part)
        
        with st.chat_message("Học sinh"):
            st.markdown(f"**Bài tập Đính kèm Ảnh:**")
            st.image(image_bytes, width=150)
            st.markdown(prompt)

    else:
        st.chat_message("Học sinh").markdown(prompt)
    
    # Gửi yêu cầu và nhận phản hồi từ Gemini
    with st.spinner("Gia sư đang phân tích và soạn hướng dẫn..."):
        response = st.session_state.chat_session.send_message(contents)
    
    # Hiển thị phản hồi của AI
    with st.chat_message("Gia Sư"):
        st.markdown(response.text)

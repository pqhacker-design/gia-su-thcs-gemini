import streamlit as st
import os
from google import genai
from google.genai import types

# *** CSS TÙY CHỈNH ĐỂ TẠO FOOTER CỐ ĐỊNH ***
st.markdown("""
<style>
    /* Ẩn footer mặc định của Streamlit (Deploy button, Made with Streamlit) */
    footer {visibility: hidden;}
    
    /* Định nghĩa khu vực footer mới (Bộ đếm) */
    .custom-footer-container {
        position: fixed; /* Cố định vị trí */
        bottom: 0px; /* Nằm ngay sát đáy trình duyệt */
        left: 0;
        width: 100%;
        background-color: white; /* Đảm bảo footer có nền trắng để nổi lên */
        padding: 5px 0;
        z-index: 999999; /* Đảm bảo nó nằm trên tất cả các thành phần khác */
        border-top: 1px solid #f0f2f6; /* Đường phân cách mờ */
        text-align: center;
        font-size: 0.7em;
        color: grey;
    }
</style>
""", unsafe_allow_html=True)
# **********************************************
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
    
    # 1. Định nghĩa System Instruction
    system_instruction = """
BẠN LÀ AI: Bạn là "Gia Sư AI THCS – Trợ lý học tập thông minh cho học sinh cấp 2" chuyên nghiệp, thân thiện, và kiên nhẫn, chuyên hỗ trợ học sinh Trung học cơ sở (Lớp 6 đến Lớp 9) tại Việt Nam trong MỌI môn học.

Mục tiêu: Hướng dẫn học sinh THCS hiểu bài, giải bài tập, ôn luyện và phát triển tư duy ở tất cả các môn học theo chương trình giáo dục phổ thông mới.

1. Phong cách giao tiếp
    Ngôn ngữ thân thiện, gần gũi, dễ hiểu với học sinh cấp 2.
    Khi giải thích, luôn giải từng bước rõ ràng, không chỉ cho đáp án mà phải giúp học sinh hiểu “vì sao ra kết quả đó”.
    Khi cần, có thể đưa ví dụ minh họa, hình dung trực quan hoặc liên hệ thực tế.
    Giọng điệu khích lệ, động viên học sinh (“Em làm rất tốt rồi!”, “Thử nghĩ xem, nếu ta đổi cách làm thì sao nhỉ?”).
    Không dùng thuật ngữ quá phức tạp; nếu buộc phải dùng thì giải nghĩa đơn giản.
    Không phán xét, không nặng nề đạo lý, mà hướng dẫn bằng tình cảm tích cực.
    Không nêu nội dung chính trị, chiến tranh hay phân tích phức tạp.
    *LƯU Ý: Dữ liệu phải lấy theo dữ liệu thực tế theo thời gian thực.

2. Quy tắc xử lý theo từng nhóm môn học
    A. TOÁN HỌC
        Luôn trình bày các bước giải chi tiết, từ việc xác định dữ kiện, lập luận, đến kết quả.
        Nếu học sinh hỏi đáp án, vẫn giải thích cách làm và lý do chọn phương pháp đó.
        Với bài toán có nhiều cách giải, nêu 2 cách khác nhau (nếu có): cách truyền thống và cách ngắn gọn.
        Có thể gợi mở để học sinh tự suy luận bước tiếp theo trước khi cho lời giải đầy đủ.
        Khi bài toán có hình học, mô tả bằng ngôn ngữ dễ hình dung, tránh ký hiệu rối.

    B. VẬT LÝ – HÓA HỌC – SINH HỌC (KHOA HỌC TỰ NHIÊN)
        Giải thích bằng ngôn ngữ đời sống, giúp học sinh liên hệ với hiện tượng thực tế.
        Khi có công thức, giải thích ý nghĩa từng đại lượng và đơn vị đo.
        Với bài tính toán, trình bày: Công thức – Thay số – Tính toán – Kết luận.
        Khuyến khích học sinh hiểu bản chất hiện tượng, không chỉ học thuộc.
        Với thí nghiệm, nêu rõ mục đích, dụng cụ, cách tiến hành và kết quả dự kiến.

    C. NGỮ VĂN
        Khi phân tích văn bản, chú trọng ý chính, cảm xúc và thông điệp.
        Giúp học sinh hiểu nghĩa từng câu, từng hình ảnh, biện pháp tu từ.
        Với bài tập làm văn, hướng dẫn dàn ý 3 phần (Mở bài – Thân bài – Kết bài).
        Có thể gợi ý cách viết sáng tạo, nhưng vẫn đúng trọng tâm đề và độ tuổi.
        Tuyệt đối không viết hộ toàn bộ bài văn, chỉ hướng dẫn, gợi ý và chỉnh sửa.

    D. LỊCH SỬ – ĐỊA LÝ – GIÁO DỤC CÔNG DÂN (KHXH)
        Trình bày sự kiện theo trình tự thời gian dễ nhớ, có thể gợi cách học bằng sơ đồ hoặc mốc.
        Với địa lý, có thể dùng mô tả không gian (“phía Bắc giáp…, phía Nam là…”) hoặc bản đồ tư duy.
        Với GDCD, hướng dẫn học sinh nhận biết đúng – sai, hành vi phù hợp và lý do.
        Trả lời bằng ngôn ngữ tích cực, hướng học sinh đến hành vi tốt đẹp.

    E. TIN HỌC & CÔNG NGHỆ
        Giải thích ngắn gọn, thực hành được.
        Với bài lập trình, trình bày mã nguồn có chú thích rõ từng bước.
        Với bài công nghệ, mô tả quy trình, công cụ, tác dụng thực tế.

    F. TIẾNG ANH
        Giải thích ngữ pháp, từ vựng, và phát âm một cách dễ hiểu.
        Khi học sinh sai, sửa nhẹ nhàng, kèm giải thích lý do sai.
        Có thể gợi bài tập luyện thêm, ví dụ: “Hãy thử đặt 2 câu dùng thì hiện tại hoàn thành.”
        Dịch tiếng Việt – Anh và ngược lại sao cho tự nhiên, đúng ngữ cảnh học sinh.

3. Quy tắc phản hồi bài tập
        Nếu học sinh chỉ gửi đề bài, chatbot phải tự động nhận dạng môn học và dạng bài, sau đó giải thích cách làm.
        Nếu học sinh gửi hình ảnh bài tập, hãy nhận diện nội dung, rồi giải thích tương tự.
        Nếu học sinh sai, không chê, mà chỉ ra lỗi và hướng dẫn cách sửa đúng.
        Khi học sinh cần ôn luyện, có thể tạo bộ câu hỏi trắc nghiệm hoặc tự luận ngắn, kèm lời giải.

4. Phạm vi và giới hạn
        Chỉ hướng dẫn trong phạm vi kiến thức THCS (lớp 6–9).
        Không làm thay hoàn toàn bài kiểm tra hoặc bài thi, chỉ hướng dẫn cách giải.
        Tôn trọng bản quyền sách giáo khoa, không sao chép nguyên văn.
        
5. Vai trò và nhiệm vụ của chatbot
        Là “gia sư đồng hành” giúp học sinh hiểu bài, tự tin học tập.
        Luôn ưu tiên hiểu bản chất hơn học thuộc lòng.
        Có thể tạo bài tập tương tự để học sinh luyện thêm sau khi đã hiểu.
        Có khả năng gợi ý cách học hiệu quả, ghi nhớ lâu.
"""
    
    # 2. Thiết lập cấu hình
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=1 
    )
    
    # 3. Khởi tạo phiên trò chuyện với cơ chế tự động chuyển đổi mô hình (Fallback)
    try:
        # Thử chạy model chính phiên bản mới cao cấp nhất trước
        st.session_state.chat_session = client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )
    except Exception as e:
        # Nếu model chính quá tải (503), tự động chuyển sang model dự phòng ổn định cao
        st.warning("Hệ thống chính đang bận, đang kết nối với phòng gia sư dự phòng...")
        try:
            st.session_state.chat_session = client.chats.create(
                model="gemini-1.5-flash",
                config=config
            )
        except Exception as final_error:
            st.error("Hiện tại tất cả các máy chủ Google đều đang quá tải. Bạn vui lòng tải lại trang (F5) sau ít phút nhé!")
            st.stop()
# ********** BƯỚC 3: Xây Dựng Giao Diện Người Dùng (UI) **********
st.title("🎓 Gia Sư AI - THCS Bình San")
st.caption("Xin chào! Tôi là Gia Sư AI của Trường THCS Bình San, sẵn sàng hỗ trợ bạn trong **Tất cả các môn học THCS**.")

st.markdown("---")
st.markdown("**Hãy nhập câu hỏi hoặc tải ảnh bài tập lên nhé!**")
st.markdown("---")


# ---------- CHỨC NĂNG TẢI ẢNH LÊN (ĐA PHƯƠNG THỨC) ----------
uploaded_file = st.file_uploader(
    "Tải ảnh bài tập lên (Toán, Lý, Hóa, Ngữ Văn, Lịch sử, Địa lý, bài tập khác...)",
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
    st.sidebar.image(image_bytes, caption='Ảnh bài tập đã tải lên', width='stretch')
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
        try:
            # Gửi tin nhắn bình thường
            response = st.session_state.chat_session.send_message(contents)
            
            # 3. Hiển thị phản hồi của AI nếu thành công
            with st.chat_message("Gia Sư"):
                st.markdown(response.text)
                
        except Exception as e:
            # Kiểm tra nếu lỗi do server nghẽn (503 hoặc UNAVAILABLE)
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                st.error("😥 Máy chủ Google hiện tại đang quá tải cục bộ do số lượng truy cập lớn. Gia sư chưa nhận được câu hỏi, bạn vui lòng nhấn nút Gửi hoặc nhập lại câu hỏi sau 10-15 giây nhé!")
            else:
                # Các lỗi client hoặc lỗi khác
                st.error(f"Đã xảy ra lỗi không mong muốn: {e}")
# ********** PHẦN MỚI: BỘ ĐẾM SỐ LƯỢNG TRUY CẬP **********

# Dùng st.divider() để tạo đường phân cách rõ ràng
st.divider()

# ********** PHẦN MỚI: BỘ ĐẾM NẰM CỐ ĐỊNH Ở DƯỚI CÙNG **********

st.markdown(
    f"""
    <div class="custom-footer-container">
        <br>
        Ứng dụng được phát triển bởi Trường THCS Bình San
    </div>
    """,
    unsafe_allow_html=True
)

# ***************************************************************













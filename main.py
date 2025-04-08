import os
import time
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from duckduckgo_search import DDGS
import google.generativeai as genai
from dotenv import load_dotenv
from newspaper import Article  # Thêm thư viện để trích xuất bài báo

# ==== 1. LOAD BIẾN MÔI TRƯỜNG ====
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# ==== 2. VALIDATE ====
if not GOOGLE_API_KEY:
    raise ValueError("❌ Thiếu GOOGLE_API_KEY trong biến môi trường.")
if not EMAIL_SENDER or not EMAIL_PASSWORD or not EMAIL_RECEIVER:
    raise ValueError("❌ Thiếu thông tin email trong biến môi trường.")

# ==== 3. CẤU HÌNH GEMINI ====
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

# ==== 4. TÌM KIẾM WEB VÀ LẤY NỘI DUNG BÀI BÁO ====
def web_search(query, max_results=5):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r["title"],
                "href": r["href"],
                "body": r.get("body", "Không có mô tả")
            })
    return results

# ==== 5. LẤY VÀ PHÂN TÍCH BÀI BÁO ====
def get_article_content(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.text

# ==== 6. TẠO PROMPT VÀ TÓM TẮT ====
def generate_summary(article_content):
    prompt = (
        f"Tôi là một nhà báo AI chuyên nghiệp. Dưới đây là nội dung bài báo. Hãy phân tích kỹ nội dung bài viết và đưa ra tóm tắt chi tiết, "
        f"các yếu tố quan trọng, tác động của sự kiện và kết luận:\n\n{article_content}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# ==== 7. GỬI EMAIL ====
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

    print("✅ Email đã được gửi thành công!")

# ==== 8. AGENT CHẠY HÀNG NGÀY ====
def daily_summary():
    query = "tin tức Việt Nam và thế giới mới nhất hôm nay"
    print("🔍 Đang thu thập tin tức...")
    articles = web_search(query, max_results=3)  # Lấy 5 bài báo
    print("🧠 Đang phân tích và tóm tắt...")

    all_summaries = []
    for article in articles:
        article_content = get_article_content(article["href"])
        summary = generate_summary(article_content)
        all_summaries.append(f"📑 Tiêu đề: {article['title']}\n{summary}\n\n")

    full_email = (
        f"📅 BẢN TIN SÁNG TỰ ĐỘNG - {time.strftime('%d/%m/%Y')}\n\n"
        + "\n".join(all_summaries)  # Kết hợp tất cả các bản tin
        + "🤖 Bản tin được tạo bởi AI Agent tự động mỗi sáng."
    )
    send_email("📰 Bản tin sáng AI Agent", full_email)

# ==== 9. LỊCH CHẠY ====
schedule.every().day.at("07:00").do(daily_summary)

print("🤖 AI Agent đã sẵn sàng và sẽ chạy mỗi sáng lúc 7h!")

while True:
    print("⏳ Đang chờ đến giờ chạy...")
    schedule.run_pending()
    time.sleep(60)

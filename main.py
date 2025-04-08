# ai_news_agent/main.py
import os
import time
import schedule
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from duckduckgo_search import DDGS
import google.generativeai as genai

# ==== LẤY API KEY VÀ EMAIL TỪ BIẾN MÔI TRƯỜNG ====
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# ==== CẤU HÌNH GEMINI ====
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# ==== TÌM KIẾM WEB ====
def web_search(query):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            results.append(f"- {r['title']}\n{r['href']}\n")
    return "\n".join(results)

# ==== TẠO BẢN TÓM TẮT ====
def generate_summary(content):
    prompt = f"Tóm tắt và diễn giải nội dung sau thành bản tin dễ hiểu:\n{content}"
    response = model.generate_content(prompt)
    return response.text

# ==== GỬI EMAIL ====
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print("📧 Đã gửi email thành công!")

# ==== AGENT TỰ ĐỘNG HÓA ====
def daily_summary():
    query = "tin tức mới nhất trong ngày"
    print("🔍 Đang tìm tin tức...")
    content = web_search(query)
    print("🧠 Đang tạo bản tóm tắt...")
    summary = generate_summary(content)
    send_email("📰 Bản tin sáng AI Agent", summary)

# ==== LỊCH TRÌNH TỰ ĐỘNG ====
daily_summary()
schedule.every().day.at("07:00").do(daily_summary)

print("🤖 AI Agent đã sẵn sàng và sẽ chạy tự động mỗi sáng lúc 7h...")

while True:
    print("Đang chạyyy.... !!! ")
    schedule.run_pending()
    time.sleep(60)

import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time

# Khởi tạo Firebase Admin SDK
cred = credentials.Certificate("firebase_service_account.json")  # Đảm bảo tệp .json nằm cùng thư mục với file Python
firebase_admin.initialize_app(cred)

# Khởi tạo Firestore client
db = firestore.client()

# Đường dẫn tới ChromeDriver
CHROMEDRIVER_PATH = r'F:\Web Crawl data\chromedriver.exe'  # Đảm bảo đường dẫn chính xác đến chromedriver của bạn

# Tạo driver Chrome
def create_driver():
    options = Options()
    options.add_argument("--headless")  # Chạy ở chế độ ẩn
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

# Hàm lọc số điện thoại (bắt đầu từ số 0)
def extract_phone_number(text):
    phone_pattern = re.compile(r'\b0\d{1,2}[-.\s]?\d{3}[-.\s]?\d{3,4}\b')
    phone_numbers = phone_pattern.findall(text)
    return phone_numbers if phone_numbers else None

# Hàm lưu dữ liệu vào Firebase Firestore
def save_to_firebase(data):
    doc_ref = db.collection("web_data").add(data)
    print("\n📤 Dữ liệu đã được lưu vào Firebase.")

# Hàm lấy thông tin trang web
def auto_extract_content(url):
    driver = create_driver()
    driver.get(url)
    time.sleep(3)  # Chờ một chút cho trang web tải xong

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # 1. Lấy tiêu đề trang
    title = soup.title.get_text(strip=True) if soup.title else "Không tìm thấy tiêu đề"
    print(f"\n🎯 Tiêu đề trang: {title}")

    # 2. Lấy tất cả các link (URLs) trên trang
    links = soup.find_all("a", href=True)
    link_list = [link['href'] for link in links]

    # 3. Lọc nội dung chính của trang (thường là các article, section, main, div, p...)
    main_content = soup.find_all(["article", "section", "main", "div", "p"])
    content_list = []
    for block in main_content:
        text = block.get_text(strip=True, separator=" ")
        if text and len(text) > 100:  # Chỉ lấy các đoạn văn dài hơn 100 ký tự
            content_list.append(text)

    # 4. Lọc số điện thoại nếu có
    phone_numbers = extract_phone_number(soup.get_text())

    # 5. Xác định loại trang web (Ví dụ: bán điện thoại, dịch vụ, tin tức...)
    web_type = "Chưa rõ loại"
    if "phone" in title.lower() or "mobile" in title.lower():
        web_type = "Trang web bán điện thoại"
    elif "shop" in title.lower() or "store" in title.lower():
        web_type = "Trang web mua sắm"
    elif "news" in title.lower():
        web_type = "Trang web tin tức"

    # Tạo dữ liệu để lưu vào Firebase
    data = {
        "title": title,
        "url": url,
        "links": link_list,
        "main_content": content_list,
        "phone_numbers": phone_numbers if phone_numbers else None,
        "web_type": web_type
    }

    # Lưu dữ liệu vào Firebase
    save_to_firebase(data)

if __name__ == "__main__":
    url = input("🌐 Nhập URL trang web: ")
    auto_extract_content(url)

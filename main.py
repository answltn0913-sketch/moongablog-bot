import os
import json
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
import google.generativeai as genai

GEMINI_API_KEY = (os.environ.get("GEMINI_KEY") or os.environ.get("GEMINI_API_KEY", "")).strip()
EMAIL_SENDER = "answltn0913@gmail.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = "answltn0913@gmail.com"

CATEGORY_QUERIES = [
    ("지원금·금융", "정부지원금 OR 정책금융 OR 청년지원금 OR 서민금융"),
    ("경제·재테크", "금리인하 OR 한국은행 OR 부동산대책 OR 세제개편안"),
    ("IT·테크", "인공지능 OR 챗봇 OR 스마트폰 OR 생성형AI"),
    ("부동산", "부동산정책 OR 청약 OR 아파트시세 OR 전세사기대책")
]

def fetch_current_hot_trend():
    shuffled_sources = CATEGORY_QUERIES.copy()
    random.shuffle(shuffled_sources)
    for cat_name, query in shuffled_sources:
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as res:
                xml_data = res.read().decode('utf-8')
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                candidates = []
                for item in items[:15]:
                    title_elem = item.find('title')
                    if title_elem is not None and title_elem.text:
                        clean_title = title_elem.text.split(' - ')[0].strip()
                        if len(clean_title) > 8 and not clean_title.lower().startswith("fotmob"):
                            candidates.append(clean_title)
                if candidates:
                    return cat_name, random.choice(candidates)
        except Exception:
            continue
    return "지원금·금융", "2026 하반기 서민 가계 고정비 절감 및 정부 긴급 금융 지원 정책 총정리"

def generate_expert_package(category: str, topic: str) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_KEY가 설정되지 않았습니다.")

    genai.configure(api_key=GEMINI_API_KEY)

    prompt = f"""
    당신은 대한민국 최상위 블로그 콘텐츠 전문가입니다.
    분야: [{category}], 주제: '{topic}'

    - 100% 팩트 기반 검증 내용 작성
    - 쉬운 눈높이와 1~2줄 단위 줄바꿈

    반드시 아래 순수 JSON 포맷으로만 응답하세요:
    {{
      "naver_title": "네이버 블로그 제목",
      "naver_body": "네이버 블로그 본문 (1~2줄 분절)",
      "naver_tags": "#태그1 #태그2 #태그3 #태그4 #태그5 #태그6 #태그7 #태그8 #태그9 #태그10",
      "tistory_title": "티스토리/워드프레스 제목",
      "tistory_html": "완성형 HTML 본문",
      "tistory_tags": "#태그1 #태그2 #태그3 #태그4 #태그5 #태그6 #태그7 #태그8 #태그9 #태그10",
      "wordpress_tags": "태그1, 태그2, 태그3, 태그4, 태그5, 태그6, 태그7, 태그8, 태그9, 태그10"
    }}
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )

    response = model.generate_content(prompt)
    raw = response.text.strip()
    if "{" in raw and "}" in raw:
        raw = raw[raw.find("{"):raw.rfind("}")+1]
    return json.loads(raw)

def main():
    category, topic = fetch_current_hot_trend()
    print(f"🔥 [{category}] 팩트 기반 원고 생성 시작: {topic}")
    post = generate_expert_package(category, topic)

    mail_body = f"""================================================================================
문가장의 지식 네비게이션 원고 패키지
[카테고리: {category}]
주제: {topic}
================================================================================

[MODE 1] 네이버 블로그 전용
--------------------------------------------------------------------------------
[제목] {post.get('naver_title')}

[본문]
{post.get('naver_body')}

[태그] {post.get('naver_tags')}


[MODE 2] 티스토리 & 워드프레스 전용
--------------------------------------------------------------------------------
[제목] {post.get('tistory_title')}

[HTML 본문]
{post.get('tistory_html')}

[태그] {post.get('tistory_tags')}
"""

    msg = MIMEMultipart()
    msg['Subject'] = Header(f"[{category}] [팩트체크 원고] {post.get('naver_title', topic)}", 'utf-8')
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    part = MIMEText(mail_body, 'plain', 'utf-8')
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, local_hostname='localhost') as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    print(f"🎉 메일 발송 완료!")

if __name__ == "__main__":
    main()

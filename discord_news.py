import feedparser
import requests
import json
import os
from datetime import datetime

# 1. 설정: GitHub Actions의 'env' 설정과 이름을 맞췄습니다.
DISCORD_WEBHOOK_URL = os.environ.get('NEWSBOTG') 
RSS_URLS = [
    "https://news.google.com/rss/search?q=급등+상한가+공시&hl=ko&gl=KR", # 국내
    "https://search.cnbc.com/rs/search/combined/all/rss.xml",           # 해외(CNBC)
    "https://finance.yahoo.com/news/rssindex"                         # 해외(Yahoo)
]
DB_FILE = "sent_links.txt"

# 2. 키워드별 색상 매핑 (광범위 매크로 버전)
KEYWORD_COLORS = {
    # 🔴 매크로 및 긴급
    "FED": 15548997, 
    "CPI": 15548997,
    "INFLATION": 15548997,
    "INTEREST RATE": 15548997,
    
    # 🟡 기업 실적 및 공시
    "EARNINGS": 16776960,
    "REVENUE": 16776960,
    "GUIDANCE": 16776960,
    "M&A": 16776960,
    
    # 🟢 시장 지수 및 테마
    "NASDAQ": 5763719,
    "S&P 500": 5763719,
    "RALLY": 5763719,
    "BREAKOUT": 5763719,
    
    # 🔵 섹터 뉴스
    "BIG TECH": 3447003,
    "AI": 3447003,
    "SEMICONDUCTOR": 3447003
}

def load_sent_links():
    """이미 보낸 뉴스 기록을 불러옴"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_sent_link(link):
    """새로 보낸 뉴스 기록을 저장"""
    with open(DB_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def send_to_discord(entry, color, keyword):
    """디스코드 임베드 형식으로 전송"""
    if not DISCORD_WEBHOOK_URL:
        return

    # 날짜 정보가 없는 경우 처리
    pub_date = getattr(entry, 'published', '날짜 정보 없음')

    payload = {
        "embeds": [{
            "title": f"[{keyword}] {entry.title}",
            "url": entry.link,
            "description": f"📅 {pub_date}",
            "color": color,
            "footer": {"text": "실시간 글로벌 증시 큐레이션 by 재우"}
        }]
    }
    
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print(f"✅ 전송 성공: {entry.title[:20]}...")
    else:
        print(f"❌ 전송 실패: {res.status_code}")

def run_bot():
    print(f"🚀 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 스캔 시작...")
    
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK(NEWSBOTG) 환경 변수를 찾을 수 없습니다.")
        return

    sent_links = load_sent_links()
    new_news_count = 0

    # 리스트에 담긴 모든 RSS URL을 순회합니다.
    for rss_url in RSS_URLS:
        try:
            feed = feedparser.parse(rss_url)
            # 각 피드에서 최신 뉴스 30개씩 확인
            for entry in feed.entries[:30]:
                if entry.link not in sent_links:
                    # 제목을 대문자로 변환하여 키워드 매칭 (대소문자 무시)
                    upper_title = entry.title.upper()
                    found_keyword = next((kw for kw in KEYWORD_COLORS if kw in upper_title), None)
                    
                    if found_keyword:
                        target_color = KEYWORD_COLORS[found_keyword]
                        send_to_discord(entry, target_color, found_keyword)
                        save_sent_link(entry.link)
                        sent_links.add(entry.link) # 중복 방지 즉시 반영
                        new_news_count += 1
        except Exception as e:
            print(f"❌ {rss_url} 스캔 중 오류 발생: {e}")
    
    print(f"🏁 작업 완료. 새로 전송된 뉴스: {new_news_count}개")

if __name__ == "__main__":
    run_bot()

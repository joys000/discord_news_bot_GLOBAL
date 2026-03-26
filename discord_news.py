import feedparser
import requests
import json
import os
from datetime import datetime

# 1. 설정: GitHub Actions의 'env' 설정과 이름을 맞췄습니다.
DISCORD_WEBHOOK_URL = os.environ.get('NEWSBOT') 
RSS_URL = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
DB_FILE = "sent_links.txt"

# 2. 키워드별 색상 매핑 (10진수 색상 코드)
# 팁: 나중에 키워드를 추가하려면 아래 리스트에 똑같이 적으세요.
# 더 민감하고 수익에 직결되는 키워드들입니다.
KEYWORD_COLORS = {
    "상한가": 15548997,   # 강렬한 빨강
    "공시": 16776960,     # 노랑 (중요 정보)
    "영업이익": 16776960,
    "흑자전환": 5763719,   # 녹색 (호재)
    "최대주주": 10181046,  # 보라 (지분 변동)
    "급등": 15548997,
    "폭락": 2303786,
    "나스닥": 5763719,
    "코스피": 3447003,
    "특징주": 10181046,   # 보라 (시장 관심주)
    "뉴스": 3447003       # (테스트용: 알림이 잘 오는지 확인 후 삭제하세요)
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
        print("❌ 에러: 웹훅 주소가 없습니다.")
        return

    payload = {
        "embeds": [{
            "title": f"[{keyword}] {entry.title}",
            "url": entry.link,
            "description": f"📅 {entry.published}",
            "color": color,
            "footer": {"text": "실시간 주식 뉴스 큐레이션"}
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
        print("❌ DISCORD_WEBHOOK 환경 변수를 찾을 수 없습니다.")
        return

    feed = feedparser.parse(RSS_URL)
    sent_links = load_sent_links()
    
    new_news_count = 0
    # 최식 뉴스 50개를 훑으며 키워드 검색
    for entry in feed.entries[:50]:
        if entry.link not in sent_links:
            # 제목에서 키워드 찾기
            found_keyword = next((kw for kw in KEYWORD_COLORS if kw in entry.title), None)
            
            if found_keyword:
                target_color = KEYWORD_COLORS[found_keyword]
                send_to_discord(entry, target_color, found_keyword)
                save_sent_link(entry.link)
                new_news_count += 1
    
    print(f"🏁 작업 완료. 새로 전송된 뉴스: {new_news_count}개")

if __name__ == "__main__":
    run_bot()

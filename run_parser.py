import urllib.request, urllib.error, re, base64, random, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ENCRYPTED_SOURCES = [
    "aHR0cHM6Ly9zYXRleHByZXNzdHYucnUvYXBrL3NldHYubTN1",                                                # satexpresstv.ru
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0RpbW9ub3ZpY2gvVFYvRGltb25vdmljaC9GUkVFL1RW",       # Dimonovich FREE TV
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0lQWTFTSEFSRUQvVmVyb25hVFYvcmVmcy9oZWFkcy9tYWluL1Zlcm9uYVRWLm0zdQ==", # VeronaTV
    "aHR0cDovL3N0cmVhbS5tY3F1YWNrLm5ldC8zNjkvaW5kZXgubTN1OA",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FydGVtLWFydDk5OC9JUFRWcnUvcmVmcy9oZWFkcy9tYWluL2lwdHYxMjYubTN1",     # iptv126.m3u
    "aHR0cHM6Ly9nY2xuay5jb20vbGY0SnRCTGM=",                                                           # gclnk.com
    "aHR0cHM6Ly9pcHR2LW9yZy5naXRodWIuaW8vaXB0di9pbmRleC5tM3U=",                                       # iptv-org index.m3u
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2ZyZWUtaXB0di9pcHR2L21hc3Rlci9jYW5hbHMvcnUubTN1",    # free-iptv russia
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0xhbmVpay9pcHR2L21hc3Rlci9pcHR2Lm0zdQ==",            # Laneik iptv list
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tLzFtcGgvaXB0di9tYWluL2JpZy1pcHR2Lm0zdQ==",            # big-iptv aggregator
    "aHR0cHM6Ly9zbW9sbnAuZ2l0aHViLmlvL0lQVFZydS9JUFRWc3RhYmxlLm0zdTg=",                               # IPTVru Stable Mirror
    "aHR0cHM6Ly9zbW9sbnAuZ2l0aHViLmlvL0lQVFZydS9JUFRWcnUubTN1"                                         # IPTVru Main Mirror
]

FAVORITE_CHANNELS = [
    "моя планета", "кино 1 international", "мосфильм золотая коллекция", "неизвестная планета", 
    "travel adventure", "индийское кино", "Travel Channel", "телепутешествия", "моя стихия", 
    "vf мосфильм", "нтв сериал", "nat geo wild", "viju explore", "discovery", "нтв хит",
    "живая планета", "диалоги о рыбалке", "глазами туриста", "animal planet", "national geographic",
    "дом кино", "родное кино", "любимое кино"
]

# ПРЯМЫЕ СТРИМЫ БЕЗ ОГРАНИЧЕНИЙ ПРОВАЙДЕРОВ
RESERVE_LINKS = {
    "моя планета": {
        "url": "https://viju.su", 
        "tag": '#EXTINF:-1 tvg-id="Moya Planeta" tvg-logo="https://githubusercontent.com",Моя Планета'
    },
    "мосфильм золотая коллекция": {
        "url": "https://footprint.net", 
        "tag": '#EXTINF:-1 tvg-id="Mosfilm Zolotaya Kollektsiya" tvg-logo="https://githubusercontent.com",Мосфильм. Золотая коллекция'
    },
    "телепутешествия": {
        "url": "https://pctv.ru", 
        "tag": '#EXTINF:-1 tvg-id="Teleputeshestviya" tvg-logo="https://teletravel.tv",Телепутешествия'
    },
    "живая планета": {
        "url": "https://viju.su", 
        "tag": '#EXTINF:-1 tvg-id="Zhivaya Planeta" tvg-logo="https://githubusercontent.com",Живая планета'
    },
    "дом кино": {
        "url": "https://cdnvideo.ru", 
        "tag": '#EXTINF:-1 tvg-id="Dom Kino" tvg-logo="https://githubusercontent.com",Дом Кино'
    },
    "родное кино": {
        "url": "https://cdnvideo.ru", 
        "tag": '#EXTINF:-1 tvg-id="Rodnoe Kino" tvg-logo="https://githubusercontent.com",Родное Кино'
    }
}

def decode_url(s):
    try: return base64.b64decode(s.encode("utf-8")).decode("utf-8")
    except: return ""

def clean_string(s): 
    return re.sub(r"[^a-zA-Z0-9а-яёА-ЯЁ]", "", s.lower())

def clean_group_title(tag_line):
    return re.sub(r'\s*group-title="[^"]*"', '', tag_line)

def get_quality_score(c): 
    return 10 if "HD" in str(c).upper() else 0

# УМНЫЙ ФИЛЬТР ЗАГЛУШЕК И ЗАБЛОКИРОВАННЫХ ПОТОКОВ
def is_blocked_stream(url):
    url_lower = url.lower()
    # Отсекаем известные пулы взломанных ресиверов Триколор/НТВ+, которые выдают заглушки
    blocked_patterns = [
        "tricolor", "cinerama", "36e", "56e", "dre", "scrambled", 
        "92.243.", "85.203.", "test-stream", "dummy"
    ]
    for pattern in blocked_patterns:
        if pattern in url_lower:
            return True
    return False

def check_url(url):
    if is_blocked_stream(url):
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r: 
            return r.status == 200
    except: 
        return False

def parse_source(enc_url):
    url = decode_url(enc_url)
    if not url: return []
    res = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            lines = r.read().decode("utf-8", errors="ignore").splitlines()
            cur = ""
            for l in lines:
                l = l.strip()
                if l.startswith("#EXTINF"): cur = l
                elif l.startswith("http") and cur: 
                    res.append((cur, l))
                    cur = ""
    except: 
        pass
    return res

def is_strict_match(fav_clean, cand_clean):
    if fav_clean == cand_clean:
        return True
    for suffix in ["hd", "fhd", "50fps", "orig"]:
        if cand_clean == fav_clean + suffix:
            return True
    return False

def main():
    ssl._create_default_https_context = ssl._create_unverified_context
    all_p = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(parse_source, s) for s in ENCRYPTED_SOURCES]
        for f in as_completed(futures): 
            all_p.extend(f.result())
            
    matched = {}
    fav_c = [clean_string(ch) for ch in FAVORITE_CHANNELS]
    for inf, url in all_p:
        m = re.search(r",([^,\n\r]+)$", inf)
        if m:
            name = m.group(1).strip()
            c_name = clean_string(name)
            if "скораяпомощь" in c_name: 
                continue
            for i, fav in enumerate(fav_c):
                ok = False
                if fav == "нтвсериал" and c_name in ["нтвсериал", "нтвсериалы"]: 
                    ok = True
                elif fav == "телепутешествия" and fav in c_name and not any(x in c_name for x in ["hd2", "world", "международный"]): 
                    ok = True
                elif fav == "discovery" and fav in c_name and "science" not in c_name and "world" not in c_name: 
                    ok = True
                elif fav == "моя стихия" and ("моястихия" in c_name or is_strict_match("морской", c_name)):
                    ok = True
                elif fav not in ["нтвсериал", "телепутешествия", "discovery", "моя стихия"]:
                    ok = is_strict_match(fav, c_name)
                    
                if ok:
                    std = FAVORITE_CHANNELS[i]
                    if std not in matched: matched[std] = []
                    matched[std].append((inf, url)); break
                    
    final = ["#EXTM3U\n"]
    added = set()
    
    for ch in FAVORITE_CHANNELS:
        done = False
        
        # Если для канала прописан железный и чистый CDN-резерв, берем сначала его
        if ch in RESERVE_LINKS:
            r = RESERVE_LINKS[ch]
            if r["url"] not in added and check_url(r["url"]):
                final.append(f"{r['tag']}\n{r['url']}\n")
                added.add(r["url"])
                done = True
                
        # Если резерва нет или он подвел, ищем в общих базах с жестким отсевом заглушек
        if not done and ch in matched:
            matched[ch].sort(key=get_quality_score, reverse=True)
            for inf, url in matched[ch]:
                if url in added: 
                    continue
                if ".m3u" in url.lower() and check_url(url): 
                    clean_inf = clean_group_title(inf)
                    final.append(f"{clean_inf}\n{url}\n")
                    added.add(url)
                    done = True
                    break

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(final)
    print(f"Плейлист пересобран без заглушек! Всего чистых каналов: {len(added)}")

if __name__ == "__main__":
    main()




import urllib.request, urllib.error, re, base64, random, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ENCRYPTED_SOURCES = [
    "aHR0cHM6Ly9zYXRleHByZXNzdHYucnUvYXBrL3NldHYubTN1",                                                # satexpresstv.ru
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0RpbW9ub3ZpY2gvVFYvRGltb25vdmljaC9GUkVFL1RW",       # Dimonovich FREE TV
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0lQWTFTSEFSRUQvVmVyb25hVFYvcmVmcy9oZWFkcy9tYWluL1Zlcm9uYVRWLm0zdQ==", # VeronaTV
    "aHR0cDovL3N0cmVhbS5tY3F1YWNrLm5ldC8zNjkvaW5kZXgubTN1OA",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FydGVtLWFydDk5OC9JUFRWcnUvcmVmcy9oZWFkcy9tYWluL2lwdHYxMjYubTN1",     # iptv126.m3u
    "aHR0cHM6Ly9nY2xuay5jb20vbGY0SnRCTGM=",                                                           # gclnk.com
    "aHR0cHM6Ly9pcHR2LW9yZy5naXRodWIuaW8vaXB0di9pbmRleC5tM3U="                                        # iptv-org index.m3u
]

FAVORITE_CHANNELS = [
    "моя планета", "кино 1 international", "мосфильм золотая коллекция", "неизвестная планета", 
    "travel adventure", "индийское кино", "Travel Channel", "телепутешествия", "моя стихия", 
    "vf мосфильм", "нтв сериал", "nat geo wild", "viju explore", "discovery", "нтв хит"
]

RESERVE_LINKS = {
    "моя планета": {
        "url": "https://beetv.kz", 
        "tag": '#EXTINF:-1 tvg-id="Moya Planeta" tvg-logo="https://githubusercontent.com",Моя Планета'
    },
    "мосфильм золотая коллекция": {
        "url": "http://mcquack.net", 
        "tag": '#EXTINF:-1 tvg-id="Mosfilm Zolotaya Kollektsiya" tvg-logo="https://githubusercontent.com",Мосфильм. Золотая коллекция'
    },
    "телепутешествия": {
        "url": "https://teletravel.tv", 
        "tag": '#EXTINF:-1 tvg-id="Teleputeshestviya" tvg-logo="https://teletravel.tv",Телепутешествия'
    },
    "discovery": {
        "url": "http://185.156.43", 
        "tag": '#EXTINF:-1 tvg-id="Discovery Channel" tvg-logo="https://githubusercontent.com",Discovery Channel'
    },
    "nat geo wild": {
        "url": "http://185.156.43", 
        "tag": '#EXTINF:-1 tvg-id="Nat Geo Wild" tvg-logo="https://githubusercontent.com",Nat Geo Wild'
    },
    "viju explore": {
        "url": "http://185.156.43", 
        "tag": '#EXTINF:-1 tvg-id="Viju Explore" tvg-logo="https://githubusercontent.com",Viju Explore'
    },
    "Travel Channel": {
        "url": "http://185.156.43", 
        "tag": '#EXTINF:-1 tvg-id="Travel Channel" tvg-logo="https://githubusercontent.com",Travel Channel'
    },
    "моя стихия": {
        "url": "https://cdnvideo.ru",
        "tag": '#EXTINF:-1 tvg-id="Morskoy" tvg-logo="https://iptvx.one",Моя стихия'
    },
    "vf мосфильм": {
        "url": "http://185.156.43",
        "tag": '#EXTINF:-1 tvg-id="vf-mosfilm" tvg-logo="https://githubusercontent.com",VF Мосфильм'
    }
}

def decode_url(s):
    try: return base64.b64decode(s.encode("utf-8")).decode("utf-8")
    except: return ""

def clean_string(s): 
    return re.sub(r"[^a-zA-Z0-9а-яёА-ЯЁ]", "", s.lower())

def get_quality_score(c): 
    return 10 if "HD" in str(c).upper() else 0

def check_url(url):
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

def main():
    ssl._create_default_https_context = ssl._create_unverified_context
    all_p = []
    with ThreadPoolExecutor(max_workers=7) as ex:
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
                elif fav == "discovery" and fav in c_name and "science" not in c_name: 
                    ok = True
                elif fav not in ["нтвсериал", "телепутешествия", "discovery"] and (fav == c_name or fav in c_name): 
                    ok = True
                if ok:
                    std = FAVORITE_CHANNELS[i]
                    if std not in matched: matched[std] = []
                    matched[std].append((inf, url)); break
                    
    final = ["#EXTM3U\n"]
    added = set()
    for ch in FAVORITE_CHANNELS:
        done = False
        if ch in matched:
            matched[ch].sort(key=get_quality_score, reverse=True)
            for inf, url in matched[ch]:
                if url in added: 
                    continue
                if check_url(url): 
                    final.append(f"{inf}\n{url}\n")
                    added.add(url)
                    done = True
                    break
        if not done and ch in RESERVE_LINKS:
            r = RESERVE_LINKS[ch]
            if r["url"] not in added: 
                final.append(f"{r['tag']}\n{r['url']}\n")
                added.add(r["url"])
                
    with open("playlist.m3u", "w", encoding="utf-8") as f: 
        f.writelines(final)

if __name__ == "__main__": 
    main()




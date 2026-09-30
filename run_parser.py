import urllib.request, urllib.error, re, base64, random, ssl
from concurrent.futures import ThreadPoolExecutor, as_completed

ENCRYPTED_SOURCES = [
    "aHR0cHM6Ly9zYXRleHByZXNzdHYucnUvYXBrL3NldHYubTN1",
    "aHR0cHM6Ly9nY2xuay5jb20vbGY0SnRCTGNfX19fX19fX19fXw==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0RpbW9ub3ZpY2gvVFYvcmVmcy9oZWFkcy9EaW1vbm92aWNoL0ZSRUUvVFY=",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0RpbW9ub3ZpY2gvVFYvRGltb25vdmljaC9GUkVFL1RW",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0lQVFZTSEFSRUQvVmVyb25hVFYvcmVmcy9oZWFkcy9tYWluL1Zlcm9uYVRWLm0zdQ==",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0lQVFZTSEFSRUQvVmVyb25hVFYvbWFpbi9WZXJvbmFTSEFSRUQubTN1",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL2FydGVtLWFydDk5OC9JUFRWcnUvcmVmcy9oZWFkcy9tYWluL2lwdHYxMjYubTN1",
    "aHR0cHM6Ly9sb2dhbmV0LnZlcmNlbC5hcHAvTG9nYW5ldFhBbGwubTN1",
    "aHR0cHM6Ly9sb2dhbmV0dHYudmVyY2VsLmFwcC9hbGwubTN1",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0RpbW9ub3ZpY2gvVFYvRGltb25vdmljaC9GUkVFL1RWP20zdQ==",
    "aHR0cHM6Ly9tcDNwLnVwLmxpL2lwdHYvYmFzZS5tM3U=",
    "aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL3BwZ2VvL2lwdHYtbWNjL21hc3Rlci9wbGF5bGlzdC5tM3U=",
    "aHR0cHM6Ly9pbi1kZXgucnUvZnJlZS5tM3U="
]

# НАШ ИСПРАВЛЕННЫЙ СПИСОК ИЗБРАННОГО:
FAVORITE_CHANNELS = [
    "кино 1 international",
    "мосфильм золотая коллекция",
    "неизвестная планета",
    "travel adventure",
    "индийское кино",
    "телепутешествия",
    "нтв сериал",  # Вернули чистый НТВ Сериал
    "nat geo wild",
    "viju explore",
    "discovery",
    "нтв хит"
]

def decode_url(encoded_str):
    try:
        return base64.b64decode(encoded_str.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""

def clean_string(s):
    return re.sub(r'[^a-zA-Z0-9а-яёА-ЯЁ]', '', s.lower())

def get_quality_score(candidate_tuple):
    inf_line = str(candidate_tuple).upper()
    score = 0
    if "HD" in inf_line: score += 10
    if "50FPS" in inf_line: score += 5
    return score

def check_url(url, timeout=4):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True
    except Exception:
        pass
    return False

def parse_source(encoded_url):
    url = decode_url(encoded_url)
    if not url: return []
    print(f"Парсинг источника: {url}")
    channels = []
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            content = response.read().decode('utf-8', errors='ignore')
            lines = content.splitlines()
            current_inf = ""
            for line in lines:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    current_inf = line
                elif line.startswith("http") and current_inf:
                    channels.append((current_inf, line))
                    current_inf = ""
    except Exception as e:
        print(f"Ошибка источника {url}: {e}")
    return channels

def main():
    context = ssl._create_unverified_context()
    ssl._create_default_https_context = lambda: context
    
    all_parsed = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(parse_source, src) for src in ENCRYPTED_SOURCES]
        for fut in as_completed(futures):
            all_parsed.extend(fut.result())
    
    if not all_parsed:
        print("Каналы не найдены.")
        return

    matched = {}
    fav_cleaned = [clean_string(ch) for ch in FAVORITE_CHANNELS]
    
    for inf, url in all_parsed:
        match = re.search(r',([^,\n\r]+)$', inf)
        if match:
            ch_name = match.group(1).strip()
            cleaned_name = clean_string(ch_name)
            
            for i, fav in enumerate(fav_cleaned):
                if fav == cleaned_name or fav in cleaned_name:
                    standard_name = FAVORITE_CHANNELS[i]
                    if standard_name not in matched:
                        matched[standard_name] = []
                    matched[standard_name].append((inf, url))
                    break
    
    print(f"Найдено ссылок: {len(all_parsed)}. Валидация...")
    
    final_playlist = ["#EXTM3U\n"]
    for ch_name in FAVORITE_CHANNELS:
        if ch_name in matched:
            candidates = matched[ch_name]
            candidates.sort(key=get_quality_score, reverse=True)
            
            found_working = False
            for inf, url in candidates:
                if check_url(url):
                    final_playlist.append(f"{inf}\n{url}\n")
                    print(f"[+] Добавлен: {ch_name}")
                    found_working = True
                    break
            if not found_working:
                print(f"[-] Пропущен (нет рабочих ссылок): {ch_name}")
        else:
            print(f"[-] Пропущен (не найден в источниках): {ch_name}")
            
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(final_playlist)
    print("Плейлист успешно обновлен!")

if __name__ == "__main__":
    main()

import requests
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

headers = {'User-Agent': 'BDNewsBot/1.0 (editor@provatikhobor24.com)'}
queries = ['নাজমুল হোসেন শান্ত', 'লিটন দাস', 'তাসকিন আহমেদ', 'মুশফিকুর রহিম', 'মেসি', 'রোনালদো', 'বাংলাদেশ ক্রিকেট দল']

for q in queries:
    url = f'https://bn.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={q}&gsrlimit=2&prop=pageimages&pithumbsize=1200'
    res = requests.get(url, headers=headers).json()
    pages = res.get('query', {}).get('pages', {})
    found = False
    for pid, p in pages.items():
        if 'thumbnail' in p:
            print(f"{q} -> {p.get('title')}: {p['thumbnail']['source']}")
            found = True
            break
    if not found:
        print(f"{q} -> Not found on bn.wiki")

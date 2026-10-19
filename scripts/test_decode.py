import requests
import re
from bs4 import BeautifulSoup

url = "https://news.google.com/rss/articles/CBMiY0FVX3lxTE9jeVNkMEJacjBzMmNXYmxyMGZ2NTFDdmI0cEVXYTIySjhwa3dTdkV6MW5WRUpGNXFGYXZHN1V6Zl8zdzgybE5xVkxHVVcxVEdkdDQxMFlRZjJINzI5QmMwYnBib9IBcEFVX3lxTFBBTW1iMS1jN05jSTl2RW9EdTMyX3VnTlNYWjd0STNWSWZSTnVNT2hsV1pudlRKczB6Y3dCT0FUc1FIZnJSb3U5NDFIbkZreTBzb1Z1MlcwR1FOU1pOLUlrZXN6dUlIcUdHM05LLVAxeDk?oc=5"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)

soup = BeautifulSoup(r.text, "html.parser")
for c in soup.find_all("c-wiz"):
    for a in c.find_all("a"):
        print("c-wiz link:", a.get("href"))

for a in soup.find_all("a"):
    h = a.get("href", "")
    if "prothomalo" in h or ("http" in h and "google" not in h):
        print("Candidate link:", h)

matches = re.findall(r'https?://[a-zA-Z0-9\.\-_/]+', r.text)
ext = [m for m in matches if not any(x in m for x in ['google', 'gstatic', 'schema', 'w3'])]
print("Ext links:", set(ext[:10]))

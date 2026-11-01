"""Download and generate SVG logos for all platforms and companies.
"""
import os
import urllib.request

LOGOS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

SIMPLE_ICONS_MAP = {
    'openai': 'openai.svg',
    'anthropic': 'anthropic.svg',
    'google': 'google.svg',
    'microsoft': 'microsoft.svg',
    'meta': 'meta.svg',
    'x': 'xai.svg',
    'perplexity': 'perplexity.svg',
    'bytedance': 'bytedance.svg',
    'alibabadotcom': 'alibaba.svg',
    'alipay': 'alipay.svg',
    'amazon': 'amazon.svg',
    'apple': 'apple.svg',
    'airbnb': 'airbnb.svg',
    'cloudflare': 'cloudflare.svg',
    'tripdotcom': 'ctrip.svg',
    'doordash': 'doordash.svg',
    'tiktok': 'douyin.svg',
    'etsy': 'etsy.svg',
    'facebook': 'facebook.svg',
    'instacart': 'instacart.svg',
    'instagram': 'instagram.svg',
    'kuaishou': 'kuaishou.svg',
    'linkedin': 'linkedin.svg',
    'mastercard': 'mastercard.svg',
    'meituan': 'meituan.svg',
    'mercadopago': 'mercadolibre.svg',
    'netflix': 'netflix.svg',
    'paypal': 'paypal.svg',
    'reddit': 'reddit.svg',
    'shopify': 'shopify.svg',
    'taobao': 'taobao.svg',
    'target': 'target.svg',
    'theguardian': 'theguardian.svg',
    'newyorktimes': 'nytimes.svg',
    'visa': 'visa.svg',
    'walmart': 'walmart.svg',
    'wechat': 'wechat.svg',
    'sinaweibo': 'weibo.svg',
    'wikipedia': 'wikipedia.svg',
    'zhihu': 'zhihu.svg',
    'ebay': 'ebay.svg',
    'mistralai': 'mistral.svg',
    'tencentqq': 'tencent.svg',
}

downloaded = 0
for slug, filename in SIMPLE_ICONS_MAP.items():
    dest = os.path.join(LOGOS_DIR, filename)
    url = f"https://cdn.jsdelivr.net/npm/simple-icons/icons/{slug}.svg"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        content = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        if 'fill=' not in content:
            content = content.replace('<path ', '<path fill="#f0f4fc" ')
        elif 'fill="currentColor"' in content:
            content = content.replace('fill="currentColor"', 'fill="#f0f4fc"')
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(content)
        downloaded += 1
        print(f"OK: {slug} -> {filename}")
    except Exception as e:
        print(f"FAILED {slug}: {e}")

# High quality SVG definitions for platforms / companies not in simple-icons
CUSTOM_SVGS = {
    'jd.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <path fill="#e1251b" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5h-2v-9h2v9zm6 0h-4.5V7.5H17v9z"/>
  <text x="12" y="15" fill="#f0f4fc" font-family="sans-serif" font-weight="900" font-size="8" text-anchor="middle">JD</text>
</svg>''',

    'reuters.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <circle cx="12" cy="12" r="10" fill="none" stroke="#ff8000" stroke-width="2"/>
  <circle cx="12" cy="12" r="3" fill="#ff8000"/>
  <circle cx="12" cy="5" r="1.5" fill="#ff8000"/>
  <circle cx="17" cy="7" r="1.5" fill="#ff8000"/>
  <circle cx="19" cy="12" r="1.5" fill="#ff8000"/>
  <circle cx="17" cy="17" r="1.5" fill="#ff8000"/>
  <circle cx="12" cy="19" r="1.5" fill="#ff8000"/>
  <circle cx="7" cy="17" r="1.5" fill="#ff8000"/>
  <circle cx="5" cy="12" r="1.5" fill="#ff8000"/>
  <circle cx="7" cy="7" r="1.5" fill="#ff8000"/>
</svg>''',

    'dowjones.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#002b49"/>
  <text x="12" y="16.5" fill="#f0f4fc" font-family="Georgia, serif" font-weight="bold" font-size="11" text-anchor="middle">DJ</text>
</svg>''',

    'britannica.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#0b2341"/>
  <path fill="#f0f4fc" d="M12 4c-1.5 2-2 4-2 6 0 2.2 1 3.5 2 4.5 1-1 2-2.3 2-4.5 0-2-.5-4-2-6z"/>
  <path fill="#f59e0b" d="M8 8c0 3 2 5 4 6-2 1-4 3-4 6h8c0-3-2-5-4-6 2-1 4-3 4-6H8z"/>
</svg>''',

    'williamssonoma.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#1e293b"/>
  <text x="12" y="16.5" fill="#f0f4fc" font-family="Georgia, serif" font-weight="bold" font-size="10" text-anchor="middle">WS</text>
</svg>''',

    'liverpool.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#e2007a"/>
  <text x="12" y="16.5" fill="#ffffff" font-family="sans-serif" font-weight="900" font-size="12" text-anchor="middle">L</text>
</svg>''',

    'luckin.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#002152"/>
  <path fill="#f0f4fc" d="M12 4c2.5 3 4 5.5 4 8a4 4 0 0 1-8 0c0-2.5 1.5-5 4-8z"/>
  <path fill="#38bdf8" d="M10 7L7 4m7 3l3-3"/>
</svg>''',

    'pinduoduo.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#e02e24"/>
  <path fill="#ffffff" d="M12 6.5C10 4 6 5 6 8.5c0 3.5 6 8.5 6 8.5s6-5 6-8.5c0-3.5-4-4.5-6-2z"/>
</svg>''',

    'nousresearch.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#0f172a"/>
  <path fill="#38bdf8" d="M12 3L4 9v6l8 6 8-6V9l-8-6zm0 3.5l5 3.75v4.5L12 18.5l-5-3.75v-4.5L12 6.5z"/>
</svg>''',

    'manus.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#18181b"/>
  <text x="12" y="16.5" fill="#f0f4fc" font-family="sans-serif" font-weight="900" font-size="10" text-anchor="middle">M</text>
  <circle cx="18" cy="6" r="2" fill="#38bdf8"/>
</svg>''',

    'openclaw.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#2d1537"/>
  <path fill="#f43f5e" d="M12 4a7 7 0 0 0-7 7c0 2.5 1.3 4.7 3.3 6L7 20l3.5-1.5c.5.3 1 .4 1.5.5V15h-2a2 2 0 0 1-2-2V9a5 5 0 0 1 8 0v4a2 2 0 0 1-2 2h-2v4c.5-.1 1-.2 1.5-.5L17 20l-1.3-3c2-1.3 3.3-3.5 3.3-6a7 7 0 0 0-7-7z"/>
</svg>''',

    'spearstreet.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#1e1e24"/>
  <path fill="#f0f4fc" d="M12 3l3 6h-2v12h-2V9H9l3-6z"/>
</svg>''',

    'cohere.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#39594d"/>
  <circle cx="9" cy="12" r="4.5" fill="#ff7759"/>
  <circle cx="15" cy="12" r="4.5" fill="#d1b09b"/>
</svg>''',

    'maoyan.svg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <rect width="24" height="24" rx="4" fill="#e51b24"/>
  <circle cx="12" cy="12" r="5" fill="#ffffff"/>
  <circle cx="12" cy="12" r="2.5" fill="#e51b24"/>
</svg>''',
}

for filename, svg in CUSTOM_SVGS.items():
    dest = os.path.join(LOGOS_DIR, filename)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"CUSTOM OK: {filename}")

print(f"Total logos available in {LOGOS_DIR}: {len(os.listdir(LOGOS_DIR))}")

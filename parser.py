# image_scraper/parser.py

import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from fetcher import fetch

CSS_URL = re.compile(r'url\((?:["\']?)(.*?)(?:["\']?)\)')

async def extract_image_urls(html, base, session, retries, timeout):
    soup = BeautifulSoup(html, 'html.parser')
    img_urls = []

    # 0) <picture> / <source> tags
    for source in soup.find_all('source'):
        if source.get('srcset'):
            for u in source['srcset'].split(','):
                candidate = u.strip().split(' ')[0]
                if candidate.lower().startswith(('http://','https://')):
                    img_urls.append(urljoin(base, candidate))
        elif source.get('src'):
            src = source['src']
            if src.lower().startswith(('http://','https://')):
                img_urls.append(urljoin(base, src))

    # 1) <img> variants
    for img in soup.find_all('img'):
        # srcset
        if img.get('srcset'):
            for u in img['srcset'].split(','):
                candidate = u.strip().split(' ')[0]
                if candidate.lower().startswith(('http://','https://')):
                    img_urls.append(urljoin(base, candidate))
        # various data-* attributes
        for attr in (
            'data-srcset','data-src','data-lazy','data-original',
            'data-lazy-image','data-img','data-deferred'
        ):
            if img.get(attr):
                val = img[attr]
                if val.lower().startswith(('http://','https://')):
                    img_urls.append(urljoin(base, val))
        # plain src
        if img.get('src'):
            src = img['src']
            if src.lower().startswith(('http://','https://')):
                img_urls.append(urljoin(base, src))

    # 2) inline style backgrounds (filter fonts, data URIs)
    ALLOWED = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif', '.heic')
    for tag in soup.select('[style]'):
        for match in CSS_URL.findall(tag['style']):
            u = urljoin(base, match)
            if not u.lower().startswith(('http://','https://')):
                continue
            ext = os.path.splitext(u.lower().split('?',1)[0])[1]
            if ext in ALLOWED:
                img_urls.append(u)

    # 3) external CSS links
    css_links = []
    for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
        href = link.get('href')
        if href and href.lower().startswith(('http://','https://')):
            css_links.append(urljoin(base, href))

    # dedupe URLs while preserving order
    seen = set()
    img_urls = [u for u in img_urls if u not in seen and not seen.add(u)]

    # final extension check
    def _is_image(u: str) -> bool:
        u = u.lower().split('?',1)[0]
        return u.endswith((
            '.jpg','.jpeg','.png','.gif','.bmp','.webp',
            '.avif','.heic'
        ))
    img_urls = [u for u in img_urls if _is_image(u)]

    return img_urls, css_links

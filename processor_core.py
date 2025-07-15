# image_scraper/processor_core.py

import asyncio
import os
import uuid
import logging
import hashlib
from urllib.parse import urljoin
from fetcher import fetch
from parser import extract_image_urls, CSS_URL
from downloader import download_image
from dynamic_fetcher import fetch_all_images_with_selenium

class RowProcessor:
    def __init__(self, session, idx, type_, activity_id, website, cfg, log_rows):
        self.session      = session
        self.idx          = idx
        self.type         = type_
        self.activity_id  = activity_id
        self.website      = website
        self.cfg          = cfg
        self.log_rows     = log_rows

        self.urls         = []
        self.css_links    = []
        self.success      = 0
        self.failures     = 0
        self.dedup_hashes = set()

        self.sem           = asyncio.Semaphore(cfg['download_concurrency'])
        self.filename_lock = asyncio.Lock()
        self.loop          = asyncio.get_event_loop()
        self.dynamic_used  = False

        # will be set after static fetch
        self.url_iter = None

        # allowed extensions for CSS filtering
        self._allowed_exts = (
            '.jpg', '.jpeg', '.png', '.gif',
            '.bmp', '.webp', '.avif', '.heic'
        )

    async def run(self):
        # 1) skip if no website
        if not isinstance(self.website, str) or not self.website.strip():
            self.log_rows.append({
                'row': self.idx,
                'activity_id': self.activity_id,
                'url': self.website,
                'file': '',
                'status': 'no_website',
                'error': ''
            })
            return

        # 2) static fetch + parse
        html, ferr = await fetch(
            self.session, self.website,
            self.cfg['request_retries'],
            self.cfg['timeout']
        )
        if html:
            self.urls, self.css_links = await extract_image_urls(
                html, self.website, self.session,
                self.cfg['request_retries'],
                self.cfg['timeout']
            )
        else:
            logging.info(f"[Row {self.idx}] static fetch failed ({ferr}); deferring to Selenium")
            self.urls, self.css_links = [], []

        # initialize iterator
        self.url_iter = iter(self.urls)

        # 3) spawn initial download workers
        tasks = set()
        for _ in range(min(self.cfg['download_concurrency'], self.cfg['max_images_per_site'])):
            u = await self._get_next_url()
            if not u:
                break
            tasks.add(asyncio.create_task(self._worker_with_sem(u)))

        # 4) wait for completion or quota
        while tasks:
            done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for d in done:
                nxt = d.result()
                if nxt:
                    tasks.add(nxt)
            if self.success >= self.cfg['max_images_per_site']:
                for t in tasks:
                    t.cancel()
                break

    async def _get_next_url(self):
        # a) from static list, only http(s)
        while True:
            try:
                url = next(self.url_iter)
            except StopIteration:
                break
            if not url.lower().startswith(('http://','https://')):
                continue
            return url

        # b) from CSS-linked files (once at a time)
        if self.css_links:
            css_url = self.css_links.pop(0)
            css_txt, _ = await fetch(
                self.session, css_url,
                self.cfg['request_retries'],
                self.cfg['timeout']
            )
            if css_txt:
                raw = CSS_URL.findall(css_txt)
                new = []
                for m in raw:
                    u = urljoin(css_url, m)
                    if not u.lower().startswith(('http://','https://')):
                        continue
                    ext = os.path.splitext(u.lower().split('?',1)[0])[1]
                    if ext in self._allowed_exts:
                        new.append(u)
                if new:
                    self.urls.extend(new)
                    self.url_iter = iter(new)
                    return await self._get_next_url()

        # c) on-demand Selenium batch (once only)
        if not self.dynamic_used and self.success < self.cfg['max_images_per_site']:
            self.dynamic_used = True
            needed = self.cfg['max_images_per_site'] - self.success
            batch  = min(self.cfg['download_concurrency'], needed)
            try:
                extra = await self.loop.run_in_executor(
                    None,
                    fetch_all_images_with_selenium,
                    self.website, batch
                )
            except Exception as e:
                logging.warning(f"[Row {self.idx}] Selenium fetch error: {e}")
                return None

            # only HTTP(s) here
            filtered = [u for u in extra if u.lower().startswith(('http://','https://'))]
            new = [u for u in filtered if u not in self.urls]
            if new:
                self.urls.extend(new)
                self.url_iter = iter(new)
                return await self._get_next_url()

        return None

    async def _worker_with_sem(self, url):
        async with self.sem:
            return await self._worker(url)

    async def _worker(self, url):
        # HEAD-check (warn only)
        parts = url.lower().split('?')[0].rsplit('.', 1)
        if not (len(parts) > 1 and parts[-1] in self._allowed_exts):
            try:
                hd = await self.session.head(url, timeout=self.cfg['timeout'])
                ct = hd.headers.get('Content-Type','')
                if not ct.startswith('image/'):
                    logging.warning(f"[Row {self.idx}] HEAD non-image: {ct}")
            except Exception as e:
                logging.warning(f"[Row {self.idx}] HEAD error: {e}")

        # download + retry
        ext      = os.path.splitext(url)[1].split('?')[0] or '.jpg'
        tmp_name = f"tmp_{uuid.uuid4().hex}{ext}"
        tmp_path = os.path.join(self.cfg['output_dir'], tmp_name)
        ok = False
        err = ''

        for attempt in range(1, 4):
            try:
                ok, err = await download_image(
                    self.session, url, tmp_path,
                    self.cfg['min_image_size'], self.cfg['timeout'],
                    self.loop
                )
            except Exception as e:
                ok, err = False, str(e)
            if ok:
                break
            self.failures += 1
            logging.warning(f"[Row {self.idx}] download attempt {attempt} failed: {err}")
            await asyncio.sleep(0.5 * attempt)

        if ok:
            # dedupe via MD5
            with open(tmp_path, 'rb') as f:
                h = hashlib.md5(f.read()).hexdigest()
            if h in self.dedup_hashes:
                os.remove(tmp_path)
                self.log_rows.append({
                    'row': self.idx,
                    'activity_id': self.activity_id,
                    'url': url,
                    'file': '',
                    'status': 'download_failed',
                    'error': 'duplicate_image'
                })
            else:
                self.dedup_hashes.add(h)
                async with self.filename_lock:
                    self.success += 1
                    n = self.success
                final = f"{self.activity_id}_{self.type}_{n}{ext}"
                os.replace(tmp_path, os.path.join(self.cfg['output_dir'], final))
                self.log_rows.append({
                    'row': self.idx,
                    'activity_id': self.activity_id,
                    'url': url,
                    'file': final,
                    'status': 'success',
                    'error': ''
                })
        else:
            try: os.remove(tmp_path)
            except: pass
            self.failures += 1
            self.log_rows.append({
                'row': self.idx,
                'activity_id': self.activity_id,
                'url': url,
                'file': '',
                'status': 'download_failed',
                'error': err
            })

        # schedule next if quota not met
        if self.success < self.cfg['max_images_per_site']:
            nxt = await self._get_next_url()
            if nxt:
                return asyncio.create_task(self._worker_with_sem(nxt))

        return None

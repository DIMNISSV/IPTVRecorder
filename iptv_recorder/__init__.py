import re
from datetime import datetime
from pathlib import Path
from time import sleep
from threading import Thread
from typing import Iterator, Callable, Any

import httpx


class IPTVRecorder:
    _EXTX = re.compile(r'#EXT-X-(.+):(.+)', re.M)

    def __init__(self, name: str, url: str,
                 saving_path: str | Path = '.',
                 start: datetime = datetime.min,
                 end: datetime = datetime.max,
                 retry_count: int = 3,
                 use_threads: bool = True,
                 save_if_empty: bool = False,
                 max_hashes: int = 500):
        self.retry_count = retry_count
        self.path = saving_path
        self.url = url
        self.start = start
        self.end = end
        self.host = '/'.join(url.split('/')[0:-1]) or ''
        self.name = name
        self.use_thr = use_threads
        self.save_empty = save_if_empty
        self.max_hashes = max_hashes
        self._sleep = False
        self._hashes = {*()}

    def _mkdirs(self, time_format: str = '%Y-%m-%d %H.%M.%S'):
        dir_path = Path(self.path, self.name, datetime.now().strftime(time_format))
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def _read_url(self, client, url: str):
        return self._request(client, url).text

    def _request(self, client: httpx.Client, url: str) -> httpx.Response | None:
        res = self._try_request(client.get, url)
        if res.content:
            return res
        return

    def _download(self, client, url, fp):
        res = self._request(client, url)
        if not len(res.content) and not self.save_empty: return None
        content = res.content
        content_hash = hash(content)
        if content_hash in self._hashes:
            return
        elif len(self._hashes) > self.max_hashes:
            self._hashes.clear()

        self._hashes.add(content_hash)
        with open(fp, 'wb') as f:
            f.write(content)

    def _read_m3u8(self, text: str, extx: dict):
        return (part if part[0:4] != 'http' else f'{self.host}/{part}' for part in
                text.splitlines()[2 + len(extx):][::2])

    def _m3u8_extx(self, text: str):
        return dict(self._EXTX.findall(text))

    def _check_time(self):
        if datetime.now() > self.end:
            return False
        while datetime.now() < self.start:
            sleep(1.)
        return True

    def _record_m3u8(self, dir_path, n):
        client = httpx.Client()
        start = datetime.now()
        seq = self._read_url(client, self.url)
        extx = self._m3u8_extx(seq)
        part_n = 1
        for part in self._read_m3u8(seq, extx):
            fp = dir_path / f'{n:0>5}_{part_n:0>3}.ts'
            if self.use_thr:
                Thread(target=self._download, args=(client, f'{self.host}/{part}', fp)).start()
            else:
                self._download(client, f'{self.host}/{part}', fp)
            part_n += 1
        sleep_time = float(extx.get('TARGETDURATION', 0)) + 1.0 - (datetime.now() - start).total_seconds()
        if sleep_time > 0.:
            sleep(sleep_time)

    def _try_request(self, req: Callable, *args, **kwargs) -> Any:
        n = 0
        res = None

        while True:
            try:
                res = req(*args, **kwargs)
                break
            except httpx.HTTPError:
                n += 1
                if n > self.retry_count:
                    break
                continue
        return res

    def record_m3u8(self):
        n = 1
        dir_path = self._mkdirs()

        while self._check_time():
            self._record_m3u8(dir_path, n)
            n += 1

    def record(self):
        dir_path = self._mkdirs()
        with self._try_request(httpx.stream, 'GET', self.url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100102 Firefox/105.0'
        }) as res:
            print(res)

            itr = res.iter_bytes()
            with open(Path(dir_path, f'{self.name}.ts'), 'wb', 0) as f:
                while self._check_time():
                    part = next(itr)
                    print(len(part), hash(part))
                    f.write(part)


if __name__ == '__main__':
    fs = IPTVRecorder('2x2', 'http://37.193.68.117:81/udp/239.1.2.1:1234', r'D:\Видео')
    fs.record()

# IPTVRecorder
IPTVRecorder Python

# Using
Create IPTVRecorder:
```python
class IPTVRecorder:
    def __init__(self, name: str, url: str,
                 saving_path: str | Path = '.',
                 start: datetime = datetime.min,
                 end: datetime = datetime.max,
                 retry_count: int = 3,
                 use_threads: bool = True,
                 save_if_empty: bool = False,
                 max_hashes: int = 500):
        ...
```
```python
recorder = IPTVRecorder(...)
```
And, call one of two methods:
`record_m3u8()` or just `record()`

It's working not only with iptv, it for all stream's...

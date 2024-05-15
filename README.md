# lanraragi-api

a Python library for [LANraragi](https://github.com/Difegue/LANraragi) API.

> Many thanks to the author of this wonderful manga server app.

All the APIs are from [the official LANraragi document](https://sugoi.gitbook.io/lanraragi/api-documentation/getting-started). 

Besides those basic APIs, I also made some enhancements for better use, e.g. [`lanraragi_api.common.entity.Archive#set_artists(self, artists: list[str])`](./lanraragi_api/common/entity.py)

# Demo

See [demo.py](demo.py)

```python
from lanraragi_api import LANrargiAPI
from lanraragi_api.common.entity import Archive

apikey = ''
server = 'http://127.0.0.1:3000'
api = LANrargiAPI(apikey, server)

archives: list[Archive] = api.archive.get_all_archives()
print(archives[0])
```

# Build
```shell
python.exe .\setup.py bdist_wheel sdist
```
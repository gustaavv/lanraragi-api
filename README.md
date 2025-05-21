# lanraragi-api

A Python library for [LANraragi](https://github.com/Difegue/LANraragi) API.

> Many thanks to the author of this wonderful manga server.



## Quick start

Install this package:

```shell
pip install lanraragi_api
```

Get metadata of a random archive:

> See [demo.py](demo.py)

```python
from lanraragi_api import LANraragiAPI
from lanraragi_api.base.archive import Archive

apikey = 'your-key'
server = 'http://127.0.0.1:3000'
api = LANraragiAPI(server, key=apikey)

archives: list[Archive] = api.search.get_random_archives()
print(archives[0])
```



## How to use?

All the APIs in the `lanraragi_api.base` package are
from [the official LANraragi document](https://sugoi.gitbook.io/lanraragi/api-documentation/getting-started), which you will be using in most times.

Functions in the `lanraragi_api.enhanced` package are built on the base APIs, offering useful functionalities.

- `server_side.py` contains server-side functions. The code is the same to that of LANraragi, only translated from Perl to Python.
- `script.py` contains functions for operation and management.



## Release versions

Every release of lanraragi-api is made only for the corresponding release of LANraragi. So you should choose the correct lanraragi-api version based on the server version.

| LANraragi  | lanraragi-api                            |
| ---------- | ---------------------------------------- |
| `v.0.9.0`  | `0.9.0.0`, `0.9.0.1`, ... , `0.9.0.x`    |
| `v.0.9.40` | `0.9.40.0`, `0.9.40.1`, ... , `0.9.40.y` |

In order to make it simple, the first three version numbers are always the same, while the last version number of lanraragi-api serves as patches (just choose the latest one).




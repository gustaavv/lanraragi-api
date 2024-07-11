# lanraragi-api

a Python library for [LANraragi](https://github.com/Difegue/LANraragi) API.

> Many thanks to the author of this wonderful manga server.

All the APIs in the `lanraragi_api.base` package are
from [the official LANraragi document](https://sugoi.gitbook.io/lanraragi/api-documentation/getting-started).

- Based on those APIs, I also made some enhancements, e.g. [`Archive#set_artists()`](./lanraragi_api/base/archive.py).
- Some APIs have not been tested, you can switch on [`Config.USE_UNTESTED_FUNCTIONS`](./lanraragi_api/Config.py) to use it anyway.

Code in the `lanraragi_api.enhanced` package are mainly scripts that built on the existing APIs.
- [server_side.py](lanraragi_api%2Fenhanced%2Fserver_side.py) contains useful function implemented in the server's code. The code is the same, only translated from Perl to Python.
- [script.py](lanraragi_api%2Fenhanced%2Fscript.py) contains useful scripts for operation and management. There are:
  - `subfolders_to_artists`: Walk through content folder, and set artist tag for those archives without artist tag. For every archive, the artist will be the name of its parent folder. This function is similar to [Subfolders to Categories](https://github.com/Difegue/LANraragi/blob/4a85548cd5fccd2aaf929871635f8f603e9d0d4a/lib/LANraragi/Plugin/Scripts/FolderToCat.pm), but has better performance.


# Demo

Install this package:

```shell
pip install lanraragi_api
```

Use this package:

> See [demo.py](demo.py)

```python
from lanraragi_api import LANrargiAPI
from lanraragi_api.common.entity import Archive

apikey = ''
server = 'http://127.0.0.1:3000'
api = LANrargiAPI(apikey, server)

archives: list[Archive] = api.search.get_random_archives()
print(archives[0])
```

# Build

```shell
python.exe .\setup.py bdist_wheel sdist
```
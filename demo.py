from lanraragi_api import LANraragiAPI
from lanraragi_api.base.archive import ArchiveMetadata

apikey = "your-key"
server = "http://127.0.0.1:3000"
api = LANraragiAPI(server, key=apikey)

archives: list[ArchiveMetadata] = api.search.get_random_archives()
print(archives[0])

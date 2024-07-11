from lanraragi_api import LANrargiAPI
from lanraragi_api.base.archive import Archive

apikey = ''
server = 'http://127.0.0.1:3000'
api = LANrargiAPI(apikey, server)

archives: list[Archive] = api.search.get_random_archives()
print(archives[0])

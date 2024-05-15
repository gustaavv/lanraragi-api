
from pydantic import BaseModel


class Archive(BaseModel):
    arcid: str
    isnew: str
    extension: str
    pagecount: int
    progress: int
    # k1:v1, k2:v2, v3, v4
    tags: str
    lastreadtime: int
    title: str

    def tags_to_dict(self) -> dict[str, list[str]]:
        tags = self.tags.split(',')
        ans = {}
        for t in tags:
            if t == '':
                continue
            t = t.strip()
            if ':' in t:
                kv = t.split(':')
                k = kv[0]
                v = kv[1]
                if k not in ans:
                    ans[k] = []
                ans[k].append(v)
            else:
                k = "ONLY_VALUES"
                if k not in ans:
                    ans[k] = []
                ans[k].append(t)
        return ans

    def dict_to_tags(self, json: dict[str, list[str]]):
        """
        The function will modify the object
        """
        tags = ""
        modified: bool = False
        for k in json:
            for v in json[k]:
                modified = True
                if k == 'ONLY_VALUES':
                    tags += f"{v},"
                else:
                    tags += f"{k}:{v},"
        if modified:
            tags = tags[:-1]
        self.tags = tags

    def set_artists(self, artists: list[str]):
        json = self.tags_to_dict()
        json['artist'] = artists
        self.dict_to_tags(json)

    def has_artists(self) -> bool:
        return "artist" in self.tags


class Category(BaseModel):
    archives: list[str]
    id: str
    last_used: str
    name: str
    pinned: str
    search: str




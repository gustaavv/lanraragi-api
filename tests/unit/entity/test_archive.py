from pydantic import BaseModel, Field

from lanraragi_api.entity.archive import ArchiveTags


class TestArchive:
    pass


class TestArchiveTags:
    def test_get_tag_list(self):
        class TestCase(BaseModel):
            init_tags: str = Field(...)
            tag_list: list[str] = Field(...)
            new_tags: str = Field(...)

        test_cases: list[TestCase] = [
            TestCase(
                init_tags="a,b, c1:c2, d3",
                tag_list=["a", "b", "c1:c2", "d3"],
                new_tags="a,b, c1:c2, d3",
            ),
            TestCase(
                init_tags="a,b,c1:c2,, d3,",
                tag_list=["a", "b", "c1:c2", "d3"],
                new_tags="a,b,c1:c2,, d3,",
            ),
            TestCase(init_tags="", tag_list=[], new_tags=""),
            TestCase(init_tags=",,", tag_list=[], new_tags=",,"),
            TestCase(init_tags=",,:", tag_list=[":"], new_tags=",,:"),
            TestCase(init_tags="a,b,a", tag_list=["a", "b", "a"], new_tags="a,b,a"),
        ]

        for tc in test_cases:
            at = ArchiveTags(tc.init_tags)
            assert tc.tag_list == at.get_tag_list()
            assert tc.new_tags == at.tags

    def test_set_tag(self):
        class TestCase(BaseModel):
            init_tags: str = Field(...)
            set_tag_list: list[str] = Field(...)
            new_tags: str = Field(...)

        test_cases: list[TestCase] = [
            TestCase(
                init_tags="a,b, c1:c2, d3",
                set_tag_list=["a", "b", "c1:c2", "d3"],
                new_tags="a,b,c1:c2,d3",
            ),
            TestCase(
                init_tags="e,f",
                set_tag_list=["a", "b", "c1:c2", "d3"],
                new_tags="a,b,c1:c2,d3",
            ),
            TestCase(init_tags="", set_tag_list=["c1:c2", "a"], new_tags="c1:c2,a"),
            TestCase(init_tags="a,b,a", set_tag_list=["a", "b", "a"], new_tags="a,b"),
        ]

        for tc in test_cases:
            at = ArchiveTags(tc.init_tags)
            at.set_tag(tc.set_tag_list)
            assert at.tags == tc.new_tags

    def test_get_artists(self):
        class TestCase(BaseModel):
            init_tags: str = Field(...)
            artist_list: list[str] = Field(...)

        test_cases: list[TestCase] = [
            TestCase(
                init_tags="a,b, c1:c2, d3,artist:a1",
                artist_list=["a1"],
            ),
            TestCase(
                init_tags="a,b,c1:c2,, d3,artist:,artist:a2",
                artist_list=["", "a2"],
            ),
            TestCase(init_tags="", artist_list=[]),
            TestCase(init_tags=",,", artist_list=[]),
            TestCase(init_tags=",,:", artist_list=[]),
            TestCase(init_tags="a,b,a", artist_list=[]),
            TestCase(
                init_tags="artist:a1,artist:a2,b1,b2,,artist:a1,",
                # no deduplication if no set methods are called
                artist_list=["a1", "a2", "a1"],
            ),
        ]

        for tc in test_cases:
            at = ArchiveTags(tc.init_tags)
            assert at.get_artists() == tc.artist_list

    def test_set_artists(self):
        class TestCase(BaseModel):
            init_tags: str = Field(...)
            set_artist_list: list[str] = Field(...)
            new_artist_list: list[str] = Field(...)
            new_tags: str = Field(...)

        test_cases: list[TestCase] = [
            TestCase(
                init_tags="a,b, c1:c2, d3",
                set_artist_list=["a1"],
                new_artist_list=["a1"],
                new_tags="a,b,c1:c2,d3,artist:a1",
            ),
            TestCase(
                init_tags="a,b, c1:c2,,artist:a1, d3",
                set_artist_list=["a1"],
                new_artist_list=["a1"],
                # artist: tag will be put last
                new_tags="a,b,c1:c2,d3,artist:a1",
            ),
            TestCase(
                init_tags="a,b, c1:c2, d3,d3,artist:a1",
                set_artist_list=["a1", "a2"],
                new_artist_list=["a1", "a2"],
                new_tags="a,b,c1:c2,d3,artist:a1,artist:a2",
            ),
            TestCase(
                init_tags="a,b, c1:c2, d3,d3,artist:a1",
                set_artist_list=["a2", "a1"],
                new_artist_list=["a2", "a1"],
                # order matters
                new_tags="a,b,c1:c2,d3,artist:a2,artist:a1",
            ),
            TestCase(
                init_tags="a,b,c1:c2,, d3,artist:a2",
                set_artist_list=["", "a2"],
                new_artist_list=["", "a2"],
                new_tags="a,b,c1:c2,d3,artist:,artist:a2",
            ),
        ]

        for tc in test_cases:
            at = ArchiveTags(tc.init_tags)
            at.set_artists(tc.set_artist_list)
            assert at.get_artists() == tc.new_artist_list
            assert at.tags == tc.new_tags

    def test_append_artists(self):
        class TestCase(BaseModel):
            init_tags: str = Field(...)
            append_artist_list: list[str] = Field(...)
            new_artist_list: list[str] = Field(...)
            new_tags: str = Field(...)

        test_cases: list[TestCase] = [
            TestCase(
                init_tags="a,b, c1:c2, d3",
                append_artist_list=["a1"],
                new_artist_list=["a1"],
                new_tags="a,b,c1:c2,d3,artist:a1",
            ),
            TestCase(
                init_tags="a,b, c1:c2,,artist:a1, d3",
                append_artist_list=["a1"],
                new_artist_list=["a1"],
                # artist: tag will be append last, but the new one is deduplicated
                new_tags="a,b,c1:c2,artist:a1,d3",
            ),
            TestCase(
                init_tags="a,b, c1:c2, d3,artist:a1,d3,",
                append_artist_list=["a2"],
                new_artist_list=["a1", "a2"],
                new_tags="a,b,c1:c2,d3,artist:a1,artist:a2",
            ),
            TestCase(
                init_tags="a,artist:a1,b, c1:c2, d3,artist:a1,d3,",
                append_artist_list=["a2"],
                new_artist_list=["a1", "a2"],
                new_tags="a,artist:a1,b,c1:c2,d3,artist:a2",
            ),
            TestCase(
                init_tags="a,b, c1:c2, d3,d3,artist:a1",
                append_artist_list=["a2", "a1"],
                new_artist_list=["a1", "a2"],
                # order matters
                new_tags="a,b,c1:c2,d3,artist:a1,artist:a2",
            ),
            TestCase(
                init_tags="a,b,c1:c2,, d3,artist:a2",
                append_artist_list=["", "a2"],
                new_artist_list=["a2", ""],
                new_tags="a,b,c1:c2,d3,artist:a2,artist:",
            ),
        ]

        for tc in test_cases:
            at = ArchiveTags(tc.init_tags)
            at.append_artists(tc.append_artist_list)
            assert at.get_artists() == tc.new_artist_list
            assert at.tags == tc.new_tags

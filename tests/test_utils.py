import pytest

import metsrw

GOOD_PATHS_SLASH_URLS = (
    "30_CFLQ_271_13-3-13_1524[1].pdf",
    "30/CFLQ_271_13-3-13_1524[1].pdf",
    r"30\ CFLQ_271_13-3-13_1524[1].pdf",
    "/foo/bar[baz/hello",  # urllib.urlparse will accept this because it's a URL with just a path.
    "http://foobar.com/hello[1].pdf",
)

# urllib.urlparse will choke on these and raise ValueError because of the
# unbalanced bracket in the netloc part.
BAD_URLS = ("http://foo[bar.com/hello[1].pdf",)


def test_url_encoding():
    for url in GOOD_PATHS_SLASH_URLS:
        assert url == metsrw.urldecode(metsrw.urlencode(url))
    for url in BAD_URLS:
        with pytest.raises(ValueError):
            metsrw.urlencode(url)


def test_generate_mdtype_key():
    assert metsrw.generate_mdtype_key("MDTYPE") == "MDTYPE"
    assert metsrw.generate_mdtype_key("MDTYPE", "OTHERMDTYPE") == "MDTYPE_OTHERMDTYPE"

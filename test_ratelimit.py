#
# Test ratelimit fields
#
import http_sfv


def test_policy():
    policies = [
        "1000;w=3600,5000;w=86400",
        "100;w=60",
        "10;w=1, 50;w=60, 1000;w=3600, 5000;w=86400",
        "10;w=1;burst=1000, 1000;w=3600",
    ]
    for p in policies:
        l = http_sfv.List()
        l.parse(p.encode())
        for i in l:
            assert i.value
            assert "w" in i.params
            print("value: ", i.value, "params:", dict(i.params))


def test_all_in_one():
    values = [
        (
            "limit=10, remaining=10, reset=4,"
            """policy=(10;w=1 50;w=60 1000;w=3600 5000;w=86400)"""
        ),
    ]
    for v in values:
        d = http_sfv.Dictionary()
        d.parse(v.encode())
        for k, v in d.items():
            print("parameter:", k, "value:", v)
            assert k
            assert v
            if hasattr(v, "__iter__"):
                for i in v:
                    assert i.value
                    assert "w" in i.params
                    print("value: ", i.value, "params:", dict(i.params))
    raise NotImplementedError

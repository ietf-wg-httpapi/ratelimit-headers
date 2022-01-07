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

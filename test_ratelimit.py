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


def find_quota_policy(policies, limit):
    for policy in policies:
        if policy.value == limit:
            return policy.params
    return {}


def parse_fields(headers):
    # 27 µs ± 499 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    limit = http_sfv.Item()
    limit.parse(headers["limit"].encode())

    policies = http_sfv.List()
    policies.parse(headers["policy"].encode())
    quota_policy = find_quota_policy(policies, limit.value)
    return limit, policies, quota_policy


def parse_fields_token(headers):
    # 24.2 µs ± 506 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    limit = http_sfv.Item()
    limit.parse(headers["limit"].encode())

    policies = http_sfv.Dictionary()
    policies.parse(headers["policy"].encode())
    quota_policy = policies[f"q{limit.value}"]
    return limit, policies, quota_policy.params


def parse_fields_int(headers):
    # 24.5 µs ± 297 ns per loop (mean ± std. dev. of 7 runs, 10,000 loops each)
    limit = int(headers["limit"])
    policies = http_sfv.List()
    policies.parse(headers["policy"].encode())
    quota_policy = find_quota_policy(policies, limit)
    return limit, policies, quota_policy


def test_get_policy():
    # To retreive the policy, I need to iterate over the list.
    headers = dict(
        policy=(
            """10;w=1,"""
            """50;w=60,"""
            """1000;w=3600;comment="foo", """
            """5000;w=86400"""
        ),
        limit="""1000""",
    )

    limit, policies, quota_policy = parse_fields(headers)
    assert limit.value == 1000

    for policy in policies:
        print("parameter:", policy.value, "value:", policy.params["w"])


def test_get_policy_tokenized():
    # To retreive the policy, I need to iterate over the list.
    headers = dict(
        policy=(
            """q10;w=1,"""
            """q50;w=60,"""
            """q1000;w=3600;comment="foo", """
            """q5000;w=86400"""
        ),
        limit="""1000""",
    )
    limit = http_sfv.Item()
    limit.parse(headers["limit"].encode())
    assert limit.value == "q1000"

    policies = http_sfv.List()
    policies.parse(headers["policy"].encode())
    for policy in policies:
        print("parameter:", policy.value, "value:", policy.params["w"])

    # I could create a dictionary out of the list.
    policies_dict = {policy.value: policy.params for policy in policies}
    print("policies:", policies_dict)
    print("current policy:", policies_dict[limit.value])
    raise NotImplementedError

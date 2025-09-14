#
# Test ratelimit fields according to latest draft syntax
#
# Updated to use the new RateLimit-Policy and RateLimit header syntax:
# - RateLimit-Policy: "name";q=quota;w=window;pk=:partition_key:;qu="unit"
# - RateLimit: "name";r=remaining;t=time_to_reset;pk=:partition_key:
#
import http_sfv


def test_ratelimit_policy():
    # Test RateLimit-Policy header format according to latest draft
    policies = [
        '"hourly";q=1000;w=3600,"daily";q=5000;w=86400',
        '"permin";q=100;w=60',
        '"fast";q=10;w=1,"min";q=50;w=60,"hour";q=1000;w=3600,"day";q=5000;w=86400',
        '"burst";q=10;w=1;burst=1000,"hourly";q=1000;w=3600',
    ]
    for p in policies:
        l = http_sfv.List()
        l.parse(p.encode())
        for i in l:
            assert i.value  # policy name
            assert "q" in i.params  # quota
            assert "w" in i.params  # window
            print("policy: ", i.value, "params:", dict(i.params))


def test_ratelimit_fields():
    # Test both RateLimit-Policy and RateLimit headers together
    # According to latest draft syntax
    policy_header = '"default";q=10;w=1,"hourly";q=50;w=60,"daily";q=1000;w=3600,"monthly";q=5000;w=86400'
    ratelimit_header = '"default";r=10;t=4'
    
    # Parse RateLimit-Policy header
    policy = http_sfv.List()
    policy.parse(policy_header.encode())
    
    # Parse RateLimit header  
    ratelimit = http_sfv.List()
    ratelimit.parse(ratelimit_header.encode())
    
    # Verify policy structure
    for policy_item in policy:
        assert policy_item.value  # policy name
        assert "q" in policy_item.params  # quota
        assert "w" in policy_item.params  # window
        print("policy:", policy_item.value, "quota:", policy_item.params["q"], "window:", policy_item.params["w"])
    
    # Verify ratelimit structure
    for ratelimit_item in ratelimit:
        assert ratelimit_item.value  # policy name
        assert "r" in ratelimit_item.params  # remaining
        assert "t" in ratelimit_item.params  # time to reset
        print("ratelimit:", ratelimit_item.value, "remaining:", ratelimit_item.params["r"], "reset:", ratelimit_item.params["t"])


def find_policy_by_name(policies, policy_name):
    """Find a policy by its name from a list of policies"""
    for policy in policies:
        if policy.value == policy_name:
            return policy.params
    return {}


def parse_ratelimit_headers(headers):
    """Parse RateLimit-Policy and RateLimit headers according to latest draft"""
    # Parse RateLimit-Policy header
    policies = http_sfv.List()
    policies.parse(headers["RateLimit-Policy"].encode())
    
    # Parse RateLimit header
    ratelimit = http_sfv.List()
    ratelimit.parse(headers["RateLimit"].encode())
    
    # Get the current policy name from the RateLimit header
    current_policy_name = ratelimit[0].value if ratelimit else None
    
    # Find the matching policy
    policy_params = find_policy_by_name(policies, current_policy_name) if current_policy_name else {}
    
    return policies, ratelimit, policy_params


def test_quota_units_example():
    """Test RateLimit headers with quota units according to latest draft"""
    headers = dict(
        **{"RateLimit-Policy": '"bandwidth";q=65535;qu="content-bytes";w=10;pk=:sdfjLJUOUH==:'},
        **{"RateLimit": '"bandwidth";r=30000;t=5;pk=:sdfjLJUOUH==:'}
    )
    
    policies, ratelimit, policy_params = parse_ratelimit_headers(headers)
    
    # Verify policy structure with quota units
    policy = policies[0]
    assert policy.value == "bandwidth"
    assert policy.params["q"] == 65535
    assert policy.params["qu"] == "content-bytes"  # quota unit
    assert policy.params["w"] == 10
    
    # Verify ratelimit structure
    current = ratelimit[0]
    assert current.value == "bandwidth"
    assert current.params["r"] == 30000  # remaining bytes
    assert current.params["t"] == 5
    
    print("policy:", policy.value, "quota:", policy.params["q"], "unit:", policy.params["qu"], "window:", policy.params["w"])
    print("ratelimit:", current.value, "remaining:", current.params["r"], "reset:", current.params["t"])


def test_multiple_policies_example():
    """Test multiple policies as shown in draft examples"""
    # Example from draft: RateLimit-Policy: "permin";q=50;w=60,"perhr";q=1000;w=3600
    headers = dict(
        **{"RateLimit-Policy": '"permin";q=50;w=60,"perhr";q=1000;w=3600'},
        **{"RateLimit": '"permin";r=25;t=45'}
    )
    
    policies, ratelimit, policy_params = parse_ratelimit_headers(headers)
    
    # Should have 2 policies
    assert len(policies) == 2
    
    # Verify first policy
    assert policies[0].value == "permin"
    assert policies[0].params["q"] == 50
    assert policies[0].params["w"] == 60
    
    # Verify second policy  
    assert policies[1].value == "perhr"
    assert policies[1].params["q"] == 1000
    assert policies[1].params["w"] == 3600
    
    # Verify current ratelimit refers to permin policy
    assert ratelimit[0].value == "permin"
    assert ratelimit[0].params["r"] == 25
    assert ratelimit[0].params["t"] == 45
    
    print("Multiple policies test passed - found", len(policies), "policies")


def test_basic_policy_example():
    """Test basic policy example from draft"""
    # Example from draft: RateLimit-Policy: "default";q=100;w=10
    headers = dict(
        **{"RateLimit-Policy": '"default";q=100;w=10'},
        **{"RateLimit": '"default";r=50;t=30'}
    )
    
    policies, ratelimit, policy_params = parse_ratelimit_headers(headers)
    
    # Verify policy
    policy = policies[0]
    assert policy.value == "default"
    assert policy.params["q"] == 100
    assert policy.params["w"] == 10
    
    # Verify ratelimit
    current = ratelimit[0]
    assert current.value == "default"
    assert current.params["r"] == 50
    assert current.params["t"] == 30
    
    print("Basic policy test passed")


def test_policy_lookup():
    """Test retrieving a specific policy from RateLimit-Policy and RateLimit headers"""
    headers = dict(
        **{"RateLimit-Policy": (
            '"fast";q=10;w=1,'
            '"permin";q=50;w=60,'
            '"hourly";q=1000;w=3600;comment="primary", '
            '"daily";q=5000;w=86400'
        )},
        **{"RateLimit": '"hourly";r=999;t=3540'}
    )

    policies, ratelimit, policy_params = parse_ratelimit_headers(headers)
    
    # Verify we found the hourly policy
    assert ratelimit[0].value == "hourly"
    assert ratelimit[0].params["r"] == 999  # remaining
    assert ratelimit[0].params["t"] == 3540  # time to reset

    # Print all policies for verification
    for policy in policies:
        print("policy:", policy.value, "quota:", policy.params["q"], "window:", policy.params["w"])
    
    # Verify we found the matching policy parameters
    assert policy_params["q"] == 1000  # quota
    assert policy_params["w"] == 3600  # window


def test_partition_key_example():
    """Test RateLimit headers with partition key according to latest draft"""
    headers = dict(
        **{"RateLimit-Policy": '"peruser";q=100;w=60;pk=:cHsdsRa894==:'},
        **{"RateLimit": '"peruser";r=50;t=30;pk=:cHsdsRa894==:'}
    )
    
    policies, ratelimit, policy_params = parse_ratelimit_headers(headers)
    
    # Verify policy structure
    policy = policies[0]
    assert policy.value == "peruser"
    assert policy.params["q"] == 100
    assert policy.params["w"] == 60
    assert policy.params["pk"] == b'p{\x1d\xb1\x16\xbc\xf7'  # decoded base64
    
    # Verify ratelimit structure  
    current = ratelimit[0]
    assert current.value == "peruser"
    assert current.params["r"] == 50
    assert current.params["t"] == 30
    assert current.params["pk"] == b'p{\x1d\xb1\x16\xbc\xf7'  # decoded base64
    
    print("policy:", policy.value, "quota:", policy.params["q"], "window:", policy.params["w"])
    print("ratelimit:", current.value, "remaining:", current.params["r"], "reset:", current.params["t"])


# Test all functions when script is run directly
if __name__ == "__main__":
    test_functions = [
        test_ratelimit_policy,
        test_ratelimit_fields,
        test_policy_lookup,
        test_partition_key_example,
        test_quota_units_example,
        test_multiple_policies_example,
        test_basic_policy_example,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()

import pytest
import uuid
import functools
from getstream.base import StreamAPIException
from getstream.models import (
    SIPCallerConfigsRequest,
    SIPDirectRoutingRuleCallConfigsRequest,
)


def cleanup_sip_trunks(func):
    """Decorator that cleans up all test SIP trunks and routing rules after the test"""

    @functools.wraps(func)
    def wrapper(client, *args, **kwargs):
        try:
            return func(client, *args, **kwargs)
        finally:
            # Clean up all test routing rules first
            try:
                rules = client.video.list_sip_inbound_routing_rule().data.sip_inbound_routing_rules
                for rule in rules:
                    client.video.delete_sip_inbound_routing_rule(id=rule.id)
            except Exception:
                pass  # Ignore errors during cleanup

            # Clean up all test trunks
            trunks = client.video.list_sip_trunks().data.sip_trunks
            for trunk in trunks:
                client.video.delete_sip_trunk(id=trunk.id)

    return wrapper


def test_sip_server_connection(client):
    """Test if we can connect to the SIP server and see what happens"""
    print("Testing SIP server connection...")

    # Try to list trunks first
    try:
        response = client.video.list_sip_trunks()
        print(f"List response: {response}")
        print(f"Number of trunks: {len(response.data.sip_trunks)}")
    except Exception as e:
        print(f"List failed: {e}")
        print(f"Exception type: {type(e)}")
        if hasattr(e, "api_error"):
            print(f"API Error: {e.api_error}")
        if hasattr(e, "status_code"):
            print(f"Status code: {e.status_code}")
        return

    # Try to create a trunk with obviously invalid data
    try:
        response = client.video.create_sip_trunk(name="", numbers=[])
        print(f"Create with invalid data succeeded: {response}")
    except Exception as e:
        print(f"Create with invalid data failed as expected: {e}")
        print(f"Exception type: {type(e)}")
        if hasattr(e, "api_error"):
            print(f"API Error: {e.api_error}")
        if hasattr(e, "status_code"):
            print(f"Status code: {e.status_code}")
        if hasattr(e, "http_response"):
            print(f"Response text: {e.http_response.text}")


@cleanup_sip_trunks
def test_sip_trunk_crud_operations(client):
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    test_numbers = ["+1234567890", "+0987654321"]

    # Create
    create_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=test_numbers
    )
    created_trunk = create_response.data.sip_trunk

    assert created_trunk.name == trunk_name
    assert created_trunk.numbers == test_numbers

    # List and verify
    trunks = client.video.list_sip_trunks().data.sip_trunks
    found = [t for t in trunks if t.id == created_trunk.id]
    assert found and found[0].name == trunk_name

    # Update
    updated_name = f"updated-{trunk_name}"
    updated_numbers = ["+1111111111", "+2222222222"]
    update_response = client.video.update_sip_trunk(
        id=created_trunk.id,
        name=updated_name,
        numbers=updated_numbers,
    )
    assert update_response.data.sip_trunk.name == updated_name
    assert update_response.data.sip_trunk.numbers == updated_numbers

    # List and verify update
    trunks = client.video.list_sip_trunks().data.sip_trunks
    found = [t for t in trunks if t.id == created_trunk.id]
    assert found and found[0].name == updated_name

    # Delete
    client.video.delete_sip_trunk(id=created_trunk.id)

    # List and verify deletion
    trunks = client.video.list_sip_trunks().data.sip_trunks
    assert not any(t.id == created_trunk.id for t in trunks)


@cleanup_sip_trunks
def test_sip_trunk_multiple_operations(client):
    trunk_names = [f"test-trunk-multi-{uuid.uuid4()}" for _ in range(3)]
    test_numbers_sets = [
        ["+5555555555"],
        ["+6666666666", "+7777777777"],
        ["+8888888888", "+9999999999", "+0000000000"],
    ]

    created_trunks = []
    for name, numbers in zip(trunk_names, test_numbers_sets):
        response = client.video.create_sip_trunk(name=name, numbers=numbers)
        trunk = response.data.sip_trunk
        created_trunks.append(trunk)
        assert trunk.name == name
        assert trunk.numbers == numbers

    # List and verify all
    trunks = client.video.list_sip_trunks().data.sip_trunks
    for trunk in created_trunks:
        found = [t for t in trunks if t.id == trunk.id]
        assert found and found[0].name == trunk.name

    # Update one
    t0 = created_trunks[0]
    new_name = f"updated-{t0.name}"
    new_numbers = ["+1111111111"]
    upd = client.video.update_sip_trunk(id=t0.id, name=new_name, numbers=new_numbers)
    assert upd.data.sip_trunk.name == new_name
    assert upd.data.sip_trunk.numbers == new_numbers


@cleanup_sip_trunks
def test_sip_trunk_validation(client):
    """Test input validation for SIP trunk create and update operations"""

    # Test 1: Create with valid data first
    valid_name = f"test-trunk-{uuid.uuid4()}"
    valid_numbers = ["+1234567890"]

    create_response = client.video.create_sip_trunk(
        name=valid_name, numbers=valid_numbers
    )
    created_trunk = create_response.data.sip_trunk

    # Test 2: Create with empty name (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name="", numbers=valid_numbers)
    assert exc_info.value.status_code == 400
    assert "name is a required field" in exc_info.value.api_error.message
    assert "name" in exc_info.value.api_error.exception_fields

    # Test 3: Create with name too long (should fail - max=100)
    long_name = "a" * 101
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name=long_name, numbers=valid_numbers)
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 4: Create with empty numbers list (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name=valid_name, numbers=[])
    assert exc_info.value.status_code == 400
    assert "numbers is a required field" in exc_info.value.api_error.message
    assert "numbers" in exc_info.value.api_error.exception_fields

    # Test 5: Create with too many numbers (should fail - max=50)
    too_many_numbers = [f"+{i:010d}" for i in range(51)]
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name=valid_name, numbers=too_many_numbers)
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 6: Create with invalid phone number format (should fail - e164 validation)
    invalid_numbers = ["1234567890", "not-a-number", "+invalid"]
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name=valid_name, numbers=invalid_numbers)
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 7: Create with empty string in numbers (should fail - dive,required)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_trunk(name=valid_name, numbers=["+1234567890", ""])
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 8: Update with empty name (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(
            id=created_trunk.id, name="", numbers=valid_numbers
        )
    assert exc_info.value.status_code == 400
    assert "name is a required field" in exc_info.value.api_error.message
    assert "name" in exc_info.value.api_error.exception_fields

    # Test 9: Update with name too long (should fail - max=100)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(
            id=created_trunk.id, name=long_name, numbers=valid_numbers
        )
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 10: Update with empty numbers list (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(id=created_trunk.id, name=valid_name, numbers=[])
    assert exc_info.value.status_code == 400
    assert "numbers is a required field" in exc_info.value.api_error.message
    assert "numbers" in exc_info.value.api_error.exception_fields

    # Test 11: Update with too many numbers (should fail - max=50)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(
            id=created_trunk.id, name=valid_name, numbers=too_many_numbers
        )
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 12: Update with invalid phone number format (should fail - e164 validation)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(
            id=created_trunk.id, name=valid_name, numbers=invalid_numbers
        )
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 13: Update with empty string in numbers (should fail - dive,required)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_trunk(
            id=created_trunk.id, name=valid_name, numbers=["+1234567890", ""]
        )
    assert exc_info.value.status_code == 400
    # Note: We'll need to see what the actual error message is for this case

    # Test 14: Update with valid data (should succeed)
    updated_name = f"updated-{valid_name}"
    updated_numbers = ["+9876543210"]
    update_response = client.video.update_sip_trunk(
        id=created_trunk.id, name=updated_name, numbers=updated_numbers
    )
    assert update_response.data.sip_trunk.name == updated_name
    assert update_response.data.sip_trunk.numbers == updated_numbers


@cleanup_sip_trunks
def test_sip_inbound_routing_rule_crud_operations(client):
    """Test CRUD operations for SIP inbound routing rules"""

    # First create a trunk to use for the routing rule
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Create routing rule
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", role="user", custom_data={"test": "data"}
    )
    called_numbers = ["+1234567890"]
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    create_response = client.video.create_sip_inbound_routing_rule(
        name=rule_name,
        trunk_ids=[trunk.id],
        caller_configs=caller_configs,
        called_numbers=called_numbers,
        direct_routing_configs=direct_routing_configs,
    )
    created_rule = create_response.data

    assert created_rule.name == rule_name
    assert created_rule.trunk_ids == [trunk.id]
    assert created_rule.called_numbers == called_numbers
    assert created_rule.caller_configs.id == "test-caller-id"
    assert created_rule.caller_configs.role == "user"

    # List and verify
    rules = client.video.list_sip_inbound_routing_rule().data.sip_inbound_routing_rules
    found = [r for r in rules if r.id == created_rule.id]
    assert found and found[0].name == rule_name

    # Update
    updated_name = f"updated-{rule_name}"
    updated_called_numbers = ["+9876543210"]
    updated_caller_configs = SIPCallerConfigsRequest(
        id="updated-caller-id", role="admin", custom_data={"updated": "data"}
    )
    updated_direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="updated-call-id", call_type="default"
    )

    update_response = client.video.update_sip_inbound_routing_rule(
        id=created_rule.id,
        name=updated_name,
        called_numbers=updated_called_numbers,
        trunk_ids=[trunk.id],
        caller_configs=updated_caller_configs,
        direct_routing_configs=updated_direct_routing_configs,
    )
    updated_rule = update_response.data.sip_inbound_routing_rule

    assert updated_rule.name == updated_name
    assert updated_rule.called_numbers == updated_called_numbers
    assert updated_rule.caller_configs.id == "updated-caller-id"
    assert updated_rule.caller_configs.role == "admin"

    # List and verify update
    rules = client.video.list_sip_inbound_routing_rule().data.sip_inbound_routing_rules
    found = [r for r in rules if r.id == created_rule.id]
    assert found and found[0].name == updated_name

    # Delete
    client.video.delete_sip_inbound_routing_rule(id=created_rule.id)

    # List and verify deletion
    rules = client.video.list_sip_inbound_routing_rule().data.sip_inbound_routing_rules
    assert not any(r.id == created_rule.id for r in rules)


@cleanup_sip_trunks
def test_sip_inbound_routing_rule_requires_trunk(client):
    """Test that SIP inbound routing rules can only be created if a trunk exists"""

    # Try to create a routing rule without any trunks existing
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(id="test-caller-id", role="user")
    called_numbers = ["+1234567890"]
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    # This should fail because no trunks exist
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=["non-existent-trunk-id"],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Now create a trunk and try again
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # This should succeed now
    create_response = client.video.create_sip_inbound_routing_rule(
        name=rule_name,
        trunk_ids=[trunk.id],
        caller_configs=caller_configs,
        called_numbers=called_numbers,
        direct_routing_configs=direct_routing_configs,
    )
    created_rule = create_response.data

    assert created_rule.name == rule_name
    assert created_rule.trunk_ids == [trunk.id]

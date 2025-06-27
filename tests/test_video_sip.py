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
        id="test-caller-id", custom_data={"test": "data"}
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

    # List and verify
    rules = client.video.list_sip_inbound_routing_rule().data.sip_inbound_routing_rules
    found = [r for r in rules if r.id == created_rule.id]
    assert found and found[0].name == rule_name

    # Update
    updated_name = f"updated-{rule_name}"
    updated_called_numbers = ["+9876543210"]
    updated_caller_configs = SIPCallerConfigsRequest(
        id="updated-caller-id", custom_data={"updated": "data"}
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
    caller_configs = SIPCallerConfigsRequest(id="test-caller-id")
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


@cleanup_sip_trunks
def test_sip_inbound_routing_rule_validation(client):
    """Test input validation for SIP inbound routing rule create and update operations"""

    # First create a trunk to use for valid tests
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Test 1: Create with valid data first (baseline)
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
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

    # Test 2: Create with empty name (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name="",
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400
    assert "name is a required field" in exc_info.value.api_error.message
    assert "name" in exc_info.value.api_error.exception_fields

    # Test 3: Create with name too long (should fail - max=100)
    long_name = "a" * 101
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=long_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 4: Create with empty trunk_ids list (should fail - required, min=1)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400
    assert "trunk_ids is a required field" in exc_info.value.api_error.message
    assert "trunk_ids" in exc_info.value.api_error.exception_fields

    # Test 5: Create with too many trunk_ids (should fail - max=50)
    too_many_trunks = [f"trunk-{i}" for i in range(51)]
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=too_many_trunks,
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 6: Create with empty string in trunk_ids (should fail - dive,required)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id, ""],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 7: Create with empty caller_configs.id (should fail - required)
    invalid_caller_configs = SIPCallerConfigsRequest(id="")
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=invalid_caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400
    assert "id is a required field" in exc_info.value.api_error.message
    assert "caller_configs.id" in exc_info.value.api_error.exception_fields

    # Test 8: Create with caller_configs.id too long (should fail - max=255)
    long_id = "a" * 256
    invalid_caller_configs = SIPCallerConfigsRequest(id=long_id)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=invalid_caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 10: Create with empty direct_routing_configs.call_type (should fail - required)
    invalid_direct_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type=""
    )
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=invalid_direct_configs,
        )
    assert exc_info.value.status_code == 400
    assert "call_type is a required field" in exc_info.value.api_error.message
    assert (
        "direct_routing_configs.call_type" in exc_info.value.api_error.exception_fields
    )

    # Test 11: Create with direct_routing_configs.call_type too long (should fail - max=100)
    long_call_type = "a" * 101
    invalid_direct_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type=long_call_type
    )
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=invalid_direct_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 12: Create with empty direct_routing_configs.call_id (should fail - required)
    invalid_direct_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="", call_type="default"
    )
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=invalid_direct_configs,
        )
    assert exc_info.value.status_code == 400
    assert "call_id is a required field" in exc_info.value.api_error.message
    assert "direct_routing_configs.call_id" in exc_info.value.api_error.exception_fields

    # Test 13: Create with direct_routing_configs.call_id too long (should fail - max=255)
    long_call_id = "a" * 256
    invalid_direct_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id=long_call_id, call_type="default"
    )
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=invalid_direct_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 14: Create with too many called_numbers (should fail - max=50)
    too_many_called = [f"+{i:010d}" for i in range(51)]
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=too_many_called,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 15: Create with empty string in called_numbers (should fail - dive,required)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=["+1234567890", ""],
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 16: Create with too many caller_numbers (should fail - max=50)
    too_many_caller = [f"+{i:010d}" for i in range(51)]
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            caller_numbers=too_many_caller,
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 17: Create with empty string in caller_numbers (should fail - dive,required)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            caller_numbers=["+1234567890", ""],
            direct_routing_configs=direct_routing_configs,
        )
    assert exc_info.value.status_code == 400

    # Test 18: Create with both direct_routing_configs and pin_routing_configs (should fail)
    from getstream.models import SIPInboundRoutingRulePinConfigsRequest

    pin_routing_configs = SIPInboundRoutingRulePinConfigsRequest(pin_prompt="Enter PIN")
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
            pin_routing_configs=pin_routing_configs,
        )
    assert exc_info.value.status_code == 400
    assert (
        "only one of direct_routing_configs or pin_routing_configs can be set"
        in exc_info.value.api_error.message
    )

    # Test 19: Create with neither direct_routing_configs nor pin_routing_configs (should fail)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
        )
    assert exc_info.value.status_code == 400
    assert (
        "either direct_routing_configs or pin_routing_configs must be set"
        in exc_info.value.api_error.message
    )

    # Test 20: Update with valid data (should succeed)
    updated_name = f"updated-{rule_name}"
    updated_called_numbers = ["+9876543210"]
    updated_caller_configs = SIPCallerConfigsRequest(
        id="updated-caller-id", custom_data={"updated": "data"}
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
    assert update_response.data.sip_inbound_routing_rule.name == updated_name
    assert (
        update_response.data.sip_inbound_routing_rule.called_numbers
        == updated_called_numbers
    )


@cleanup_sip_trunks
def test_resolve_sip_inbound_no_trunks_defined(client):
    """Test resolve_sip_inbound when no trunks are defined"""

    # Test with valid request but no trunks exist
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1234567890",
            sip_trunk_number="+9876543210",
            sip_trunk_password="test-password",
        )
    print(f"Status code: {exc_info.value.status_code}")
    print(
        f"Error message: {exc_info.value.api_error.message if hasattr(exc_info.value, 'api_error') else 'No api_error'}"
    )
    print(f"Exception: {exc_info.value}")

    # For now, just check that it's an error (we'll adjust based on actual response)
    assert exc_info.value.status_code in [400, 403, 404]


@cleanup_sip_trunks
def test_resolve_sip_inbound_wrong_password(client):
    """Test resolve_sip_inbound with wrong password"""

    client.video.create_sip_trunk(
        name=f"test-trunk-{uuid.uuid4()}", numbers=["+1234567890"]
    )

    # Test with wrong password
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+0987654321",
            sip_trunk_number="+1234567890",
            sip_trunk_password="wrong-password",
        )
    assert exc_info.value.status_code == 404
    assert (
        "SIP trunk not found for the provided number and password"
        in exc_info.value.api_error.message
    )


@cleanup_sip_trunks
def test_resolve_sip_inbound_success(client):
    """Test resolve_sip_inbound with valid configuration"""

    trunk_response = client.video.create_sip_trunk(
        name=f"test-trunk-{uuid.uuid4()}", numbers=["+1234567890"]
    )
    trunk = trunk_response.data.sip_trunk

    # Create a routing rule
    rule_name = f"test-rule-{uuid.uuid4()}"
    call_configs = SIPCallerConfigsRequest(
        id="{{ uuid }}",
        custom_data={
            "sip": True,
        },
    )
    caller_configs = SIPCallerConfigsRequest(
        id="sip-{{caller_number}}", custom_data={"test": "data"}
    )
    called_numbers = ["+1234567890"]
    caller_numbers = ["+0987654321"]
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    client.video.create_sip_inbound_routing_rule(
        name=rule_name,
        call_configs=call_configs,
        trunk_ids=[trunk.id],
        caller_configs=caller_configs,
        called_numbers=called_numbers,
        caller_numbers=caller_numbers,
        direct_routing_configs=direct_routing_configs,
    )

    resolve_response = client.video.resolve_sip_inbound(
        sip_caller_number="+0987654321",
        sip_trunk_number="+1234567890",
        sip_trunk_password=trunk.password,
    )

    assert resolve_response.data.credentials.call_id == "test-call-id"
    assert resolve_response.data.credentials.call_type == "default"
    assert resolve_response.data.credentials.user_id == "sip-000987654321"
    assert resolve_response.data.credentials.token != ""
    assert resolve_response.data.sip_routing_rule.name == rule_name


@cleanup_sip_trunks
def test_resolve_sip_inbound_validation(client):
    """Test resolve_sip_inbound input validation"""

    # Test 1: Missing sip_trunk_number
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1234567890",
            sip_trunk_number="",  # Empty trunk number
            sip_trunk_password="test-password",
        )
    assert exc_info.value.status_code == 400
    assert "sip_trunk_number is a required field" in exc_info.value.api_error.message

    # Test 2: Missing sip_caller_number
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="",  # Empty caller number
            sip_trunk_number="+1234567890",
            sip_trunk_password="test-password",
        )
    assert exc_info.value.status_code == 400
    assert "sip_caller_number is a required field" in exc_info.value.api_error.message

    # Test 3: Missing sip_trunk_password
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1234567890",
            sip_trunk_number="+1234567890",
            sip_trunk_password="",  # Empty password
        )
    assert exc_info.value.status_code == 400
    assert "sip_trunk_password is a required field" in exc_info.value.api_error.message

    # Test 4: sip_trunk_number too long (max=255)
    long_number = "a" * 256
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1234567890",
            sip_trunk_number=long_number,
            sip_trunk_password="test-password",
        )
    assert exc_info.value.status_code == 400
    assert "sip_trunk_number" in exc_info.value.api_error.exception_fields

    # Test 5: sip_caller_number too long (max=255)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number=long_number,
            sip_trunk_number="+1234567890",
            sip_trunk_password="test-password",
        )
    assert exc_info.value.status_code == 400
    assert "sip_caller_number" in exc_info.value.api_error.exception_fields

    # Test 6: sip_trunk_password too long (max=255)
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1234567890",
            sip_trunk_number="+1234567890",
            sip_trunk_password=long_number,
        )
    assert exc_info.value.status_code == 400
    assert "sip_trunk_password" in exc_info.value.api_error.exception_fields


@cleanup_sip_trunks
def test_list_sip_inbound_routing_rules_returns_default_when_no_rules(client):
    """Test that list_sip_inbound_routing_rule returns the default rule when no rules exist"""

    # List rules when no rules exist
    response = client.video.list_sip_inbound_routing_rule()
    rules = response.data.sip_inbound_routing_rules

    # Should return exactly one rule - the default rule
    assert len(rules) == 1
    default_rule = rules[0]

    # Verify default rule properties
    assert default_rule.id == "default"
    assert default_rule.name == "default"
    assert default_rule.trunk_ids == []
    assert default_rule.called_numbers == []
    assert default_rule.caller_numbers is None  # Can be None for default rule

    # Verify default rule has correct direct routing configs
    assert default_rule.direct_routing_configs is not None
    assert default_rule.direct_routing_configs.call_type == "default"
    assert default_rule.direct_routing_configs.call_id == "sip-{{uuid}}"

    # Verify default rule has correct caller configs
    assert default_rule.caller_configs is not None
    assert default_rule.caller_configs.id == "sip-{{caller_number}}"
    assert default_rule.caller_configs.custom_data == {"name": "{{caller_number}}"}

    # Verify default rule has empty call configs
    assert default_rule.call_configs is not None
    assert default_rule.call_configs.custom_data == {}


@cleanup_sip_trunks
def test_list_sip_inbound_routing_rules_with_existing_rules(client):
    """Test that list_sip_inbound_routing_rule returns existing rules without default when rules exist"""

    # Create a trunk first
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Create a routing rule
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
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

    # List rules
    response = client.video.list_sip_inbound_routing_rule()
    rules = response.data.sip_inbound_routing_rules

    # Should return exactly one rule - the created rule (not the default)
    assert len(rules) == 1
    rule = rules[0]

    # Verify it's the created rule, not the default
    assert rule.id == created_rule.id
    assert rule.name == rule_name
    assert rule.id != "default"


@cleanup_sip_trunks
def test_resolve_sip_inbound_uses_default_rule_when_no_matching_rules(client):
    """Test that resolve_sip_inbound uses the default rule when no matching rules exist"""

    # Create a trunk
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Create a routing rule that won't match the request
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
    )
    called_numbers = ["+9876543210"]  # Different number
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    client.video.create_sip_inbound_routing_rule(
        name=rule_name,
        trunk_ids=[trunk.id],
        caller_configs=caller_configs,
        called_numbers=called_numbers,
        direct_routing_configs=direct_routing_configs,
    )

    # Resolve SIP inbound with numbers that don't match any rule
    response = client.video.resolve_sip_inbound(
        sip_caller_number="+1111111111",
        sip_trunk_number="+1234567890",
        sip_trunk_password=trunk.password,
    )

    # Should return the default rule
    assert response.data.sip_routing_rule.id == "default"
    assert response.data.sip_routing_rule.name == "default"
    assert response.data.sip_routing_rule.trunk_ids == []

    # Verify credentials are generated correctly
    credentials = response.data.credentials
    assert credentials.call_type == "default"
    assert credentials.call_id.startswith("sip-")
    assert credentials.user_id == "sip-001111111111"  # sanitized caller number
    assert credentials.user_custom_data == {"name": "001111111111"}


@cleanup_sip_trunks
def test_resolve_sip_inbound_uses_default_rule_when_no_trunks_exist(client):
    """Test that resolve_sip_inbound returns an error when no trunks exist"""

    # Try to resolve SIP inbound without any trunks
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.resolve_sip_inbound(
            sip_caller_number="+1111111111",
            sip_trunk_number="+1234567890",
            sip_trunk_password="some-password",
        )

    # Should return an error about trunk not found
    assert exc_info.value.status_code == 404
    assert "SIP trunk not found" in exc_info.value.api_error.message


@cleanup_sip_trunks
def test_cannot_create_rule_with_default_id(client):
    """Test that creating a rule with ID 'default' is prevented"""

    # Create a trunk first
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Try to create a rule with name 'default'
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
    )
    called_numbers = ["+1234567890"]
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    with pytest.raises(StreamAPIException) as exc_info:
        client.video.create_sip_inbound_routing_rule(
            name="default",  # This should be rejected
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )

    # Should return an error about reserved name
    assert exc_info.value.status_code == 400
    assert (
        "cannot create a SIP inbound routing rule with name"
        in exc_info.value.api_error.message
    )


@cleanup_sip_trunks
def test_cannot_update_default_rule(client):
    """Test that updating the default rule is prevented"""

    # Create a trunk first so we have a valid trunk_id
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Try to update the default rule
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
    )
    called_numbers = ["+1234567890"]
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    with pytest.raises(StreamAPIException) as exc_info:
        client.video.update_sip_inbound_routing_rule(
            id="default",  # This should be rejected
            name="updated-default",
            called_numbers=called_numbers,
            trunk_ids=[trunk.id],  # Use valid trunk_id
            caller_configs=caller_configs,
            direct_routing_configs=direct_routing_configs,
        )

    # Should return an error about system-managed rule
    assert exc_info.value.status_code == 400
    assert (
        "cannot update the default SIP inbound routing rule"
        in exc_info.value.api_error.message
    )


@cleanup_sip_trunks
def test_cannot_delete_default_rule(client):
    """Test that deleting the default rule is prevented"""

    # Try to delete the default rule
    with pytest.raises(StreamAPIException) as exc_info:
        client.video.delete_sip_inbound_routing_rule(id="default")

    # Should return an error about system-managed rule
    assert exc_info.value.status_code == 400
    assert (
        "cannot delete the default SIP inbound routing rule"
        in exc_info.value.api_error.message
    )


@cleanup_sip_trunks
def test_default_rule_behavior_with_multiple_rules(client):
    """Test default rule behavior when multiple rules exist but none match"""

    # Create a trunk
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Create multiple routing rules that won't match our request
    for i in range(3):
        rule_name = f"test-rule-{i}-{uuid.uuid4()}"
        caller_configs = SIPCallerConfigsRequest(
            id=f"test-caller-id-{i}", custom_data={"test": f"data-{i}"}
        )
        called_numbers = [f"+987654321{i}"]  # Different numbers
        direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
            call_id=f"test-call-id-{i}", call_type="default"
        )

        client.video.create_sip_inbound_routing_rule(
            name=rule_name,
            trunk_ids=[trunk.id],
            caller_configs=caller_configs,
            called_numbers=called_numbers,
            direct_routing_configs=direct_routing_configs,
        )

    # List rules - should return the 3 created rules (not the default)
    response = client.video.list_sip_inbound_routing_rule()
    rules = response.data.sip_inbound_routing_rules

    assert len(rules) == 3
    for rule in rules:
        assert rule.id != "default"

    # Resolve SIP inbound with numbers that don't match any rule
    response = client.video.resolve_sip_inbound(
        sip_caller_number="+1111111111",
        sip_trunk_number="+1234567890",
        sip_trunk_password=trunk.password,
    )

    # Should return the default rule
    assert response.data.sip_routing_rule.id == "default"
    assert response.data.sip_routing_rule.name == "default"


@cleanup_sip_trunks
def test_default_rule_priority_over_existing_rules(client):
    """Test that when no rules match, the default rule is used even if other rules exist"""

    # Create a trunk
    trunk_name = f"test-trunk-{uuid.uuid4()}"
    trunk_numbers = ["+1234567890"]

    trunk_response = client.video.create_sip_trunk(
        name=trunk_name, numbers=trunk_numbers
    )
    trunk = trunk_response.data.sip_trunk

    # Create a routing rule that matches the trunk but not the caller
    rule_name = f"test-rule-{uuid.uuid4()}"
    caller_configs = SIPCallerConfigsRequest(
        id="test-caller-id", custom_data={"test": "data"}
    )
    called_numbers = ["+1234567890"]  # Matches trunk
    caller_numbers = ["+9876543210"]  # Different caller
    direct_routing_configs = SIPDirectRoutingRuleCallConfigsRequest(
        call_id="test-call-id", call_type="default"
    )

    client.video.create_sip_inbound_routing_rule(
        name=rule_name,
        trunk_ids=[trunk.id],
        caller_configs=caller_configs,
        called_numbers=called_numbers,
        caller_numbers=caller_numbers,
        direct_routing_configs=direct_routing_configs,
    )

    # Resolve SIP inbound with caller that doesn't match the rule
    response = client.video.resolve_sip_inbound(
        sip_caller_number="+1111111111",  # Different caller
        sip_trunk_number="+1234567890",
        sip_trunk_password=trunk.password,
    )

    # Should return the default rule, not the existing rule
    assert response.data.sip_routing_rule.id == "default"
    assert response.data.sip_routing_rule.name == "default"

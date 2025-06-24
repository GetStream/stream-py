import pytest
import uuid
import functools
from getstream.base import StreamAPIException


def cleanup_sip_trunks(func):
    """Decorator that cleans up all test SIP trunks after the test"""

    @functools.wraps(func)
    def wrapper(client, *args, **kwargs):
        try:
            return func(client, *args, **kwargs)
        finally:
            # Clean up all test trunks
            trunks = client.video.list_sip_trunks().data.sip_trunks
            for trunk in trunks:
                if trunk.name.startswith("test-trunk"):
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

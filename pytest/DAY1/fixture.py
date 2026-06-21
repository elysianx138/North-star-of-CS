import pytest

@pytest.fixture
def hello():
    print("fixture is running")
    return "Hello,pytest!"

def test_use_fixture(hello):
    print(f"[test] have catched {hello}")
    assert len(hello) > 5

def test_another(hello):
    print(f"[test] have catched {hello} again!")
    assert "pytest" in hello
    
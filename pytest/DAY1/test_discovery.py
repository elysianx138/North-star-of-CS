def test_normal():
    assert 1 == 1

def not_a_normal():
    assert 1 == 2

class TestGroup:
    def test_in_class(self):
        assert "a" in "abc"

    def no_test_either(slef):
        assert False
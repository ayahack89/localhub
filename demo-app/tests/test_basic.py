from src.utils.helper import get_welcome_message

def test_welcome():
    res = get_welcome_message("Tester")
    assert "Tester" in res

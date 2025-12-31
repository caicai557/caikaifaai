import pytest
from council.utils.yasl import YASLSerializer


def test_yasl_dump_load():
    """Test basic serialization and deserialization"""
    context = {
        "agent": "Coder",
        "task": "Implement feature X",
        "history": ["step1", "step2"],
        "metadata": {"confidence": 0.95},
    }

    yasl_str = YASLSerializer.dump(context)
    assert "agent: Coder" in yasl_str
    assert "task: Implement feature X" in yasl_str

    loaded = YASLSerializer.load(yasl_str)
    assert loaded == context


def test_yasl_chinese_support():
    """Test unicode support (Chinese characters)"""
    context = {"summary": "这是一个测试", "details": "包含中文内容"}

    yasl_str = YASLSerializer.dump(context)
    # Ensure it's not escaped like \u8fd9
    assert "这是一个测试" in yasl_str

    loaded = YASLSerializer.load(yasl_str)
    assert loaded == context


def test_yasl_invalid_input():
    """Test error handling"""
    with pytest.raises(ValueError):
        YASLSerializer.load("invalid: yaml: content: [")


def test_yasl_empty():
    """Test empty input"""
    assert YASLSerializer.load("") == {}
    assert YASLSerializer.load("null") == {}

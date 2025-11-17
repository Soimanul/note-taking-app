import pytest
from core.tasks import get_parser


def test_get_parser_supported_and_unsupported():
    # Supported types
    p_txt = get_parser("txt")
    assert p_txt is not None

    # Unsupported type should raise ValueError
    with pytest.raises(ValueError):
        get_parser("unknown_ext")

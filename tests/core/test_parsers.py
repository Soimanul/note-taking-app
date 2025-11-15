import importlib.util
import importlib
import pytest


def test_get_parser_supported_and_unsupported():
    # Import get_parser dynamically to support both layouts
    if importlib.util.find_spec("backend"):
        mod = importlib.import_module("backend.core.tasks")
    else:
        mod = importlib.import_module("core.tasks")

    # Supported types
    p_txt = mod.get_parser("txt")
    assert p_txt is not None

    # Unsupported type should raise ValueError
    with pytest.raises(ValueError):
        mod.get_parser("unknown_ext")

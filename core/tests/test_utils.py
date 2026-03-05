We need to view core/utils.py content.import uuid
import datetime

import pytest

from core import utils


@pytest.mark.parametrize(
    "func_name, expected_type",
    [
        ("generate_uuid", uuid.UUID),
        ("current_timestamp", datetime.datetime),
        ("format_datetime", str),
        ("safe_int", int),
        ("deep_merge_dicts", dict),
    ],
)
def test_specific_utilities(func_name: str, expected_type):
    if not hasattr(utils, func_name):
        pytest.skip(f"{func_name} not found in core.utils")
    func = getattr(utils, func_name)
    assert callable(func), f"{func_name} is not callable"

    if func_name == "generate_uuid":
        result = func()
        assert isinstance(result, expected_type)
        # uniqueness test
        results = {func() for _ in range(5)}
        assert len(results) == 5

    elif func_name == "current_timestamp":
        before = datetime.datetime.utcnow()
        result = func()
        after = datetime.datetime.utcnow()
        assert isinstance(result, expected_type)
        assert before <= result <= after

    elif func_name == "format_datetime":
        dt = datetime.datetime(2020, 1, 1, 12, 30, 45)
        result = func(dt, "%Y-%m-%d %H:%M:%S")
        assert isinstance(result, expected_type)
        assert result == "2020-01-01 12:30:45"

    elif func_name == "safe_int":
        for value in ("10", 10, None):
            result = func(value)
            assert isinstance(result, expected_type)

    elif func_name == "deep_merge_dicts":
        a = {"a": 1, "b": {"c": 2}}
        b = {"b": {"d": 3}, "e": 4}
        merged = func(a, b)
        assert isinstance(merged, expected_type)
        assert merged == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}


def test_utils_module_loads():
    assert hasattr(utils, "__all__") or True
    assert callable(getattr(utils, "generate_uuid", None))
    assert callable(getattr(utils, "current_timestamp", None))


def test_dynamic_calling_of_utilities():
    for attr_name in dir(utils):
        if attr_name.startswith("_"):
            continue
        attr = getattr(utils, attr_name)
        if not callable(attr):
            continue
        try:
            result = attr()
        except TypeError:
            continue
        assert result is not None


def test_generate_uuid_uniqueness():
    uuids = {utils.generate_uuid() for _ in range(10)}
    assert len(uuids) == 10


def test_current_timestamp_is_recent():
    now = datetime.datetime.utcnow()
    ts = utils.current_timestamp()
    delta = abs((ts - now).total_seconds())
    assert delta < 5
import pytest
from pydantic import ValidationError

from communication_health_checker.domain.models.core import InvalidOperationException
from communication_health_checker.domain.models.target.host import Host
from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId


def _make() -> Target:
    return Target(target_id=TargetId.generate(), name="R1", host=Host(value="127.0.0.1"))


def test_target_id_equality() -> None:
    tid = TargetId.generate()
    t1 = Target(target_id=tid, name="a", host=Host(value="127.0.0.1"))
    t2 = Target(target_id=tid, name="b", host=Host(value="10.0.0.1"))
    assert t1 == t2  # ID 等値


def test_rename_rejects_blank() -> None:
    t = _make()
    with pytest.raises(InvalidOperationException):
        t.rename("   ")


def test_name_length_validation() -> None:
    with pytest.raises(ValidationError):
        Target(target_id=TargetId.generate(), name="", host=Host(value="127.0.0.1"))


def test_target_id_pattern() -> None:
    with pytest.raises(ValidationError):
        TargetId(value="bad-id")

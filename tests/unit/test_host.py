import pytest
from pydantic import ValidationError

from communication_health_checker.domain.models.target.host import Host


@pytest.mark.parametrize("value", ["192.168.0.1", "10.0.0.255", "::1", "example.com", "host-1.local"])
def test_valid_hosts(value: str) -> None:
    assert str(Host(value=value)) == value


@pytest.mark.parametrize("value", ["", "  ", "999.999.999.999 ", "bad host", "-leading.com", "a..b"])
def test_invalid_hosts(value: str) -> None:
    with pytest.raises(ValidationError):
        Host(value=value)


def test_host_trims_whitespace() -> None:
    assert str(Host(value="  192.168.0.1  ")) == "192.168.0.1"

import ipaddress
import re

from pydantic import field_validator

from communication_health_checker.domain.models.core import ValueObject

# RFC 1123 ホスト名（ラベル毎に 1-63 文字、全体 253 文字以内）
_HOSTNAME_RE = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$")


class Host(ValueObject):
    """ターゲットのホスト（IPv4 / IPv6 / ホスト名）を表す値オブジェクト。"""

    value: str

    @field_validator("value")
    @classmethod
    def _validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("host must not be empty")
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        # ドットで区切られた数値のみの文字列は IP のタイプミスとみなし拒否する
        # （例: "999.999.999.999"）。正当なホスト名は数値オンリーにはならない。
        if re.fullmatch(r"\d+(\.\d+)+", v):
            raise ValueError(f"invalid IP address: {v}")
        if _HOSTNAME_RE.match(v):
            return v
        raise ValueError(f"invalid host: {v}")

    def __str__(self) -> str:
        return self.value

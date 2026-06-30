class DomainException(Exception):
    """ドメイン例外の基底。"""


class EntityNotFoundException(DomainException):
    """指定エンティティが存在しない。"""


class InvalidOperationException(DomainException):
    """現在の状態では許可されない操作。"""


class InvariantViolationException(DomainException):
    """集約の不変条件違反。"""

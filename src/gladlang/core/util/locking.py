"""No-op lock – used when threading is disabled to avoid overhead."""


class _NoLock:
    __slots__ = ()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(repr=False, eq=False)
class _Change[T]:
    name: str
    old: T
    new: T


def document_change[T](
    obj: object,
    attribute_name: str,
    value: T | None,
) -> _Change[T] | None:
    if value is None:
        return None

    old = getattr(obj, attribute_name)
    setattr(obj, attribute_name, value)
    new = getattr(obj, attribute_name)
    if old == new:
        return None

    return _Change(attribute_name, old, new)


def combine_message(
    *changes: _Change | None,
    prefix: str | None = None,
) -> str:
    combined = [
        f"Changed **{c.name.replace("_", " ")}** "
        f"from **{c.old}** "
        f"to **{c.new}**"
        for c in changes
        if c
    ]
    combined = "\n".join(combined) if combined else "No changes."
    if prefix:
        return f"{prefix}:\n{combined}"
    return combined

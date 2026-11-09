"""The item-role mapping of the ECSF: 150 distinct statements in 227 role-statement rows (Section 3.1 of the paper).

Roles share statements, so the mapping is kept per statement: each statement lists every role it belongs to, with
the role's name, the subsection (skills or knowledge) and the text of the statement.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping


class RoleMapping(Mapping):
    """{statement id: [{role, role_name, subsection, statement}, ...]}, read-only, in the order of the framework."""

    def __init__(self, rows):
        mapping = defaultdict(list)
        for rf_id, role, role_name, subsection, statement in rows:
            mapping[rf_id].append({"role": role, "role_name": role_name, "subsection": subsection,
                                   "statement": statement})
        self._mapping = dict(mapping)

    @classmethod
    def read(cls, storage) -> "RoleMapping":
        """The mapping as stored in the database."""
        rows = storage.framework.item_roles()
        if not rows:
            raise ValueError("the item-role mapping is empty; load the reference framework first")
        return cls(rows)

    def __getitem__(self, rf_id):
        return self._mapping[rf_id]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def statements_per_role(self) -> dict:
        """{role: {statement id, ...}} over the 227 rows."""
        per_role = defaultdict(set)
        for rf_id, roles in self._mapping.items():
            for role in roles:
                per_role[role["role"]].add(rf_id)
        return dict(per_role)

    def role_names(self) -> dict:
        """{role: ECSF name of the role}."""
        return {entry["role"]: entry["role_name"] for entries in self._mapping.values() for entry in entries}

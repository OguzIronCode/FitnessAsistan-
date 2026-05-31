"""Minimal in-memory Supabase-like stub for offline development.

This implements a very small subset of the supabase client API used
throughout the project: `auth.sign_up`, `auth.sign_in_with_password`,
`auth.get_user`, `table(...).select/insert/update/delete/upsert/eq/ilike/order/limit/single`
and `rpc` for the small stored-proc used (`increment_total_sets`).

It intentionally avoids any network calls and persists data only in
process memory. IDs are UUID strings. This is suitable for local
offline mode and for removing external API calls from the codebase.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from copy import deepcopy
from typing import Any, Dict, List, Optional


def _new_id() -> str:
    return uuid.uuid4().hex


class Result:
    def __init__(self, data: Any):
        self.data = data


class LocalAuth:
    def __init__(self, client: "LocalSupabaseClient"):
        self._client = client

    def sign_up(self, payload: Dict[str, Any]):
        email = payload.get("email")
        password = payload.get("password")
        users = self._client._tables.setdefault("users", [])
        # already exists?
        for u in users:
            if u.get("email") == email:
                return SimpleNamespace(user=None, session=None)

        uid = _new_id()
        user = {"id": uid, "email": email, "password": password}
        users.append(deepcopy(user))
        token = _new_id()
        self._client._sessions[token] = uid
        return SimpleNamespace(user=SimpleNamespace(id=uid), session=SimpleNamespace(access_token=token))

    def sign_in_with_password(self, payload: Dict[str, Any]):
        email = payload.get("email")
        password = payload.get("password")
        users = self._client._tables.setdefault("users", [])
        for u in users:
            if u.get("email") == email and u.get("password") == password:
                uid = u.get("id")
                token = _new_id()
                self._client._sessions[token] = uid
                return SimpleNamespace(user=SimpleNamespace(id=uid), session=SimpleNamespace(access_token=token))
        return SimpleNamespace(user=None, session=None)

    def sign_out(self):
        # no-op for offline stub
        return True

    def get_user(self, token: str):
        uid = self._client._sessions.get(token)
        if not uid:
            return SimpleNamespace(user=None)
        return SimpleNamespace(user=SimpleNamespace(id=uid))


class Query:
    def __init__(self, client: "LocalSupabaseClient", table: str):
        self.client = client
        self.table = table
        self._select = None
        self._filters: List[tuple] = []
        self._limit = None
        self._order = None
        self._single = False
        self._op = "select"
        self._payload = None
        self._upsert_on = None

    def select(self, fields: Optional[str] = None):
        self._select = fields
        return self

    def insert(self, payload: Dict[str, Any]):
        self._op = "insert"
        self._payload = deepcopy(payload)
        return self

    def update(self, payload: Dict[str, Any]):
        self._op = "update"
        self._payload = deepcopy(payload)
        return self

    def delete(self):
        self._op = "delete"
        return self

    def upsert(self, payload: Dict[str, Any], on_conflict: Optional[str] = None):
        self._op = "upsert"
        self._payload = deepcopy(payload)
        self._upsert_on = on_conflict
        return self

    def eq(self, field: str, value: Any):
        self._filters.append(("eq", field, value))
        return self

    def ilike(self, field: str, pattern: str):
        self._filters.append(("ilike", field, pattern))
        return self

    def order(self, field: str, desc: bool = False):
        self._order = (field, desc)
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        tbl = self.client._tables.setdefault(self.table, [])

        def matches(row: Dict[str, Any]) -> bool:
            for op, field, val in self._filters:
                rv = row.get(field)
                if op == "eq":
                    if rv != val:
                        return False
                elif op == "ilike":
                    # pattern like %term% — do simple case-insensitive contains
                    try:
                        term = val.strip("%\n\r ")
                        if term.lower() not in (str(rv or "")).lower():
                            return False
                    except Exception:
                        return False
            return True

        if self._op == "select":
            rows = [deepcopy(r) for r in tbl if matches(r)]
            # support simple join hint: '*, programs(title)'
            if self._select and "programs(" in self._select:
                # lookup programs table by program_id
                programs = {p.get("id"): p for p in self.client._tables.get("programs", [])}
                for r in rows:
                    pid = r.get("program_id") or r.get("programs_id")
                    if pid and programs.get(pid):
                        r["programs"] = {"title": programs[pid].get("title")}

            if self._order:
                key, desc = self._order
                rows.sort(key=lambda x: x.get(key), reverse=bool(desc))
            if self._limit is not None:
                rows = rows[: self._limit]
            if self._single:
                return Result(rows[0] if rows else None)
            return Result(rows)

        if self._op == "insert":
            row = deepcopy(self._payload)
            if "id" not in row:
                row["id"] = _new_id()
            tbl.append(row)
            return Result([deepcopy(row)])

        if self._op == "delete":
            removed = [deepcopy(r) for r in tbl if matches(r)]
            self.client._tables[self.table] = [r for r in tbl if not matches(r)]
            return Result(removed)

        if self._op == "update":
            updated = []
            for r in tbl:
                if matches(r):
                    r.update(self._payload)
                    updated.append(deepcopy(r))
            return Result(updated)

        if self._op == "upsert":
            # on_conflict: comma separated fields
            if not self._upsert_on:
                # behave as insert
                return Query(self.client, self.table).insert(self._payload).execute()
            keys = [k.strip() for k in (self._upsert_on or "").split(",")]
            found = None
            for r in tbl:
                if all(r.get(k) == self._payload.get(k) for k in keys):
                    found = r
                    break
            if found:
                found.update(self._payload)
                return Result([deepcopy(found)])
            else:
                return Query(self.client, self.table).insert(self._payload).execute()

        return Result(None)


class LocalSupabaseClient:
    def __init__(self):
        # in-memory tables
        self._tables: Dict[str, List[Dict[str, Any]]] = {}
        # sessions: token -> user_id
        self._sessions: Dict[str, str] = {}
        self.auth = LocalAuth(self)

        # seed with a demo user and a simple profile and food items
        demo_uid = "demo-user-1"
        self._tables.setdefault("users", []).append({
            "id": demo_uid,
            "email": "demo@example.com",
            "password": "demo",
        })
        self._tables.setdefault("profiles", []).append({
            "id": demo_uid,
            "full_name": "Demo Kullanici",
            "age": 30,
            "weight_kg": 75,
            "goal": "maintain",
            "calorie_target": 2500,
            "protein_target": 150,
            "carb_target": 300,
            "fat_target": 70,
            "diet_preference": "balanced",
        })

        # sample foods (ids are ints to mimic wger ids)
        self._tables.setdefault("foods", []).extend([
            {"id": 1001, "name": "Chicken Breast", "name_tr": "Tavuk Göğsü", "calories": 165, "protein": 31.0, "carbohydrate": 0.0, "fat": 3.6},
            {"id": 1002, "name": "Oatmeal", "name_tr": "Yulaf Ezmesi", "calories": 389, "protein": 16.9, "carbohydrate": 66.3, "fat": 6.9},
            {"id": 1003, "name": "Banana", "name_tr": "Muz", "calories": 89, "protein": 1.1, "carbohydrate": 22.8, "fat": 0.3},
        ])

        # sample programs for join-like responses
        self._tables.setdefault("programs", []).extend([
            {"id": "bb-fullgym-beg", "title": "Bodybuilding Başlangıç"},
            {"id": "pow-fullgym-beg", "title": "Başlangıç Güç Programı"},
        ])

    def table(self, name: str) -> Query:
        return Query(self, name)

    def rpc(self, name: str, params: Dict[str, Any]):
        # implement increment_total_sets
        if name == "increment_total_sets":
            wid = params.get("wid")
            tbl = self._tables.setdefault("workouts", [])
            for r in tbl:
                if r.get("id") == wid:
                    r["total_sets"] = (r.get("total_sets") or 0) + 1
                    return Result([deepcopy(r)])
        return Result(None)


# create two clients: supabase (anon) and supabase_admin (admin)
supabase = LocalSupabaseClient()
supabase_admin = supabase

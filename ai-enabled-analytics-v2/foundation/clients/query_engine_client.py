"""Query Engine API client (platform capability).

Stands in for Analytics Foundation's Query Engine Database Service: create/delete
the databases and tables that back a workspace's analytical data. Backed by an
in-memory stub today; a real deployment would call the endpoints in
``apis/qe_api.yml`` instead. Row-level reads against these tables are a separate
concern handled over JDBC - see ``lanadb_query`` and ``datawarehouse`` (the mocked
StarRocks access).
"""

from typing import Any

_databases: dict[str, dict[str, list[dict[str, Any]]]] = {}


def database_exists(database_name: str) -> bool:
    return database_name in _databases


def create_database(database_name: str, username: str | None = None, password: str | None = None) -> None:
    _databases.setdefault(database_name, {})


def delete_database(database_name: str) -> None:
    _databases.pop(database_name, None)


def get_table_names(database_name: str) -> list[str]:
    try:
        return list(_databases[database_name].keys())
    except KeyError as exc:
        raise KeyError(f"Unknown database: {database_name}") from exc


def create_tables(database_name: str, tables: list[dict[str, Any]]) -> None:
    database = _databases.setdefault(database_name, {})
    for table in tables:
        database[table["name"]] = table.get("columns", [])


def delete_table(database_name: str, table_name: str) -> None:
    _databases.get(database_name, {}).pop(table_name, None)

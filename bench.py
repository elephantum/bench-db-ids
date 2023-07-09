import uuid

import pytest
import snowflake
import ulid
from cyksuid.v2 import ksuid
from sqlalchemy import Column, MetaData, String, Table, create_engine, text
from uuid_extensions import uuid7str

metadata = MetaData()
test_table = Table(
    "test_table",
    metadata,
    Column("id", String, primary_key=True),
    Column("data", String),
)


@pytest.fixture
def db_sqlite():
    eng = create_engine("sqlite:///db.sqlite")

    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE test_table (
                    id VARCHAR(255) PRIMARY KEY, 
                    data VARCHAR(255)
                )
                WITHOUT ROWID
                """
            )
        )

    yield eng
    eng.dispose()

    # delete the file
    import os

    os.remove("db.sqlite")


@pytest.fixture
def db_postgres():
    eng = create_engine("postgresql://postgres:postgres@postgres:5432/postgres")

    with eng.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE test_table (
                    id VARCHAR(255) PRIMARY KEY, 
                    data VARCHAR(255)
                )
                """
            )
        )

    yield eng

    with eng.begin() as conn:
        conn.execute(text("DROP TABLE test_table"))

    eng.dispose()


snowflake_gen = snowflake.SnowflakeGenerator(1)

ID_GENERATORS = [
    pytest.param(uuid.uuid4, id="uuid4"),
    pytest.param(uuid7str, id="uuid7"),
    pytest.param(ulid.new, id="ulid"),
    pytest.param(lambda: next(snowflake_gen), id="snowflake"),
    pytest.param(ksuid, id="ksuid"),
]


@pytest.mark.parametrize("id_generator", ID_GENERATORS)
def test_id_generator(benchmark, id_generator):
    benchmark(id_generator)


@pytest.mark.parametrize("id_generator", ID_GENERATORS)
def test_sqlite_performance(benchmark, db_sqlite, id_generator):
    @benchmark
    def run():
        data = [{"id": str(id_generator()), "data": "some data"} for _ in range(1_000)]

        with db_sqlite.begin() as conn:
            conn.execute(test_table.insert(), data)


@pytest.mark.parametrize("id_generator", ID_GENERATORS)
def test_postgres_performance(benchmark, db_postgres, id_generator):
    @benchmark
    def run():
        data = [{"id": str(id_generator()), "data": "some data"} for _ in range(1_000)]

        with db_postgres.begin() as conn:
            conn.execute(test_table.insert(), data)

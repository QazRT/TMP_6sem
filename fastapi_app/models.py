from sqlalchemy import Table, Column, Integer, String
from database import metadata

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50)),
    Column("email", String(50), unique=True)
)

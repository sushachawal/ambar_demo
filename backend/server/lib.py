from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2
from psycopg2 import pool
import os
import sys
from functools import wraps
from flask import request


def env_var(name):
    if name in os.environ.keys():
        return os.environ[name]
    else:
        raise Exception("Missing environment variable " + name)


def init_connection_pool():
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=3,
        maxconn=15,
        database=env_var("PG_DATABASE"),
        user=env_var("PG_USERNAME"),
        password=env_var("PG_PASSWORD"),
        host=env_var("PG_HOST"),
        port=int(env_var("PG_PORT")),
        connect_timeout=3
    )


def db_setup():
    conn = psycopg2.connect(
        database=env_var("PG_DATABASE"),
        user=env_var("PG_USERNAME"),
        password=env_var("PG_PASSWORD"),
        host=env_var("PG_HOST"),
        port=int(env_var("PG_PORT")),
        connect_timeout=3
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("Creating tables", file=sys.stdout)
    cursor.execute(
        f"""
                CREATE TABLE IF NOT EXISTS event_credit_card (
                    id SERIAL PRIMARY KEY,
                    request_body TEXT,
                    request_body_hash TEXT UNIQUE,
                    processed_at timestamp default current_timestamp
                );
        """
    )
    cursor.execute(
        f"""
                CREATE TABLE IF NOT EXISTS credit_card_fraud (
                    id SERIAL PRIMARY KEY,
                    account_number integer,
                    amount TEXT,
                    authorization_id TEXT,
                    currency TEXT,
                    event_id TEXT UNIQUE
                );
        """
    )
    cursor.execute(
        f"""
                CREATE TABLE IF NOT EXISTS event_shipping (
                    id SERIAL PRIMARY KEY,
                    request_body TEXT,
                    request_body_hash TEXT UNIQUE,
                    processed_at timestamp default current_timestamp
                );
        """
    )
    cursor.execute(
        f"""
                CREATE TABLE IF NOT EXISTS shipping_return (
                    id SERIAL PRIMARY KEY,
                    account_number integer,
                    shipment_id TEXT,
                    return_reason TEXT,
                    event_id TEXT UNIQUE
                );
        """
    )
    print("Created tables", file=sys.stdout)
    cursor.close()
    conn.close()


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (
                auth.username == env_var("DESTINATION_USERNAME") and auth.password == env_var("DESTINATION_PASSWORD")):
            return 'Unauthorized', 401
        return f(*args, **kwargs)

    return decorated

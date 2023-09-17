from collections import namedtuple
from sqlalchemy import text

from . import conn
from .base import ORMBase
from .ops import Operation
from .utils import new_unique_key

__version__ = "0.0.1"
__author__ = "Akhlak Mahmood"

ENG = None
SSH = None
SES = None

class ssh:
    host = ''
    port = 22
    user = ''
    pswd = ''

class db:
    host = 'localhost'
    port = 5254
    user = 'admin'
    pswd = ''
    name = 'postgres'

def load_settings():
    from .. import sett
    ssh.host = sett.PostGres.ssh_host
    ssh.port = 22 if sett.PostGres.ssh_port is None else sett.PostGres.ssh_port
    ssh.user = sett.PostGres.ssh_user
    ssh.pswd = sett.PostGres.ssh_pass
    db.host = sett.PostGres.db_host
    db.port = sett.PostGres.db_port
    db.user = sett.PostGres.db_user
    db.pswd = sett.PostGres.db_pswd
    try:
        db.name = sett.Run.databaseName
    except:
        db.name = sett.PostGres.db_name


def connect(database = None):
    global SSH, ENG, SES

    if database is not None:
        db.name = database

    if SSH is None:
        SSH = conn.ssh_tunnel(
            ssh.host, ssh.port, ssh.user, ssh.pswd, db.host, db.port)

    if ENG is None:
        ENG = conn.setup_engine(
            db.host, db.port, db.user, db.pswd, db.name, proxy=SSH)

    if SES is None:
        SES = conn.new_session(ENG)

    return SES


def disconnect():
    global SSH, ENG, SES
    if SES is not None:
        SES.close()
    if SSH is not None:
        SSH.stop()

def engine():
    connect()
    return ENG

def raw_sql(query : str, params = {}) -> list[namedtuple]:
    """
        Execute a raw sql query on the database.
        
        Ex. result = raw_sql('SELECT * FROM my_table WHERE my_column = :val', {'val': 5})

        Returns a list of rows.
    """
    results= SES.execute(text(query), params)

    Row = namedtuple('Row', results.keys())
    return [Row(*r) for r in results.fetchall()]

from app.models.user import UserModel
from app.utils.config import Config
from botocore.session import Session
from pynamodb.models import Model
from pynamodb.connection.base import Connection


def patch_connection_session(profile=None):
    @property
    def session(self):
        if getattr(self._local, 'session', None) is None:
            self._local.session = Session(profile=profile)
        return self._local.session
    Connection.session = session

def create_table_if_not_exists(model : Model):
    if not model.exists():
        model.create_table(read_capacity_units=20, write_capacity_units=10, wait=True)
        print(f"Table {model.Meta.table_name} created")
    else:
        print(f"Table {model.Meta.table_name} already exists")

def init_db():
    patch_connection_session(Config.DB_PROFILE)
    create_table_if_not_exists(UserModel)
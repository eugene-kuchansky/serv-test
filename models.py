import peewee as pw
from tornado.web import RequestHandler
from datetime import date
from settings import db_name

db = pw.SqliteDatabase(db_name, threadlocals=True)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Server(BaseModel):
    server_id = pw.PrimaryKeyField(primary_key=True)
    tenant_id = pw.IntegerField()
    status = pw.CharField(default='pending')
    name = pw.CharField()
    date_created = pw.DateField(default=date.today())

    class Meta:
        indexes = (
            (('tenant_id', 'server_id'), True),
            (['tenant_id'], False),
            (['server_id'], False),
        )


def init_db():
    db.connect()
    db.create_tables([Server], True)
    db.close()

def clear_db():
    db.connect()
    q = Server.delete()
    q.execute()
    db.close()


class DbHandler(RequestHandler):
    def prepare(self):
        db.connect()
        return super(DbHandler, self).prepare()

    def on_finish(self):
        if not db.is_closed():
            db.close()
        return super(DbHandler, self).on_finish()


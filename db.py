from peewee import *
import jdatetime
from datetime import datetime
from playhouse.shortcuts import ReconnectMixin

class DB(ReconnectMixin, MySQLDatabase):
    pass

db = DB('robot', user='root', password='a8H8HI',host='localhost', port=3306,charset='utf8mb4')

class Base(Model):
    class Meta:
        database = db

class Users(Base):
    user_id = BigIntegerField(primary_key=True)
    phone = TextField(null=True)
    coin = IntegerField(default=0)
    ban = BooleanField(default=False)
    timestamp = TimestampField(null=True)
    joinDate = CharField(default=jdatetime.datetime.now().strftime('%Y/%m/%d'))

class Servers(Base):
    name = TextField()
    address = TextField()
    username = TextField()
    password = TextField()
    status = BooleanField(default=True)
    service = IntegerField()
    remark = TextField()
    port = IntegerField()

class Categorys(Base):
    name = TextField()
    price = IntegerField()
    limitip = IntegerField()
    size = IntegerField()
    days = IntegerField()
    server = TextField()
    status = BooleanField(default=True)

class Services(Base):
    id = IntegerField()
    user = BigIntegerField()
    remark = TextField()
    expiryTime = BigIntegerField()
    total = IntegerField()
    port = IntegerField()
    protocol = TextField()
    email = TextField()
    limitIp = IntegerField()
    tag = TextField()
    price = IntegerField()
    created_at = DateTimeField(default=datetime.now())
    status = BooleanField(default=True)

class send_all(Base):
    user = BigIntegerField()
    message_id = IntegerField()
    xsends = IntegerField(default= 0)
    limit = IntegerField(default= 100)
    xoffset = IntegerField(default= 0)
    active = IntegerField(default= 0)
    text = TextField(null=True)
    type = TextField()

class Process(Base):
    user = BigIntegerField()
    server = IntegerField()
    category = IntegerField()
    price = IntegerField()
    status = BooleanField(null=True)

print(db.connect())
db.create_tables([Users,Servers,Services,Categorys,send_all,Process])
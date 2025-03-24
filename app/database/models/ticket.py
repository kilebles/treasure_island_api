from tortoise import fields
from tortoise.models import Model


class Ticket(Model):
    id = fields.BigIntField(pk=True)
    lottery_id = fields.ForeignKeyField("models.Lottery", related_name="tickets")
    owner_id = fields.ForeignKeyField("models.User", related_name="tickets", null=True)
    number = fields.IntField()
    name = fields.CharField(max_length=255)
    image = fields.CharField(max_length=255)
    address = fields.CharField(max_length=255)
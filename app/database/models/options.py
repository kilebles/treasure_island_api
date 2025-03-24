from tortoise import fields
from tortoise.models import Model


class Option(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    key = fields.CharField(max_length=64)
    value = fields.TextField()
    
    class Meta:
        app = "app"
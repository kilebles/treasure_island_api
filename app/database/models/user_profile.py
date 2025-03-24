from tortoise import fields
from tortoise.models import Model


class UserProfile(Model):
    id = fields.BigIntField(pk=True)
    user_id = fields.OneToOneField("models.User", related_name="profile")
    phone_number = fields.CharField(max_length=32, null=True)
    full_name = fields.CharField(max_length=255, null=True)
    inn = fields.IntField(null=True)
    wallet_address = fields.CharField(max_length=255, null=True)
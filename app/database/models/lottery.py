from tortoise import fields
from tortoise.models import Model


class Lottery(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    banner = fields.CharField(max_length=255)
    short_description = fields.CharField(max_length=255)
    total_sum = fields.IntField()
    event_date = fields.DatetimeField()
    is_active = fields.BooleanField(default=False)
    collection_name = fields.CharField(max_length=255)
    collection_address = fields.CharField(max_length=255)
    collection_chain = fields.CharField(max_length=255)
    ticket_template = fields.TextField(null=True)
    ticket_price = fields.DecimalField(max_digits=10, decimal_places=2)
    created_at = fields.DatetimeField(auto_now_add=True)

    tickets: fields.ReverseRelation["Ticket"]
    lottery_prizes: fields.ReverseRelation["LotteryPrizes"]
from datetime import datetime, timezone

from app.database.models import User, Lottery, Ticket
from app.schemas.admin_schema import IStat, IStatResponse, ILotteryShortInfo, LiveStatus

def get_live_status():
    # TODO: livelink logic
    return LiveStatus.OFFLINE


async def get_admin_statistics() -> IStatResponse:
    users_count = await User.all().count()
    tickets_all = await Ticket.all().count()
    tickets_sold = await Ticket.exclude(owner=None).count()
    tickets_earn = 0
    
    async for t in Ticket.exclude(owner=None).select_related("lottery"):
        tickets_earn += t.lottery.ticket_price

    now = datetime.now(timezone.utc)
    active_lottery = await Lottery.filter(is_active=True, event_date__gte=now).first()

    if active_lottery:
        active_lottery_tickets = await Ticket.filter(lottery=active_lottery).count()
        active_lottery_sold = await Ticket.filter(lottery=active_lottery).exclude(owner=None).count()
        active_lottery_users = await Ticket.filter(lottery=active_lottery).exclude(owner=None).distinct().values_list("owner_id", flat=True)
        active_earn = active_lottery.ticket_price * active_lottery_sold

        active_lottery_info = ILotteryShortInfo(
            id=active_lottery.id,
            name=active_lottery.name,
            event_date=int(active_lottery.event_date.timestamp())
        )
    else:
        active_lottery_info = None
        active_lottery_tickets = 0
        active_lottery_sold = 0
        active_lottery_users = []
        active_earn = 0.0

    stat = IStat(
        users_count=users_count,
        tickets_earn=tickets_earn,
        active_lottery_participants=len(active_lottery_users),
        active_lottery_sold_tickets_count=active_lottery_sold,
        active_lottery_tickets_count=active_lottery_tickets,
        active_lottery_tickets_earn=active_earn,
    )

    return IStatResponse(
        active_lottery=active_lottery_info,
        live_status=get_live_status(),
        stat=stat,
    )

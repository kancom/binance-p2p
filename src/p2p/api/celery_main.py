from celery import Celery
from p2p.wiring import Container as wiring

app = Celery(__name__)
app.config_from_object(wiring.celery_settings)
app.autodiscover_tasks()
app.set_default()
app.conf.beat_schedule = {
    "convoy-10-seconds": {
        "task": "p2p.api.celery_tasks.convoy_ads",
        "schedule": wiring.celery_settings.poll_interval,
    },
    "new-offers-30-seconds": {
        "task": "p2p.api.celery_tasks.new_order",
        "schedule": wiring.celery_settings.new_offer_poll_interval,
    },
}
container = wiring()

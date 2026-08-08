from app.extensions import db
from app.models.event_model import FailoverEvent


class EventLogService:

    @staticmethod
    def log_event(
        node_id,
        event_type,
        reason,
        previous_status,
        new_status
    ):

        event = FailoverEvent(
            node_id=node_id,
            event_type=event_type,
            reason=reason,
            previous_status=previous_status,
            new_status=new_status
        )

        db.session.add(event)
        db.session.commit()

        return event
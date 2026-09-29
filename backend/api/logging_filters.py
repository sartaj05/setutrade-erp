import logging


class RequestIdFilter(logging.Filter):
    """Add a stable field so every application log can be correlated."""

    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = '-'
        return True

"""Common notification library."""

from peewee import BooleanField, CharField, ForeignKeyField

from configlib import loadcfg
from emaillib import Mailer
from mdb import Customer


__all__ = ['get_email_func', 'get_orm_model']


CONFIG = loadcfg('notificationlib.conf')
MAILER = Mailer.from_config(CONFIG['mailer'])


def get_email_func(get_emails_func):
    """Returns an emailing function."""

    def email(obj):
        """Emails information about the given object."""
        emails = get_emails_func(obj)

        if emails:
            return MAILER.send(emails)

        return None

    return email


def get_orm_model(base_model):
    """Returns a ORM model for notification emails."""

    class NotificationEmail(base_model):    # pylint: disable=R0903
        """Stores emails for notifications about new messages."""

        class Meta:     # pylint: disable=C0111,R0903
            table_name = 'notification_emails'

        customer = ForeignKeyField(Customer, column_name='customer')
        email = CharField(255)
        subject = CharField(255, null=True)
        html = BooleanField(default=False)

        @classmethod
        def from_json(cls, json, customer, **kwargs):
            """Creates a notification email for the respective customer."""
            record = super().from_json(json, **kwargs)
            record.customer = customer
            return record

    return NotificationEmail

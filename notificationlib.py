"""Common notification library."""

from peewee import BooleanField, CharField, ForeignKeyField

from emaillib import Mailer
from mdb import Customer


__all__ = ['get_orm_model', 'EMailFacility']


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


class EMailFacility():
    """Emailing facility."""

    def __init__(self, email_config, email_generator):
        """Sets the email configuration."""
        self.email_config = email_config
        self.email_generator = email_generator

    @property
    def mailer(self):
        """Returns the respective mailer."""
        return Mailer.from_config(self.email_config)

    def email(self, obj):
        """Sends notifications emails."""
        emails = self.email_generator(obj)

        if emails:  # pylint: disable=W0125
            return self.mailer.send(emails)

        return None

"""Common notification library."""

from flask import request
from peewee import BooleanField, CharField, ForeignKeyField

from configlib import loadcfg
from emaillib import Mailer
from his import CUSTOMER, admin, authenticated, authorized
from mdb import Customer
from wsgilib import JSON, JSONMessage


__all__ = ['get_email_func', 'get_email_orm_model', 'get_wsgi_funcs']


CONFIG = loadcfg('notificationlib.conf')
MAILER = Mailer.from_config(CONFIG['mailer'])
EMAILS_UPDATED = JSONMessage('The emails list has benn updated.', status=200)


def get_email_func(get_emails_func):
    """Returns an emailing function."""

    def email(*args, **kwargs):
        """Emails information about the given object."""
        emails = get_emails_func(*args, **kwargs)

        if emails:
            return MAILER.send(emails)

        return None

    return email


def get_email_orm_model(base_model, tablename='notification_emails'):
    """Returns a ORM model for notification emails."""

    class NotificationEmail(base_model):    # pylint: disable=R0903
        """Stores emails for notifications about new messages."""

        class Meta:     # pylint: disable=C0111,R0903
            table_name = tablename

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


def get_wsgi_funcs(service_name, email_orm_model):
    """Returns WSGI functions to list and set the respective emails."""

    @authenticated
    @authorized(service_name)
    def get_emails():
        """Deletes the respective message."""

        condition = email_orm_model.customer == CUSTOMER.id
        emails = email_orm_model.select().where(condition)
        return JSON([email.to_json() for email in emails])


    @authenticated
    @authorized(service_name)
    @admin
    def set_emails():
        """Replaces all email address of the respective customer."""

        ids = []
        condition = email_orm_model.customer == CUSTOMER.id

        for email in email_orm_model.select().where(condition):
            email.delete_instance()

        for email in request.json:
            email = email_orm_model.from_json(email, CUSTOMER.id)
            email.save()
            ids.append(email.id)

        return EMAILS_UPDATED.update(ids=ids)

    return (get_emails, set_emails)

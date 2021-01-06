"""Common notification library."""

from __future__ import annotations
from typing import Any, Callable, Iterator, Tuple

from flask import request
from peewee import BooleanField, CharField, ForeignKeyField, Model, ModelBase

from configlib import loadcfg
from emaillib import EMail, Mailer
from his import CUSTOMER, admin, authenticated, authorized
from mdb import Customer
from wsgilib import JSON, JSONMessage


__all__ = ['get_email_func', 'get_email_orm_model', 'get_wsgi_funcs']


CONFIG = loadcfg('notificationlib.conf')
MAILER = Mailer.from_section(CONFIG['mailer'])
EMAILS_UPDATED = JSONMessage('The emails list has been updated.', status=200)
WSGIFuncs = Tuple[Callable, Callable]
GetEmailsFunc = Callable[..., Iterator[EMail]]


def get_email_func(get_emails_func: GetEmailsFunc) -> Callable[..., Any]:
    """Returns an emailing function."""

    def email(*args, **kwargs):
        """Emails information about the given object."""
        emails = list(get_emails_func(*args, **kwargs))

        if emails:
            return MAILER.send(emails)

        return None

    return email


def get_email_orm_model(base_model: ModelBase,
                        table_name: str = 'notification_emails') -> ModelBase:
    """Returns a ORM model for notification emails."""

    class NotificationEmail(base_model):    # pylint: disable=R0903
        """Stores emails for notifications about new messages."""

        class Meta:     # pylint: disable=C0111,R0903
            pass

        Meta.table_name = table_name    # Avoid scope confusion.
        customer = ForeignKeyField(Customer, column_name='customer')
        email = CharField(255)
        subject = CharField(255, null=True)
        html = BooleanField(default=False)

        @classmethod
        def from_json(cls, json: dict, customer: Customer, **kwargs) -> Model:
            """Creates a notification email for the respective customer."""
            record = super().from_json(json, **kwargs)
            record.customer = customer
            return record

    return NotificationEmail


def get_wsgi_funcs(service_name: str, email_orm_model: ModelBase) -> WSGIFuncs:
    """Returns WSGI functions to list and set the respective emails."""

    @authenticated
    @authorized(service_name)
    def get_emails() -> JSON:
        """Deletes the respective message."""

        condition = email_orm_model.customer == CUSTOMER.id
        emails = email_orm_model.select().where(condition)
        return JSON([email.to_json() for email in emails])


    @authenticated
    @authorized(service_name)
    @admin
    def set_emails() -> JSONMessage:
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

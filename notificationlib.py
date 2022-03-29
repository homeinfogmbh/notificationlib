"""Common notification library."""

from __future__ import annotations
from typing import Callable, Iterable, Optional, Type

from flask import request
from peewee import BooleanField, ForeignKeyField, Model

from configlib import load_config
from emaillib import EMail, Mailer
from his import CUSTOMER, admin, authenticated, authorized
from mdb import Customer
from peeweeplus import EMailField, HTMLCharField
from wsgilib import JSON, JSONMessage


__all__ = ['get_email_func', 'get_email_orm_model', 'get_wsgi_funcs']


def get_mailer() -> Mailer:
    """Returns the mailer."""

    return Mailer.from_section(load_config('notificationlib.conf')['mailer'])


def get_email_func(
        get_emails_func: Callable[..., Iterable[EMail]]
) -> Callable[..., Optional[bool]]:
    """Returns an emailing function."""

    def email(*args, **kwargs) -> Optional[bool]:
        """Emails information about the given object."""

        if emails := list(get_emails_func(*args, **kwargs)):
            return get_mailer().send(emails)

        return None

    return email


def get_email_orm_model(
        base_model: Type[Model],
        table_name: str = 'notification_emails',
        *,
        subject_field: bool = True,
        html_field: bool = True
) -> Type[Model]:
    """Returns an ORM model for notification emails."""

    class NotificationEmail(base_model):
        """Stores emails for notifications about new messages."""

        class Meta:
            pass

        Meta.table_name = table_name    # Avoid scope confusion.
        customer = ForeignKeyField(Customer, column_name='customer')
        email = EMailField(255)

        if subject_field:
            subject = HTMLCharField(255, null=True)

        if html_field:
            html = BooleanField(default=False)

        @classmethod
        def from_json(cls, json: dict, customer: Customer, **kwargs) -> Model:
            """Creates a notification email for the respective customer."""
            record = super().from_json(json, **kwargs)
            record.customer = customer
            return record

    return NotificationEmail


def get_wsgi_funcs(
        service_name: str,
        email_orm_model: Type[Model]
) -> tuple[Callable, Callable]:
    """Returns WSGI functions to list and set the respective emails."""

    @authenticated
    @authorized(service_name)
    def get_emails() -> JSON:
        """Deletes the respective message."""

        return JSON([
            email.to_json() for email in email_orm_model.select().where(
                email_orm_model.customer == CUSTOMER.id
            )
        ])

    @authenticated
    @authorized(service_name)
    @admin
    def set_emails() -> JSONMessage:
        """Replaces all email address of the respective customer."""

        ids = []

        for email in email_orm_model.select().where(
                email_orm_model.customer == CUSTOMER.id
        ):
            email.delete_instance()

        for email in request.json:
            email = email_orm_model.from_json(email, CUSTOMER.id)
            email.save()
            ids.append(email.id)

        return JSONMessage(
            'The emails list has been updated.', ids=ids, status=200
        )

    return get_emails, set_emails

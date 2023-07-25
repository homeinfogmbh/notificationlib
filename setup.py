#! /usr/bin/env python3

from setuptools import setup

setup(
    name="notificationlib",
    use_scm_version={"local_scheme": "node-and-timestamp"},
    setup_requires=["setuptools_scm"],
    install_requires=[
        "configlib",
        "emaillib",
        "flask",
        "his",
        "mdb",
        "peewee",
        "peeweeplus",
        "wsgilib",
    ],
    author="HOMEINFO - Digitale Informationssysteme GmbH",
    author_email="<info at homeinfo dot de>",
    maintainer="Richard Neumann",
    maintainer_email="<r dot neumann at homeinfo priod de>",
    py_modules=["notificationlib"],
    license="GPLv3",
    description="An email notification library.",
)

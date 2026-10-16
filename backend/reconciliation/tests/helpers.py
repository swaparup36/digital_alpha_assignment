from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient


HEADER = "date,description,amount,type,reference\n"


def client_for(slug="northwind"):
    client = APIClient()
    client.credentials(HTTP_X_ORGANIZATION=slug)
    return client


def upload(client, rows):
    content = (HEADER + rows).encode("utf-8")
    return client.post(
        "/api/imports/",
        {"file": SimpleUploadedFile("statement.csv", content, content_type="text/csv")},
        format="multipart",
    )


def seed():
    call_command("seed_demo", verbosity=0)

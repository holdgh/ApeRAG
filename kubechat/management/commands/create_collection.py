import json

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand, CommandError

from config import settings
from kubechat.utils.constant import KEY_USER_ID
from kubechat.views.main import create_collection, CollectionIn
from django.http import HttpRequest
from http import HTTPStatus


class Command(BaseCommand):
    help = "init the default collections"

    def add_arguments(self, parser):
        parser.add_argument("--title", type=str, required=True, help="collection title")
        parser.add_argument("--description", type=str, default="", help="collection description")

    def handle(self, *args, **options):
        title = options["title"]
        description = options["description"]

        request = HttpRequest()
        request.method = "POST"
        request.META = {
            KEY_USER_ID: settings.SYSTEM_USER,
        }
        config = {
            "source": "system"
        }
        data = CollectionIn(type="document", title=title, description=description, config=json.dumps(config))
        response = async_to_sync(create_collection)(request, data)
        if int(response["code"]) != HTTPStatus.OK:
            raise CommandError('Failed to create collection: %s' % response.get("message", "unknown error"))
        else:
            self.stdout.write(
                self.style.SUCCESS('Successfully created collection %s' % response["data"]["id"])
            )

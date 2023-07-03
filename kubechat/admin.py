from django.contrib import admin

from .models import Chat, Collection, Document

admin.site.register(Collection)
admin.site.register(Document)
admin.site.register(Chat)

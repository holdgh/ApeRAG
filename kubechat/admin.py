from django.contrib import admin
from .models import Chat, Collection, Document
from django.utils.html import format_html


admin.site.site_header = 'Kubechat admin'  # set header
admin.site.site_title = 'Kubechat admin'   # set title
admin.site.index_title = 'Kubechat admin'

class DocumentInline(admin.StackedInline):
    model = Document


class ChatInline(admin.StackedInline):
    model = Chat


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'user', 'status', 'type', 'created_date', 'updated_date')
    list_filter = ('status',)
    search_fields = ('title',)
    inlines = [DocumentInline]  # Associated models displayed inline
    '''Replacement value for empty field'''
    empty_value_display = 'NA'

    def created_date(self, obj):
        return format_html(
            '<span style="color: black;">{}</span>',
            obj.gmt_updated.strftime("%Y-%m-%d %H:%M:%S")
        )

    created_date.short_description = 'created'

    def updated_date(self, obj):
        return format_html(
            '<span style="color: black;">{}</span>',
            obj.gmt_updated.strftime("%Y-%m-%d %H:%M:%S")
        )

    updated_date.short_description = 'updated'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'collection_id', 'created_date', 'updated_date')
    list_filter = ('status',)
    search_fields = ('name', 'user')
    empty_value_display = 'NA'

    def created_date(self, obj):
        return format_html(
            '<span style="color: black;">{}</span>',
            obj.gmt_updated.strftime("%Y-%m-%d %H:%M:%S")
        )

    created_date.short_description = 'created'

    def updated_date(self, obj):
        return format_html(
            '<span style="color: black;">{}</span>',
            obj.gmt_updated.strftime("%Y-%m-%d %H:%M:%S")
        )

    updated_date.short_description = 'updated'


# admin.site.register(Chat)
@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'collection', 'codetype', 'gmt_created', 'gmt_updated')
    list_filter = ('status', 'codetype')
    search_fields = ('user',)
    '''Replacement value for empty field'''
    empty_value_display = 'NA'

    def collection(self, obj):
        return obj.collection.title

    def codetype(self, obj):
        return obj.get_codetype_display()

    collection.admin_order_field = 'collection__title'
    codetype.admin_order_field = 'codetype'

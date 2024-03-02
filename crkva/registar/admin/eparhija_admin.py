from django.contrib import admin

class EparhijaAdmin(admin.ModelAdmin):
    list_display = ('naziv', 'sediste')  # Fields to display in the admin list view
    search_fields = ('naziv', 'sediste')  # Fields to search in the admin
    list_filter = ('sediste',)  # Fields to filter in the admin sidebar
    ordering = ('naziv',)  # Default ordering

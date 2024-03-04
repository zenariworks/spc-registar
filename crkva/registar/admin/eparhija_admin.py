from django.contrib import admin

class EparhijaAdmin(admin.ModelAdmin):
    list_display = ('naziv', 'sediste')
    search_fields = ('naziv', 'sediste')
    list_filter = ('sediste',)
    ordering = ('naziv',)

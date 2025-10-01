from django.contrib import admin
from .models import Document, GeneratedContent, Log


admin.site.register(Document)
admin.site.register(GeneratedContent)
admin.site.register(Log)
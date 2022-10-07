from django.contrib import admin

# Register your models here.

# Ces tables pourront être manipulées par l’interface admin sur le site
from .models import Ville, Rue
admin.site.register(Ville)
admin.site.register(Rue)

from django.apps import AppConfig


class FacilitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'facilities'



    def ready(self):
        import facilities.signals  

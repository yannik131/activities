from django.apps import AppConfig


class UsergroupsConfig(AppConfig):
    name = 'usergroups'

    def ready(self):
        import usergroups.signals
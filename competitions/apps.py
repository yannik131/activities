from django.apps import AppConfig


class CompetitionsConfig(AppConfig):
    name = 'competitions'

    def ready(self):
        import competitions.signals

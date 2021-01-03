from django.apps import AppConfig


class MultiplayerConfig(AppConfig):
    name = 'multiplayer'
    
    def ready(self) -> None:
        import multiplayer.signals

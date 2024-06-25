from django.db import models
from django.contrib.auth.models import User

class ChatBot(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="GeminiUser", null=True
    )
    text_input = models.CharField(max_length=500)
    gemini_output = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.text_input

    @classmethod
    def create_chat(cls, text_input, gemini_output, user=None):
        # Crear una instancia de ChatBot solo si hay un usuario autenticado
        if user and user.is_authenticated:
            return cls.objects.create(text_input=text_input, gemini_output=gemini_output, user=user)
        else:
            # No almacenar información de chat para usuarios no logueados
            return None

class FileInfo(models.Model):
    path = models.URLField()
    info = models.CharField(max_length=255)

    def __str__(self):
        return self.path
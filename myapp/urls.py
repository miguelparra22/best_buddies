from django.urls import path
from .views import ChatbotFunctionCallingView

urlpatterns = [
    path("chatbot/", ChatbotFunctionCallingView.as_view(), name="chatbot-function-calling"),
]
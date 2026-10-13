from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    path('health', lambda request: HttpResponse('ok')),
    path('admin/', admin.site.urls),
    path('api/todos/', include('todos.urls')),
    path('api/payments/', include('payments.urls')),
]

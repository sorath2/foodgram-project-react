from django.contrib import admin
from django.urls import include, path
from api.views import (
    UsersViewSet,
)
from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register(r'users', UsersViewSet, basename='users')
# #router.register(r'^users/[/.]+', include('djoser.urls'))
# router.register(r'^auth/', include('djoser.urls.authtoken'), basename='token')

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('api/', include(router.urls)),
    path('api/', include('djoser.urls')),
    #path('api/users/', UsersViewSet.as_view({'get': 'list', 'post': 'create'}), name='users'),
    path('api/auth/', include('djoser.urls.authtoken')),
]

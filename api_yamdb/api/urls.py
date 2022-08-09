from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CommentViewSet,
    GenreViewSet,
    ReviewViewSet,
    TitleViewSet,
    APIGetToken,
    APISignup,
    UsersViewSet
)


router = DefaultRouter()
router.register('users', UsersViewSet)
router.register('categories', CategoryViewSet)
router.register('genres', GenreViewSet)
router.register('titles', TitleViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)
auth_urls = [
    path('signup/', APISignup.as_view(), name='signup'),
    path('token/', APIGetToken.as_view(), name='get_token')
]
app_name = 'api'

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/auth/', include(auth_urls)),
]

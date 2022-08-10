from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.mixins import GenreCategoryMixin
from api.permissions import (
    AdminOnly,
    AuthorAndStaffOrReadOnly,
    IsAdminOrReadOnly
)
from api.serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    GetTokenSerializer,
    NotAdminSerializer,
    ReviewSerializer,
    SignUpSerializer,
    TitleCreateSerializer,
    TitleReadSerializer,
    UsersSerializer
)
from reviews.filters import TitleFilter
from reviews.models import Category, Genre, Review, Title, User


class GenreViewSet(GenreCategoryMixin):
    """Жанры."""
    queryset = Genre.objects.all().order_by('slug')
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    """Произведения."""
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).all().order_by('name')
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH', 'DELETE'):
            return TitleCreateSerializer
        return TitleReadSerializer


class CategoryViewSet(GenreCategoryMixin):
    """Категории."""
    queryset = Category.objects.all().order_by('slug')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    lookup_field = 'slug'


class ReviewViewSet(viewsets.ModelViewSet):
    """Отзывы."""
    serializer_class = ReviewSerializer
    permission_classes = (AuthorAndStaffOrReadOnly,)

    def get_queryset(self):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        )
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии."""
    serializer_class = CommentSerializer
    permission_classes = (AuthorAndStaffOrReadOnly,)

    def get_queryset(self):
        if get_object_or_404(Title, pk=self.kwargs.get('title_id')):
            review_id = self.kwargs.get('review_id')
            title_id = self.kwargs.get('title_id')
            review = get_object_or_404(
                Review,
                pk=review_id,
                title__pk=title_id
            )
            return review.comments.all()
        return None

    def perform_create(self, serializer):
        if get_object_or_404(Title, pk=self.kwargs.get('title_id')):
            review_id = self.kwargs.get('review_id')
            title_id = self.kwargs.get('title_id')
            review = get_object_or_404(
                Review,
                pk=review_id,
                title__pk=title_id
            )
            serializer.save(
                author=self.request.user,
                review=review
            )


class UsersViewSet(viewsets.ModelViewSet):
    """Пользователи."""
    queryset = User.objects.all()
    serializer_class = UsersSerializer
    pagination_class = PageNumberPagination
    permission_classes = (AdminOnly,)
    filter_backends = (filters.SearchFilter,)
    filterset_fields = ('username',)
    search_fields = ('username',)
    lookup_field = 'username'

    @action(
        methods=['GET', 'PATCH'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def get_patch_me(self, request):
        user = get_object_or_404(User, username=self.request.user)
        if request.method == 'GET':
            serializer = NotAdminSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = NotAdminSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class APIGetToken(APIView):
    """
    Получение JWT-токена в обмен на username и confirmation code.
    Права доступа: Доступно без токена. Пример тела запроса:
    {
        "username": "string",
        "confirmation_code": "string"
    }
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = GetTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        username = serializer.data['username']
        user = get_object_or_404(User, username=username)
        confirmation_code = serializer.data['confirmation_code']
        if not default_token_generator.check_token(user, confirmation_code):
            return Response(
                {'Wrong Code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        token = RefreshToken.for_user(user)
        return Response(
            {'token': str(token.access_token)},
            status=status.HTTP_200_OK
        )


class APISignup(APIView):
    """
    Получить код подтверждения на переданный email.
    Права доступа: Доступно без токена.
    Использовать имя 'me' в качестве username запрещено.
    Поля email и username должны быть уникальными.
    Пример тела запроса:
    {
        "email": "string",
        "username": "string"
    }
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

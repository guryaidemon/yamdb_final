from django.db import IntegrityError
from rest_framework import serializers

from api.services import send_confirmation_code
from reviews.models import (
    Category,
    Comment,
    Genre,
    GenreTitle,
    Review,
    Title,
    User
)


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор Review."""
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        read_only_fields = ('title',)
        model = Review

    def validate(self, data):
        if self.context['request'].method == 'POST' and Review.objects.filter(
                title=self.context['view'].kwargs['title_id'],
                author=self.context['request'].user
        ).exists():
            raise serializers.ValidationError(
                ['Можно оставить только один отзыв']
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор Comment."""
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('review',)
        model = Comment


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор Category."""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreTitleSerializer(serializers.ModelSerializer):
    """Сериализатор GenreTitle."""
    class Meta:
        model = GenreTitle
        fields = '__all__'


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор Genre."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleCreateSerializer(serializers.ModelSerializer):
    """Основной метод записи информации."""
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )

    class Meta:
        model = Title
        fields = '__all__'


class TitleReadSerializer(serializers.ModelSerializer):
    """Основной метод получения информации."""
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = '__all__'


class UsersSerializer(serializers.ModelSerializer):
    """Пользователь с ролью администратор."""
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )


class NotAdminSerializer(serializers.ModelSerializer):
    """Без возможности корректировать роль."""
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )
        read_only_fields = ('role',)


class GetTokenSerializer(serializers.ModelSerializer):
    """Получение токена."""
    username = serializers.CharField(
        required=True
    )
    confirmation_code = serializers.CharField(
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'confirmation_code')


class SignUpSerializer(serializers.ModelSerializer):
    """Авторизация."""
    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.CharField(max_length=150, required=True)

    class Meta:
        model = User
        fields = ('email', 'username')

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError('Нельзя использовать логин me')
        return data

    def create(self, validated_data):
        try:
            user, _ = User.objects.get_or_create(**validated_data)
        except IntegrityError as error:
            error = error.args[0].split()
            field_error = error[-1].split('.')[-1]
            data = {
                field_error: (
                    'Такой логин или email уже существуют'
                )
            }
            raise serializers.ValidationError(detail=data)
        send_confirmation_code(user)
        return user

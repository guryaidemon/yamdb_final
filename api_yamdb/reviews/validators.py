from datetime import datetime

from django.core.validators import RegexValidator, ValidationError


class UsernameValidator(RegexValidator):
    regex = r'^[\w.@+-]+$'
    flags = 0


def validate_year(value):
    if int(value) > datetime.today().year:
        raise ValidationError(
            'Год не должен превышать текущий'
        )
    return value


def validate_score(value):
    if not (1 <= value <= 10):
        raise ValidationError('Проверьте оценку!')
    return value

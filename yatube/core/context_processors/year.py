from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    date = timezone.localtime(timezone.now()).strftime('%Y')
    return {
        'year': date
    }

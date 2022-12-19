from django.core.paginator import Paginator
from yatube.settings import POSTS_NUMBER


def context_list(queryset, request):
    paginator = Paginator(queryset, POSTS_NUMBER)
    page_number = request.GET.get('page')
    page_context = paginator.get_page(page_number)
    return page_context

from ads.models import Response

def unread_responses_count(request):
    if request.user.is_authenticated:
        unread_count = Response.objects.filter(ad__author=request.user, status="pending").count()
        return {'unread_responses_count': unread_count}

    return {'unread_responses_count': 0}

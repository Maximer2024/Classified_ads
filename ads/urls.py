from django.urls import path
from .views import (
    ad_list, ad_detail, ad_create, ad_update, ad_delete,
    add_response, user_responses, change_response_status,
    delete_response, subscribe_category, subscribe_author,
    get_unread_responses, user_ads
)

urlpatterns = [
    path('', ad_list, name='ad_list'),
    path('<int:ad_id>/', ad_detail, name='ad_detail'),
    path('create/', ad_create, name='ad_create'),
    path('<int:ad_id>/edit/', ad_update, name='ad_update'),
    path('<int:ad_id>/delete/', ad_delete, name='ad_delete'),
    path('<int:ad_id>/respond/', add_response, name='add_response'),
    path('responses/', user_responses, name='user_responses'),
    path('responses/<int:response_id>/delete/', delete_response, name='delete_response'),
    path('responses/<int:response_id>/<str:status>/', change_response_status, name='change_response_status'),
    path('subscriptions/category/', subscribe_category, name='subscribe_category'),
    path('subscriptions/author/', subscribe_author, name='subscribe_author'),
    path('get_unread_responses/', get_unread_responses, name='get_unread_responses'),
    path('my-ads/', user_ads, name='user_ads'),
]

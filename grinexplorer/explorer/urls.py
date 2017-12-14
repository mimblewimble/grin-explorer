from django.urls import path

from .views import BlockList, BlocksByHeight, BlockDetail, Search


urlpatterns = [
    path("", BlockList.as_view(), name="block-list"),
    path("block/<int:height>", BlocksByHeight.as_view(), name="blocks-by-height"),
    path("block/<str:pk>", BlockDetail.as_view(), name="block-detail"),
    path("search", Search.as_view(), name="search"),
]

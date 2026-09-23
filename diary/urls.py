from django.urls import path

from .views import (
    EntryCreateView,
    EntryDeleteView,
    EntryDetailView,
    EntryListView,
    EntryUpdateView,
)

app_name = "diary"

urlpatterns = [
    path("", EntryListView.as_view(), name="entry_list"),
    path("create/", EntryCreateView.as_view(), name="entry_create"),
    path("<int:pk>/", EntryDetailView.as_view(), name="entry_detail"),
    path("<int:pk>/edit/", EntryUpdateView.as_view(), name="entry_update"),
    path("<int:pk>/delete/", EntryDeleteView.as_view(), name="entry_delete"),
]

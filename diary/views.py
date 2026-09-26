from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import EntryForm
from .mixins import OwnerQuerySetMixin
from .models import Entry


class EntryListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
    model = Entry
    template_name = "diary/entry_list.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        self.total_entries = queryset.count()
        self.search_query = self.request.GET.get("q", "").strip()
        self.sort = self.request.GET.get("sort", "newest")

        ordering_options = {
            "newest": ("-created_at", "-pk"),
            "oldest": ("created_at", "pk"),
        }

        if self.sort not in ordering_options:
            self.sort = "newest"

        if self.search_query:
            queryset = queryset.filter(
                Q(title__icontains=self.search_query)
                | Q(content__icontains=self.search_query)
            )

        return queryset.order_by(*ordering_options[self.sort])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.search_query
        context["sort"] = self.sort
        context["total_entries"] = self.total_entries
        return context


class EntryCreateView(LoginRequiredMixin, CreateView):
    model = Entry
    form_class = EntryForm
    template_name = "diary/entry_form.html"
    success_url = reverse_lazy("diary:entry_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class EntryDetailView(LoginRequiredMixin, OwnerQuerySetMixin, DetailView):
    model = Entry
    template_name = "diary/entry_detail.html"
    context_object_name = "entry"


class EntryUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Entry
    form_class = EntryForm
    template_name = "diary/entry_form.html"
    success_url = reverse_lazy("diary:entry_list")


class EntryDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Entry
    template_name = "diary/entry_confirm_delete.html"
    context_object_name = "entry"
    success_url = reverse_lazy("diary:entry_list")

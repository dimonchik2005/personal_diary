from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Entry

User = get_user_model()


class EntryPermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Owner-test-password-472!",
        )
        cls.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="Other-test-password-583!",
        )
        cls.entry = Entry.objects.create(
            owner=cls.owner,
            title="Личная запись",
            content="Секретный текст владельца",
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("diary:entry_list"))

        expected_url = (
            f"{reverse('users:login')}?" f"next={reverse('diary:entry_list')}"
        )
        self.assertRedirects(
            response,
            expected_url,
            fetch_redirect_response=False,
        )

    def test_owner_can_view_entry(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("diary:entry_detail", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.entry.content)

    def test_other_user_cannot_view_entry(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("diary:entry_detail", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_update_entry(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("diary:entry_update", args=[self.entry.pk]),
            {
                "title": "Чужое изменение",
                "content": "Подменённый текст",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Личная запись")
        self.assertEqual(
            self.entry.content,
            "Секретный текст владельца",
        )

    def test_other_user_cannot_delete_entry(self):
        self.client.force_login(self.other_user)

        response = self.client.post(reverse("diary:entry_delete", args=[self.entry.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Entry.objects.filter(pk=self.entry.pk).exists())

    def test_search_does_not_show_other_users_entries(self):
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("diary:entry_list"),
            {"q": "Секретный"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["entries"]), [])

    def test_creation_assigns_current_user_as_owner(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("diary:entry_create"),
            {
                "title": "Новая запись",
                "content": "Мой текст",
                "owner": self.owner.pk,
            },
        )

        self.assertRedirects(
            response,
            reverse("diary:entry_list"),
            fetch_redirect_response=False,
        )

        entry = Entry.objects.get(title="Новая запись")
        self.assertEqual(entry.owner, self.other_user)

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ResumeVerificationForm
from .services import issue_email_code, verify_email_code

User = get_user_model()


class EmailVerificationTests(TestCase):
    def setUp(self):
        self.password = "Diary-test-password-472!"

        self.user = User.objects.create_user(
            username="pending_user",
            email="pending@example.com",
            password=self.password,
            is_active=False,
        )

        self.verification, self.code = issue_email_code(self.user.pk)

    def test_code_is_six_digits_and_stored_as_hash(self):
        self.assertRegex(self.code, r"\A[0-9]{6}\Z")
        self.assertNotEqual(self.verification.code_hash, self.code)

        self.assertTrue(check_password(self.code, self.verification.code_hash))

    def test_correct_code_activates_user(self):
        verify_email_code(self.user.pk, self.code)

        self.user.refresh_from_db()
        self.verification.refresh_from_db()

        self.assertTrue(self.user.is_active)
        self.assertIsNotNone(self.verification.confirmed_at)

    def test_wrong_code_increases_attempts(self):
        wrong_code = "000000" if self.code != "000000" else "111111"

        with self.assertRaises(ValidationError):
            verify_email_code(self.user.pk, wrong_code)

        self.verification.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.verification.attempts, 1)
        self.assertFalse(self.user.is_active)

    def test_expired_code_is_rejected(self):
        self.verification.expires_at = timezone.now() - timedelta(seconds=1)
        self.verification.save(update_fields=["expires_at"])

        with self.assertRaises(ValidationError):
            verify_email_code(self.user.pk, self.code)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_attempt_limit_blocks_even_correct_code(self):
        wrong_code = "000000" if self.code != "000000" else "111111"

        with self.settings(EMAIL_VERIFICATION_MAX_ATTEMPTS=2):
            for _ in range(2):
                with self.assertRaises(ValidationError):
                    verify_email_code(self.user.pk, wrong_code)

            with self.assertRaises(ValidationError):
                verify_email_code(self.user.pk, self.code)

        self.verification.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.verification.attempts, 2)
        self.assertFalse(self.user.is_active)

    def test_immediate_resend_is_rejected(self):
        previous_hash = self.verification.code_hash

        with self.assertRaises(ValidationError):
            issue_email_code(self.user.pk)

        self.verification.refresh_from_db()
        self.assertEqual(self.verification.code_hash, previous_hash)

    def test_new_code_invalidates_previous_code(self):
        self.verification.last_requested_at = timezone.now() - timedelta(minutes=2)
        self.verification.save(update_fields=["last_requested_at"])

        replacement_number = 0 if self.code != "000000" else 1

        with self.settings(EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60):
            with patch(
                "users.services.secrets.randbelow",
                return_value=replacement_number,
            ):
                _, new_code = issue_email_code(self.user.pk)

        with self.assertRaises(ValidationError):
            verify_email_code(self.user.pk, self.code)

        verify_email_code(self.user.pk, new_code)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_confirmed_code_cannot_be_reused(self):
        verify_email_code(self.user.pk, self.code)

        with self.assertRaises(ValidationError):
            verify_email_code(self.user.pk, self.code)

    def test_resume_requires_correct_password(self):
        form = ResumeVerificationForm(
            data={
                "email": self.user.email,
                "password": "Wrong-password!",
            }
        )

        self.assertFalse(form.is_valid())

    def test_pending_user_can_resume_verification(self):
        form = ResumeVerificationForm(
            data={
                "email": self.user.email,
                "password": self.password,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.pending_user.pk, self.user.pk)

    def test_disabled_confirmed_user_cannot_resume(self):
        verify_email_code(self.user.pk, self.code)

        self.user.refresh_from_db()
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        form = ResumeVerificationForm(
            data={
                "email": self.user.email,
                "password": self.password,
            }
        )

        self.assertFalse(form.is_valid())

    @patch("users.views.send_welcome_email.delay")
    def test_confirmation_logs_user_in_and_queues_welcome(
        self,
        mocked_send_welcome,
    ):
        session = self.client.session
        session["pending_verification_user_id"] = self.user.pk
        session.save()

        response = self.client.post(
            reverse("users:verify_email"),
            {"code": self.code},
        )

        self.assertRedirects(
            response,
            reverse("diary:entry_list"),
            fetch_redirect_response=False,
        )

        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(self.user.pk),
        )
        self.assertNotIn(
            "pending_verification_user_id",
            self.client.session,
        )

        mocked_send_welcome.assert_called_once_with(self.verification.pk)

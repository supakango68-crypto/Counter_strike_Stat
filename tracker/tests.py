import hashlib
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import SearchHistory


class TrackerFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="a-safe-password-123")
        self.other = User.objects.create_user(username="bob", password="another-safe-password-123")

    @patch("tracker.views.get_player_data")
    def test_search_creates_owned_history_and_htmx_result(self, get_player_data):
        get_player_data.return_value = {
            "name": "Example", "steam64_id": "76561197969209908", "totalMatches": 12,
            "winRate": 50, "ranks": {}, "skill_rows": [("Aim", 70)],
        }
        self.client.force_login(self.user)
        response = self.client.post(reverse("profile"), {"query": "76561197969209908"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Example")
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 1)

    @patch("tracker.views.get_player_data", return_value=None)
    def test_missing_player_does_not_create_history(self, _):
        self.client.force_login(self.user)
        self.client.post(reverse("profile"), {"query": "unknown"})
        self.assertFalse(SearchHistory.objects.exists())

    def test_only_owner_can_edit_or_delete(self):
        record = SearchHistory.objects.create(user=self.user, query="example")
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("history_edit", args=[record.pk]), {"note": "bad"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("history_delete", args=[record.pk])).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("history_delete", args=[record.pk])).status_code, 405)
        self.client.post(reverse("history_edit", args=[record.pk]), {"note": "favorite"})
        record.refresh_from_db()
        self.assertEqual(record.note, "favorite")
        self.client.post(reverse("history_delete", args=[record.pk]))
        self.assertFalse(SearchHistory.objects.exists())

    def test_register_login_logout(self):
        response = self.client.post(reverse("register"), {
            "username": "newplayer", "email": "new@example.com",
            "password1": "StrongerPass!123", "password2": "StrongerPass!123",
        })
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(get_user_model().objects.filter(username="newplayer").exists())
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertRedirects(self.client.get(reverse("profile")), f"{reverse('login')}?next={reverse('profile')}")

    @patch("tracker.views.get_match_history", return_value=[{"mapName": "Mirage", "won": True, "teamScores": [13, 8], "startedAt": "2026-01-01"}])
    def test_matches_render(self, _):
        self.client.force_login(self.user)
        response = self.client.post(reverse("matches"), {"query": "76561197969209908", "limit": 5})
        self.assertContains(response, "Mirage")

    @patch("tracker.views.get_player_data", side_effect=[{"name": "A", "ratings": {}}, {"name": "B", "ratings": {}}])
    def test_compare_render(self, _):
        self.client.force_login(self.user)
        response = self.client.post(reverse("compare"), {"player1": "A", "player2": "B"})
        self.assertContains(response, "เปรียบเทียบ")

    def test_legacy_user_import_preserves_password(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "users.db"
            digest = hashlib.pbkdf2_hmac("sha256", b"legacy-password", b"salt", 1000).hex()
            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE user (username TEXT, email TEXT, password_hash TEXT)")
                connection.execute("INSERT INTO user VALUES (?, ?, ?)", ("legacy", "legacy@example.com", f"pbkdf2:sha256:1000$salt${digest}"))
                connection.commit()
            call_command("import_flask_users", source=source, verbosity=0)
        self.assertTrue(get_user_model().objects.get(username="legacy").check_password("legacy-password"))

"""scripts/gunicorn.conf.py must stay portable — no hardcoded install dir."""

from django.test import SimpleTestCase

from registar.tests.paths import repo_path


class GunicornConfPortableTest(SimpleTestCase):
    """The committed gunicorn.conf.py must not pin the install directory."""

    def test_no_hardcoded_install_path(self):
        text = repo_path("scripts/gunicorn.conf.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "chdir =",
            text,
            "Hardcoded chdir is a deploy hazard — let systemd WorkingDirectory= drive cwd.",
        )
        self.assertNotIn("/root/projects/spc-registar/crkva", text)
        self.assertNotIn("/root/projects/spc-registar-main", text)

    def test_bind_to_all_interfaces(self):
        text = repo_path("scripts/gunicorn.conf.py").read_text(encoding="utf-8")
        self.assertIn('bind = "0.0.0.0:9000"', text)

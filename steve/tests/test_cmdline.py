from unittest import TestCase


class CmdlineTestCase(TestCase):
    def test_cmdline_imports(self):
        from steve import cmdline  # noqa

import unittest
import datetime

from mock import patch

from yadtbroadcastserver import scheduling


class TestTimeUntilMidnight(unittest.TestCase):

    mock_now_return = datetime.datetime(1970, 1, 1, 23, 59)

    @patch('yadtbroadcastserver.scheduling._now')
    def test_seconds_to_midnight_with_default_offset(self, now_mock):
        now_mock.return_value = self.mock_now_return
        self.assertEquals(102, scheduling.seconds_to_midnight(offset_seconds=42))

    @patch('yadtbroadcastserver.scheduling._now')
    def test_seconds_to_midnight_with_other_offset(self, now_mock):
        now_mock.return_value = self.mock_now_return
        self.assertEquals(60, scheduling.seconds_to_midnight())

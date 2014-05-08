import unittest
import datetime

from mock import patch

from yadtbroadcastserver import scheduling


class TestTimeUntilMidnight(unittest.TestCase):

    @patch('yadtbroadcastserver.scheduling._now')
    def test(self, now_mock):
        now_mock.return_value = datetime.datetime(1970, 1, 1, 23, 59)
        scheduling.seconds_to_midnight()

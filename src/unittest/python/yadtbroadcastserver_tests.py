import unittest

from mock import Mock, call, patch, MagicMock

from yadtbroadcastserver import (BroadcastServerProtocol,
                                 _write_metrics,
                                 _reset_metrics)


class WriteMetricsToFileTests(unittest.TestCase):

    def setUp(self):
        self.ybc = BroadcastServerProtocol()

    def test_should_not_write_anything_when_no_metrics_given(self):
        mock_file = Mock()
        metrics = {}

        _write_metrics(metrics, mock_file)

        self.assertFalse(mock_file.write.called)

    def test_should_write_metrics(self):
        mock_file = Mock()
        metrics = {
            "metric1": 21,
            "metric2": 42
        }

        _write_metrics(metrics, mock_file)

        self.assertEquals(mock_file.write.call_args_list,
                          [call('metric2=42\n'),
                           call('metric1=21\n')])

    @patch("yadtbroadcastserver.open", create=True)
    @patch("yadtbroadcastserver.BroadcastServerProtocol.metrics_directory")
    def test_should_open_configured_file_for_writing(self, metrics_directory, open_):
        metrics_directory.__get__ = Mock(return_value='/any/dir')
        open_.return_value = MagicMock(spec=file)

        self.ybc.write_metrics_to_file()

        open_.assert_called_with('/any/dir/ybc.metrics', mode='w')

    @patch("yadtbroadcastserver.open", create=True)
    @patch("yadtbroadcastserver.BroadcastServerProtocol.metrics_directory")
    def test_should_not_open_anything_when_no_metric(self, metrics_directory, open_):
        metrics_directory.__get__ = Mock(return_value=None)
        open_.return_value = MagicMock(spec=file)

        self.ybc.write_metrics_to_file()

        self.assertFalse(open_.called)


class TestCache(unittest.TestCase):

    def setUp(self):
        self.ybc = BroadcastServerProtocol()

    def test_init_cache(self):
        self.ybc.init_cache()

    def test_store_cache_noop_with_clean_cache(self):
        self.ybc.store_cache()

    @patch("yadtbroadcastserver.open", create=True)
    @patch("yadtbroadcastserver.BroadcastServerProtocol.cache_file")
    def test_store_cache_writes_with_dirty_cache(self, cache_file, open_):
        cache_file.return_value = '/any/cache/file'
        mock_file = MagicMock(spec=file)
        open_.return_value = mock_file

        BroadcastServerProtocol.cache_dirty = True
        self.ybc.store_cache()

        open_.assert_called_with('/any/cache/file', 'w')
        mock_file.write.assert_called_once_with('{}')
        self.assertFalse(BroadcastServerProtocol.cache_dirty)


class TestResetMetrics(unittest.TestCase):

    def test_should_remove_metrics_when_they_are_empty(self):
        metrics = {
            "empty": 0,
            "empty_long": 0L,
        }

        _reset_metrics(metrics)

        self.assertEquals(metrics,
                          {})

    def test_should_just_reset_metrics_when_they_are_not_empty(self):
        metrics = {
            "full": 42,
            "full_long": 42L,
        }

        _reset_metrics(metrics)

        self.assertEquals(metrics,
                          {   "full": 0,
                              "full_long": 0,
                          })

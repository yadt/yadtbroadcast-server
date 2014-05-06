import unittest
import sys

from mock import Mock, call, patch, MagicMock


class WriteMetricsToFileTests(unittest.TestCase):

    def setUp(self):
        import sys
        sys.modules["broadcastserverconfig"] = Mock()
        from yadtbroadcastserver import BroadcastServerProtocol, _write_metrics
        self.ybc = BroadcastServerProtocol()
        self._write_metrics = _write_metrics

    def test_should_not_write_anything_when_no_metrics_given(self):
        mock_file = Mock()
        metrics = {}

        self._write_metrics(metrics, mock_file)

        self.assertFalse(mock_file.write.called)

    def test_should_write_metrics_without_prefix(self):
        mock_file = Mock()
        metrics = {
            "metric1": 21,
            "metric2": 42
        }

        self._write_metrics(metrics, mock_file)

        self.assertEquals(mock_file.write.call_args_list,
                          [call('metric2=42\n'),
                           call('metric1=21\n')])

    def test_should_write_metrics_with_prefix(self):
        mock_file = Mock()
        metrics = {
            "metric1": 21,
            "metric2": 42
        }

        self._write_metrics(metrics, mock_file, prefix="example.system.")

        self.assertEquals(mock_file.write.call_args_list,
                          [call('example.system.metric2=42\n'),
                           call('example.system.metric1=21\n')])

    @patch("yadtbroadcastserver.open", create=True)
    @patch("yadtbroadcastserver.BroadcastServerProtocol.metrics_directory")
    def test_should_open_configured_file_for_writing(self, metrics_directory, open_):
        metrics_directory.__iadd__.side_effect = lambda other: '/any/dir/ybc.metrics'
        open_.return_value = MagicMock(spec=file)

        self.ybc.write_metrics_to_file()

        open_.assert_called_with('/any/dir/ybc.metrics', mode='w')

    @patch("yadtbroadcastserver.open", create=True)
    @patch("yadtbroadcastserver.BroadcastServerProtocol.metrics_directory")
    def test_should_not_open_anything_when_no_metric(self, metrics_directory, open_):
        metrics_directory.__nonzero__.side_effect = lambda : False

        open_.return_value = MagicMock(spec=file)

        self.ybc.write_metrics_to_file()

        self.assertFalse(open_.called)

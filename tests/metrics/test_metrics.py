from typing import Any
from unittest import TestCase
from unittest.mock import mock_open, patch

from runrestic.metrics import prometheus, write_metrics


class TestResticMetrics(TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("runrestic.metrics.prometheus.generate_lines", return_value=["line1\n", "line2\n"])
    def test_write_metrics(self, mock_generate_lines, mock_open):
        cfg = {
            "name": "test",
            "metrics": {"prometheus": {"path": "/prometheus_path"}},
        }
        metrics = {
            "backup": {
                "repo1": {
                    "files": {"new": "1", "changed": "2", "unmodified": "3"},
                },
            }
        }
        write_metrics(metrics, cfg)
        mock_generate_lines.assert_called_once_with(metrics, "test")
        mock_open.assert_called_once_with("/prometheus_path", "w")
        fh = mock_open()
        fh.writelines.assert_called_once_with("line1\nline2\n")

    @patch("runrestic.metrics.prometheus.generate_lines", return_value=["line1\n", "line2\n"])
    def test_write_metrics_skipped(self, mock_generate_lines):
        cfg = {
            "name": "test",
            "metrics": {"unknown": {"path": "/other_path"}},
        }
        metrics = {"dummy": "metrics"}
        write_metrics(metrics, cfg)
        mock_generate_lines.assert_not_called()


def mock_metrics_func(metrics, name):
    return f"{name}: {metrics}"


class TestResticMetricsPrometheus(TestCase):
    def setUp(self) -> None:
        prometheus._restic_help_pre_hooks = "restic_help_pre_hooks|"
        prometheus._restic_pre_hooks = "pre:{name}:{rc}:{duration_seconds}|"
        prometheus._restic_help_post_hooks = "restic_help_post_hooks|"
        prometheus._restic_post_hooks = "post:{name}:{rc}:{duration_seconds}|"

    # def setUp(self) -> None:
    #     self.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
    #     self.prometheus_path = Path(self.temp_dir.name) / "example.prom"
    #     self.prometheus_path.mkdir()

    # def tearDown(self) -> None:
    #     self.temp_dir.cleanup()

    @patch("runrestic.metrics.prometheus.backup_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.forget_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.prune_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.check_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.stats_metrics", wraps=mock_metrics_func)
    def test_generate_lines(
        self, mock_stats_metrics, mock_check_metrics, mock_prune_metrics, mock_forget_metrics, mock_backup_metrics
    ):
        scenarios: list[dict[str, Any]] = [
            {
                "name": "all_metrics",
                "metrics": {
                    "backup": {"backup_metrics": 1},
                    "forget": {"forget_metrics": 2},
                    "prune": {"prune_metrics": 3},
                    "check": {"check_metrics": 4},
                    "stats": {"stats_metrics": 5},
                },
            },
            {
                "name": "backup_metrics",
                "metrics": {
                    "backup": {"backup_metrics": 1},
                },
            },
            {
                "name": "no_metrics",
                "metrics": {},
            },
        ]
        genral_metrics = {
            "errors": 10,
            "last_run": 11,
            "total_duration_seconds": 12,
        }
        prometheus._restic_help_general = "restic_help_general"
        prometheus._restic_general = "restic_general:{name}:{last_run}:{errors}:{total_duration_seconds}"
        for sc in scenarios:
            with self.subTest(sc["name"]):
                expected_lines = [
                    "restic_help_general",
                    f"restic_general:{sc['name']}:11:10:12",
                ] + [f"{sc['name']}: {value}" for value in sc["metrics"].values()]
                metrics = sc["metrics"] | genral_metrics
                lines = prometheus.generate_lines(metrics, sc["name"])
                self.assertEqual(list(lines), expected_lines)

    def test_backup_metrics(self):
        metrics = {
            "_restic_pre_hooks": {"duration_seconds": 2, "rc": 0},
            "_restic_post_hooks": {"duration_seconds": 4, "rc": 0},
            "repo1": {
                "files": {"new": "1", "changed": "2", "unmodified": "3"},
                "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
                "added_to_repo": 7,
                "duration_seconds": 9,
                "rc": 0,
            },
            "repo2": {
                "files": {"new": "1", "changed": "2", "unmodified": "3"},
                "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
                "added_to_repo": 5,
                "duration_seconds": 8,
                "rc": 1,
            },
        }
        # check that backup_metrics can be called with sample metrics
        _lines = prometheus.backup_metrics(metrics, "my_backup")
        # check call with simplified output
        prometheus._restic_help_backup = "restic_help_backup|"
        prometheus._restic_backup = "restic_backup_data:{name}:{added_to_repo}:{duration_seconds}|"
        lines = prometheus.backup_metrics(metrics, "my_backup")
        self.assertEqual(
            lines,
            "|".join([
                "restic_help_backup",
                "restic_help_pre_hooks",
                "restic_help_post_hooks",
                "pre:my_backup:0:2",
                "post:my_backup:0:4",
                "restic_backup_data:my_backup:7:9",
                'restic_backup_rc{config="my_backup",repository="repo2"} 1\n',
            ]),
        )

    # @patch("runrestic.metrics.prometheus.generate_lines", return_value=["line1\n", "line2\n"])
    # @patch("builtins.open", new_callable=mock_open)
    # def test_write_prometheus(self, mock_open):
    #     metrics = {
    #         "backup": {
    #             "_restic_pre_hooks": {"duration_seconds": 2, "rc": 0},
    #             "_restic_post_hooks": {"duration_seconds": 2, "rc": 0},
    #             "repo1": {
    #                 "files": {"new": "1", "changed": "2", "unmodified": "3"},
    #                 "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
    #                 "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
    #                 "added_to_repo": 2,
    #                 "duration_seconds": 4,
    #                 "rc": 0,
    #             },
    #             "repo2": {
    #                 "files": {"new": "1", "changed": "2", "unmodified": "3"},
    #                 "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
    #                 "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
    #                 "added_to_repo": 2,
    #                 "duration_seconds": 4,
    #                 "rc": 0,
    #             },
    #         },
    #         "forget": {
    #             "repo1": {
    #                 "removed_snapshots": "1",
    #                 "duration_seconds": 3.2,
    #                 "rc": 0,
    #             },
    #             "repo2": {
    #                 "removed_snapshots": "1",
    #                 "duration_seconds": 3.3,
    #                 "rc": 0,
    #             },
    #         },
    #         "prune": {
    #             "/tmp/restic-repo1": {
    #                 "containing_packs_before": "576",
    #                 "containing_blobs": "95060",
    #                 "containing_size_bytes": 2764885196.8,
    #                 "duplicate_blobs": "0",
    #                 "duplicate_size_bytes": 0.0,
    #                 "in_use_blobs": "95055",
    #                 "removed_blobs": "5",
    #                 "invalid_files": "0",
    #                 "deleted_packs": "2",
    #                 "rewritten_packs": "0",
    #                 "size_freed_bytes": 16679.936,
    #                 "removed_index_files": "2",
    #                 "duration_seconds": 4.2081992626190186,
    #                 "rc": 0,
    #             },
    #             "/tmp/restic-repo2": {
    #                 "containing_packs_before": "575",
    #                 "containing_blobs": "95052",
    #                 "containing_size_bytes": 2765958938.624,
    #                 "duplicate_blobs": "0",
    #                 "duplicate_size_bytes": 0.0,
    #                 "in_use_blobs": "95047",
    #                 "removed_blobs": "5",
    #                 "invalid_files": "0",
    #                 "deleted_packs": "2",
    #                 "rewritten_packs": "0",
    #                 "size_freed_bytes": 16613.376,
    #                 "removed_index_files": "2",
    #                 "duration_seconds": 4.281890153884888,
    #                 "rc": 0,
    #             },
    #         },
    #         "check": {
    #             "/tmp/restic-repo1": {
    #                 "errors": 0,
    #                 "errors_data": 0,
    #                 "errors_snapshots": 0,
    #                 "read_data": 1,
    #                 "check_unused": 1,
    #                 "duration_seconds": 28.380418062210083,
    #                 "rc": 0,
    #             },
    #             "/tmp/restic-repo2": {
    #                 "errors": 0,
    #                 "errors_data": 0,
    #                 "errors_snapshots": 0,
    #                 "read_data": 1,
    #                 "check_unused": 1,
    #                 "duration_seconds": 28.380418062210083,
    #                 "rc": 0,
    #             },
    #         },
    #         "stats": {
    #             "/tmp/restic-repo1": {
    #                 "total_file_count": 885276,
    #                 "total_size_bytes": 18148185424,
    #                 "duration_seconds": 20.471401691436768,
    #                 "rc": 0,
    #             },
    #             "/tmp/restic-repo2": {
    #                 "total_file_count": 885276,
    #                 "total_size_bytes": 18148185424,
    #                 "duration_seconds": 20.466784715652466,
    #                 "rc": 0,
    #             },
    #         },
    #         "errors": 0,
    #         "last_run": 1575577432.185576,
    #         "total_duration_seconds": 62.44408392906189,
    #     }

    #     cfg = {
    #         "name": "test",
    #         "metrics": {"prometheus": {"path": "/prometheus_path"}},
    #     }
    #     write_metrics(metrics, cfg)
    #     mock_open.assert_called_once_with("/prometheus_path", "w")
    #     fh = mock_open()
    #     fh.writelines.assert_called_once()

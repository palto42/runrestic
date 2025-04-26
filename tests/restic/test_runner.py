from argparse import Namespace
from unittest import TestCase
from unittest.mock import patch

from runrestic.restic import runner


class TestResticRunner(TestCase):
    @patch("runrestic.restic.runner.initialize_environment")
    def test_runner_init(self, mock_init_env):
        """
        Test the initialization of the Runner class.
        """
        config = {
            "dummy": "config",
            "repositories": ["dummy-repo"],
            "environment": {"dummy_env": "dummy_value"},
            "metrics": {"prometheus": {"password_replacement": "dummy_pw"}},
        }
        args = Namespace()
        args.dry_run = False
        restic_args = ["dummy-arg"]

        runner_instance = runner.ResticRunner(config, args, restic_args)
        self.assertEqual(runner_instance.args, args)
        self.assertEqual(runner_instance.restic_args, restic_args)
        self.assertTrue(runner_instance.log_metrics)
        self.assertEqual(runner_instance.pw_replacement, "dummy_pw")

    @patch.object(runner.ResticRunner, "init")
    @patch.object(runner.ResticRunner, "backup")
    @patch.object(runner.ResticRunner, "forget")
    @patch.object(runner.ResticRunner, "prune")
    @patch.object(runner.ResticRunner, "check")
    @patch.object(runner.ResticRunner, "stats")
    @patch.object(runner.ResticRunner, "unlock")
    @patch("runrestic.restic.runner.write_metrics")
    def test_run_invokes_all_actions(
        self,
        mock_write_metrics,
        mock_unlock,
        mock_stats,
        mock_check,
        mock_prune,
        mock_forget,
        mock_backup,
        mock_init_method,
    ):
        """
        Test that run() invokes all action methods in the correct conditions and logs metrics.
        """
        config = {
            "name": "test",
            "repositories": ["repo"],
            "environment": {},
            "metrics": {"prometheus": {}},
            "execution": {},
            "backup": {},
            "prune": {},
        }
        args = Namespace(actions=["init", "backup", "prune", "check", "stats", "unlock"])
        args.dry_run = False
        restic_args = []

        runner_instance = runner.ResticRunner(config, args, restic_args)
        runner_instance.metrics["errors"] = 2

        errors = runner_instance.run()
        mock_init_method.assert_called_once()
        mock_backup.assert_called_once()
        mock_forget.assert_called_once()
        mock_prune.assert_called_once()
        mock_check.assert_called_once()
        mock_stats.assert_called_once()
        mock_unlock.assert_called_once()
        mock_write_metrics.assert_called_once_with(runner_instance.metrics, config)
        self.assertEqual(errors, 2)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_backup")
    @patch("runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo)
    def test_backup_metrics(self, mock_redact, mock_parse_backup, mock_mc):
        """
        Test backup() handles success and failure correctly and updates metrics and errors.
        """
        config = {
            "repositories": ["repo1", "repo2"],
            "environment": {},
            "execution": {},
            "backup": {"sources": ["/data"]},
            "metrics": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--opt"]
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_success = {"output": [(0, "")], "time": 0.1}
        process_fail = {"output": [(1, "")], "time": 0.2}
        mock_mc.return_value.run.return_value = [process_success, process_fail]
        mock_parse_backup.return_value = {"parsed": True}

        runner_instance.backup()
        metrics = runner_instance.metrics["backup"]
        self.assertEqual(metrics["repo1"], {"parsed": True})
        self.assertEqual(metrics["repo2"], {"rc": 1})
        self.assertEqual(runner_instance.metrics["errors"], 1)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_forget")
    @patch("runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo)
    def test_forget_metrics(self, mock_redact, mock_parse_forget, mock_mc):
        """
        Test forget() handles metrics parsing and errors correctly.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
            "prune": {"keep-last": 3},
        }
        args = Namespace(dry_run=True)
        restic_args = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_forget.return_value = {"forgotten": True}

        runner_instance.forget()
        metrics = runner_instance.metrics["forget"]
        self.assertEqual(metrics["repo"], {"forgotten": True})
        self.assertEqual(runner_instance.metrics["errors"], 0)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_new_prune", side_effect=IndexError)
    @patch("runrestic.restic.runner.parse_prune")
    @patch("runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo)
    def test_prune_metrics_old_prune(self, mock_redact, mock_parse_prune, mock_new_prune, mock_mc):
        """
        Test prune() falls back to parse_prune when parse_new_prune raises IndexError.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_prune.return_value = {"pruned": True}

        runner_instance.prune()
        metrics = runner_instance.metrics["prune"]
        self.assertEqual(metrics["repo"], {"pruned": True})

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_new_prune")
    @patch("runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo)
    def test_prune_metrics_new_prune(self, mock_redact, mock_parse_new_prune, mock_mc):
        """
        Test prune() uses parse_new_prune when available.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_new_prune.return_value = {"new_pruned": True}

        runner_instance.prune()
        metrics = runner_instance.metrics["prune"]
        self.assertEqual(metrics["repo"], {"new_pruned": True})

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo)
    @patch("runrestic.restic.runner.parse_stats")
    def test_stats_metrics(self, mock_parse_stats, mock_redact, mock_mc):
        """
        Test stats() calls parse_stats and updates metrics correctly.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--verbose"]
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_stats.return_value = {"stats": True}

        runner_instance.stats()
        metrics = runner_instance.metrics["stats"]
        self.assertEqual(metrics["repo"], {"stats": True})
        self.assertEqual(runner_instance.metrics["errors"], 0)

    @patch("runrestic.restic.runner.MultiCommand")
    def test_check_metrics(self, mock_mc):
        """
        Test check() parses errors from output correctly.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
            "check": {"checks": ["check-unused", "read-data"]},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        output_str = "error: load <snapshot/1234>\nPack ID does not match, corrupted"
        process_info = {"output": [(1, output_str)], "time": 0.5}
        mock_mc.return_value.run.return_value = [process_info]

        runner_instance.check()
        stats = runner_instance.metrics["check"]["repo"]
        self.assertEqual(stats["errors"], 1)
        self.assertEqual(stats["errors_snapshots"], 1)
        self.assertEqual(stats["errors_data"], 1)
        self.assertEqual(stats["read_data"], 1)
        self.assertEqual(stats["check_unused"], 1)
        self.assertEqual(stats["duration_seconds"], 0.5)
        self.assertEqual(stats["rc"], 1)
        self.assertEqual(runner_instance.metrics["errors"], 1)

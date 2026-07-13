from agentdojo.task_suite import register_suite
from safeconfirm_bridge.suites.banking.task_suite import task_suite as banking_task_suite
from safeconfirm_bridge.suites.workspace.task_suite import task_suite as workspace_task_suite

BENCHMARK_VERSION = "safeconfirm_l1"

register_suite(workspace_task_suite, BENCHMARK_VERSION)
register_suite(banking_task_suite, BENCHMARK_VERSION)

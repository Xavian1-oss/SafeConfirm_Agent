from pathlib import Path

from agentdojo.default_suites.v1.banking.task_suite import TOOLS, BankingEnvironment
from agentdojo.functions_runtime import make_function
from agentdojo.task_suite import TaskSuite
from safeconfirm_bridge.case_registry import cases_for_suite
from safeconfirm_bridge.task_factory import register_cases_for_suite

DATA_PATH = Path(__file__).resolve().parents[2] / "data/suites/safeconfirm_banking"

task_suite = TaskSuite(
    "safeconfirm_banking",
    BankingEnvironment,
    [make_function(tool) for tool in TOOLS],
    DATA_PATH,
)

register_cases_for_suite(task_suite, cases_for_suite("safeconfirm_banking"), BankingEnvironment)

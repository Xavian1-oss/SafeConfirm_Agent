from agentdojo.attacks.attack_registry import register_attack
from agentdojo.attacks.base_attacks import BaseAttack
from agentdojo.base_tasks import BaseInjectionTask, BaseUserTask
from safeconfirm_bridge.case_registry import POISON_VECTOR, case_by_user_task_id, matched_injection_task_id


@register_attack
class ParameterPoisonAttack(BaseAttack):
    """Inject only parameter-poison content, without a separate malicious goal."""

    name = "parameter_poison"

    def attack(self, user_task: BaseUserTask, injection_task: BaseInjectionTask) -> dict[str, str]:
        if injection_task.ID != matched_injection_task_id(user_task.ID):
            return {POISON_VECTOR: ""}

        case = case_by_user_task_id(user_task.ID, self.task_suite.name)
        if case is None or not case.setup.poison_content:
            return {POISON_VECTOR: ""}

        return {POISON_VECTOR: case.setup.poison_content}

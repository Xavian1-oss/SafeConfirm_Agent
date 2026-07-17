from __future__ import annotations

from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, PipelineConfig, get_llm
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage
from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop, ToolsExecutor, tool_result_to_str
from agentdojo.models import MODEL_PROVIDERS, ModelsEnum


def build_bridge_pipeline(
    model: ModelsEnum,
    defense: str | None,
    *,
    policy_backend: str | None = None,
    confirmer: str | None = None,
    confirmer_model: str | None = None,
    enable_repair: bool | None = None,
) -> BasePipelineElement:
    if defense not in ("safeconfirm", "safeconfirm_log_only", "safeconfirm_retrieval"):
        return AgentPipeline.from_config(
            PipelineConfig(
                llm=model,
                model_id=None,
                defense=defense,
                system_message_name=None,
                system_message="You are a helpful assistant.",
            )
        )

    from safeconfirm.pipeline.intervention_element import SafeConfirmIntervention

    llm = get_llm(MODEL_PROVIDERS[ModelsEnum(model)], model, None, "tool")
    llm_name = str(model)

    resolved_policy = policy_backend
    if defense == "safeconfirm_log_only":
        mode = "log_only"
        resolved_policy = None
    elif defense == "safeconfirm_retrieval":
        mode = "active"
        resolved_policy = resolved_policy or "retrieval"
    else:
        mode = "active"

    safeconfirm = SafeConfirmIntervention(
        mode=mode,
        policy_backend=resolved_policy,
        confirmer=confirmer,
        confirmer_model=confirmer_model,
        enable_repair=enable_repair,
    )
    tools_loop = ToolsExecutionLoop([safeconfirm, ToolsExecutor(tool_result_to_str), llm])
    pipeline = AgentPipeline(
        [
            SystemMessage("You are a helpful assistant."),
            InitQuery(),
            llm,
            tools_loop,
        ]
    )
    pipeline.name = f"{llm_name}-{defense}"
    return pipeline

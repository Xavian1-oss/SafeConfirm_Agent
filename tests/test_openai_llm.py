from agentdojo.agent_pipeline.llms.openai_llm import _message_to_openai
from agentdojo.types import ChatSystemMessage, text_content_block_from_string


def test_system_message_uses_system_role_for_deepseek():
    message: ChatSystemMessage = {
        "role": "system",
        "content": [text_content_block_from_string("You are helpful.")],
    }
    converted = _message_to_openai(message, "deepseek-chat")
    assert converted["role"] == "system"


def test_system_message_uses_developer_role_for_reasoning_models():
    message: ChatSystemMessage = {
        "role": "system",
        "content": [text_content_block_from_string("You are helpful.")],
    }
    converted = _message_to_openai(message, "o3-mini")
    assert converted["role"] == "developer"

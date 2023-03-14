"""An agent designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from langchain.agents.agent import Agent
from langchain.agents.assistant.prompt import PREFIX, SUFFIX
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMChain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate
from langchain.tools.base import BaseTool


class AssistantAgent(Agent):
    """An agent designed to hold a conversation in addition to an specialized assistant tool."""

    ai_prefix: str = "AI"

    @property
    def _agent_type(self) -> str:
        """Return Identifier of agent type."""
        return "conversational-assistant"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Assistant: "

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "AI:"

    @property
    def _stop(self) -> List[str]:
        return [f"\n{self.observation_prefix}", "\nHuman:", "\nEXAMPLE", "\nNEW INPUT:"]

    @classmethod
    def create_prompt(
        cls,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        ai_prefix: str = "AI",
        input_variables: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """Create prompt in the style of the zero shot agent.

        Args:
            prefix: String to put before the list of tools.
            suffix: String to put after the list of tools.
            input_variables: List of input variables the final prompt will expect.

        Returns:
            A PromptTemplate with the template assembled from the pieces here.
        """
        template = "\n\n".join([prefix.format(ai_prefix=ai_prefix), suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "agent_scratchpad"]
        return PromptTemplate(template=template, input_variables=input_variables)

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return self.ai_prefix

    @staticmethod
    def _remove_after(line: str) -> bool:
        if "anything else I can help" in line:
            return True
        if "anything else you would like" in line:
            return True
        if "Previous conversation history" in line:
            return True

        return False
    
    @staticmethod
    def _fix_chatgpt(text: str) -> str:
        idx = text.find("\n\nNote: ")
        if idx >= 0:
            text = text[:idx + 1]
        # Remove redundant questions, to keep history shorter
        lines = text.split("\n")
        new_lines = []
        for l in lines:
            # do not keep anthing afterwards
            if __class__._remove_after(l):
                break
            new_lines.append(l)
        text = "\n".join(new_lines)

        # text = text.replace("\nHumman:", "\nAI:")
        # for term in ["\nOutput:\n"]:
        #     prev_action_idx = text.find(term)
        #     if prev_action_idx >= 0:
        #         text = text[prev_action_idx + 8:]
        # ChatGPT fix: if the Human role is assumed by smart bot!
        # for term in ["\nNew input:", "\nFor example:"]:
        #     prev_action_idx = text.find(term)
        #     if prev_action_idx >= 0:
        #         text = text[:prev_action_idx + 1]
        return text
    
    def _fix_text(self, text: str) -> str:
        text = self._fix_chatgpt(text)
        return f"{text}\nAI:"

    def _extract_tool_and_input(self, llm_output: str) -> Optional[Tuple[str, str]]:
        # print(f"bbbbbbbbbbbbbbbbbbbbbbbbbb {llm_output}")
        llm_output = self._fix_chatgpt(llm_output)
        cmd_idx = llm_output.rfind("Assistant,")
        if cmd_idx >= 0:
            cmd = llm_output[cmd_idx + len("Assistant,"):].strip()
            search_idx = cmd.lower().find("bing search")
            if search_idx >= 0:
                 action_input = cmd[search_idx + len("bing serach") + 1:]
                 return "Bing Search", action_input
            cmd_idx = cmd.rfind(" ")
            action_input = cmd[cmd_idx + 1:].strip()
            if action_input.endswith((".", "?")):
                action_input = action_input[:-1]
            if "/" not in action_input and "http" not in action_input:
                return "Final Answer", ""
            cmd = cmd[:cmd_idx + 1].lower()
            if "receipt" in cmd:
                action = "Receipt Understanding"
            elif "business card" in cmd:
                action = "Business Card Understanding"
            elif "ocr" in cmd:
                action = "OCR Understanding"
            elif "celebrit" in cmd:
                action = "Celebrity Understanding"
            elif "landmark" in cmd:
                action = "Bing Search"
            elif "product" in cmd:
                action = "Bing Search"
            else:
                action = "Image Understanding"
            return action, action_input
        
        if f"{self.ai_prefix}:" in llm_output:
            return self.ai_prefix, llm_output.split(f"{self.ai_prefix}:")[-1].strip()
        return self.ai_prefix, llm_output.strip()

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        ai_prefix: str = "AI",
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        """Construct an agent from an LLM and tools."""
        cls._validate_tools(tools)
        prompt = cls.create_prompt(
            ai_prefix=ai_prefix,
            prefix=prefix,
            suffix=suffix,
            input_variables=input_variables,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(
            llm_chain=llm_chain, allowed_tools=tool_names, **kwargs
        )

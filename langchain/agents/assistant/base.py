"""An agent designed to hold a conversation in addition to using tools."""
from __future__ import annotations

import re
import json
from typing import Any, List, Optional, Sequence, Tuple, Dict

from langchain.agents.agent import Agent
from langchain.agents.assistant.prompt import PREFIX, SUFFIX, SYSTEM_TRIGGER, SYSTEM_TRIGGER_TASK
from langchain.agents.assistant.prompt_od import PREFIX as PREFIX_OD, SUFFIX as SUFFIX_OD
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMChain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate
from langchain.schema import AgentAction
from langchain.tools.base import BaseTool
from langchain.utils import get_url_path

class MMAssistantAgent(Agent):
    """An agent designed to hold a conversation in addition to an specialized assistant tool."""

    ai_prefix: str = "AI"
    llm_chain_od: LLMChain
    llm_chain_task: LLMChain

    @property
    def _agent_type(self) -> str:
        """Return Identifier of agent type."""
        return "conversational-mm-assistant"

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "<|im_sep|>Assistant\nAssistant:\n"

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "<|im_sep|>AI\n"

    @property
    def _stop(self) -> List[str]:
        return ["<|im_end|>"]

    @classmethod
    def create_prompt(
        cls,
        prefix: str = PREFIX,
        suffix: str = SUFFIX,
        system_trigger: str = "",
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
        if system_trigger:
            template = "\n\n".join([prefix.format(ai_prefix=ai_prefix, system_trigger=system_trigger), suffix])
        else:
            template = "\n\n".join([prefix.format(ai_prefix=ai_prefix), suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "agent_scratchpad"]
        return PromptTemplate(template=template, input_variables=input_variables)

    @property
    def finish_tool_name(self) -> str:
        """Name of the tool to use to finish the chain."""
        return "<|im_end|>"

    @staticmethod
    def _fix_chatgpt(text: str) -> str:
        text = text.replace("<|im_end|>\n", "\n")
        text = text.replace("<|im_end|>", "")
        text = text.replace("<|im_sep|>AI\n", "")
        lines = text.split("\n")
        new_lines = []
        for l in lines:
            l_lower = l.lower()
            for term in ["thank you for letting me", "is there anything else ", "or is there something else "]:
                idx = l_lower.find(term)
                if idx >= 0:
                    l = l[:idx]
                    break
            if not l:
                continue
            new_lines.append(l)
        text = "\n".join(new_lines)

        return text
    
    def _fix_text(self, text: str) -> str:
        text = self._fix_chatgpt(text)
        if "Assistant, " in text:
            return text
        return f"{text}\n{self.llm_prefix}"

    @staticmethod
    def _extract_tools(llm_output: str) -> List[List[str, str]]:
        # TODO: separate llm to decide the task

        cmd_idx = llm_output.rfind("Assistant,")
        if cmd_idx < 0:
            return
        cmd = llm_output[cmd_idx + len("Assistant,"):].strip()
        if "photo edit" in llm_output or "image edit" in llm_output:
            return [["Photo Editing", cmd]]
        action_inputs:List[str] = []
        action_input_idx, action_input_end_idx, action_input = get_url_path(cmd, return_end=True)
        action = None
        if action_input_idx >= 0:
            sub_cmd = cmd[:action_input_idx].strip().lower()
            while action_input_idx >= 0:
                action_inputs.append(action_input)
                action_input_idx, action_input_end_idx, action_input = get_url_path(cmd[action_input_end_idx:], return_end=True)
        else:
            sub_cmd = ""
        # TODO: need a separate chain to decide OCR specialization, 
        #       perhaps we do genric OCR (or receipt) then if we see an invoice then we do invoice
        if "invoice" in sub_cmd:
            action = "Invoice Understanding"
        elif "receipt" in sub_cmd:
            action = "Receipt Understanding"
        elif "business card" in sub_cmd:
            action = "Business Card Understanding"
        elif "ocr" in sub_cmd:
            if "table" in sub_cmd:
                action = "Layout Understanding"
            else:
                action = "OCR Understanding"
        elif "celebrit" in sub_cmd or "facial rec" in sub_cmd or " faces " in sub_cmd:
            action = "Celebrity Understanding"
        elif "landmark" in sub_cmd:
            action = "Bing Search"
        elif "brand" in sub_cmd:
            action = "Bing Search"
        elif "bing search" in sub_cmd:
            action = "Bing Search"
        elif "objects" in sub_cmd:
            action = "Image Understanding"
        if not action_inputs:
            if not action:
                # if no image and no action
                if cmd.endswith("?") or sub_cmd.startswith("search "):
                    action = "Bing Search"
            if action == "Bing Search":
                action_input = cmd
                action_input_lower = action_input.lower()
                for term in ["bing search for", "bing search", "search for", "search"]:
                    search_idx = action_input_lower.find(term)
                    if search_idx >= 0:
                        action_input = cmd[search_idx + len(term):].strip()
                        break
                return [[action, action_input]]
            return [[action, ""]]
        assert action_inputs
        parsed_output = []
        for action_input in action_inputs:
            action_input_lower = action_input.lower()
            new_action = action
            if not new_action:
                if ((" is written" in sub_cmd) or (" text" in sub_cmd) or sub_cmd.endswith(" say?")):
                    new_action = "OCR Understanding"
                elif sub_cmd.startswith("parse ") or sub_cmd.startswith("analyze "):
                    new_action = "OCR Understanding"
            if new_action == "Image Understanding" and action_input_lower.endswith(".pdf"):
                # Invoice is more specific
                new_action = "OCR Understanding"
            if new_action == "Receipt Understanding" and "invoice" in action_input_lower:
                # Invoice is more specific
                new_action = "Invoice Understanding"
            if new_action == "OCR Understanding":
                if "invoice" in action_input_lower:
                    new_action = "Invoice Understanding"
                elif "receipt" in action_input_lower:
                    new_action = "Receipt Understanding"
                elif "table" in action_input_lower:
                    new_action = "Layout Understanding"

            if not new_action and (sub_cmd.startswith("search ") or  " the name of " in sub_cmd):
                new_action = "Bing Search"
            parsed_output.append([new_action, action_input])
        return parsed_output
        
    def _extract_tool_and_input(self, llm_output: str, tries=0) -> Optional[Tuple[str, str]]:
        # TODO: this should be a separate llm as a tool to decide the correct tool(s) here
        llm_output = self._fix_chatgpt(llm_output)
        tool_list = []
        retry = False
        parsed_output = self._extract_tools(llm_output)
        while parsed_output is not None:
            for action, action_input in parsed_output:
                if not action or not action_input:
                    retry = True
                    continue
                tool_list.append([action, action_input])
            cmd_idx = llm_output.rfind("Assistant,")
            if cmd_idx >= 0:
                llm_output = llm_output[:cmd_idx].strip()
            parsed_output = self._extract_tools(llm_output)

        if retry and tries < 4 and not tool_list:
            # Let the model rethink
            return
        if not tool_list:
            return self.finish_tool_name, llm_output.strip()
        if len(tool_list) == 1:
            action, action_input = tool_list[0]
            return action, action_input
        return "MultiAction", json.dumps(tool_list)
    
    def _get_next_action(self, full_inputs: Dict[str, str]) -> AgentAction:
        full_output = self.llm_chain_od.predict(**full_inputs)
        # print(f"od: {full_output}")
        parsed_output = self._extract_tool_and_input(full_output)
        if parsed_output and parsed_output[0] != self.finish_tool_name:
            full_inputs["agent_scratchpad"] += full_output
            return AgentAction(
                tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
            )
        # Keep the thoughts
        output = ""
        for line in full_output.split("\n"):
            if re.match(r"^\s*\d+\.\s", line):
                output += line + "\n"
        full_output = ""
        if output:
            full_output =  output + f"\n{self.llm_prefix}"
        full_output += self.llm_chain.predict(**full_inputs)
        parsed_output = self._extract_tool_and_input(full_output)
        tries = 0
        while parsed_output is None:
            full_output = self._fix_text(full_output)
            full_inputs["agent_scratchpad"] += full_output
            output = self.llm_chain.predict(**full_inputs)
            full_output += output
            tries += 1
            parsed_output = self._extract_tool_and_input(full_output, tries=tries)
        # try to get more tasks
        if parsed_output[0] == self.finish_tool_name and "Assistant," not in full_output:
            output = self.llm_chain_task.predict(**full_inputs)
            parsed_output_task = self._extract_tool_and_input(output)
            if parsed_output_task and parsed_output_task[0] != self.finish_tool_name:
                full_inputs["agent_scratchpad"] += full_output
                full_output += "\n" + output
                return AgentAction(
                    tool=parsed_output_task[0], tool_input=parsed_output_task[1], log=full_output
                )
        return AgentAction(
            tool=parsed_output[0], tool_input=parsed_output[1], log=full_output
        )

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLLM,
        tools: Sequence[BaseTool],
        callback_manager: Optional[BaseCallbackManager] = None,
        ai_prefix: str = "AI",
        input_variables: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Agent:
        """Construct an agent from an LLM and tools."""
        cls._validate_tools(tools)
        prompt = cls.create_prompt(
            ai_prefix=ai_prefix,
            prefix=PREFIX,
            suffix=SUFFIX,
            system_trigger=SYSTEM_TRIGGER,
            input_variables=input_variables,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        prompt_od = cls.create_prompt(
            ai_prefix=ai_prefix,
            prefix=PREFIX_OD,
            suffix=SUFFIX_OD,
            input_variables=input_variables,
        )
        llm_chain_od = LLMChain(
            llm=llm,
            prompt=prompt_od,
            callback_manager=callback_manager,
        )
        prompt_task = cls.create_prompt(
            ai_prefix=ai_prefix,
            prefix=PREFIX,
            suffix=SUFFIX,
            system_trigger=SYSTEM_TRIGGER_TASK,
            input_variables=input_variables,
        )
        llm_chain_task = LLMChain(
            llm=llm,
            prompt=prompt_task,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(
            llm_chain=llm_chain, llm_chain_od=llm_chain_od, llm_chain_task=llm_chain_task, allowed_tools=tool_names, **kwargs
        )

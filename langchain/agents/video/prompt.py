# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}! My name is Human.
We are going to review videos using the transcript.
<|im_end|>

Answer any question right away if you can.
Use the video transcript to answer the questions.
"""
SUFFIX = """

{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}! My name is Human.
We are going to review videos using the script or transcript.
Any time you cannot answer my question, you can ask my Assistant.
Assistant can Stream search on video streaming services on the Internet
<|im_end|>

Answer any question right away if you can.
Use the video script or transcript to answer the questions.
Keep the tasks Assistant can handle in mind.
Gather your thoughts and observations in a list then if needed ask Assistant a task

<|im_start|>Human
can you find where to watch this episode?
<|im_sep|>{ai_prefix}
1. I do not have that information but you can watch on various streaming platforms
2. This question requires Internet search
Assistant, Stream search where you can watch this famous 1995 episode about birds 
<|im_sep|>Assistant
results from internet search
*
<|im_end|>
"""
SUFFIX = """

{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

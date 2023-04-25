# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}! My name is Human.
We are going to review videos using the script or transcript.
Any time you cannot answer my question, you can ask my Assistant.
Assistant can perform Internet search for you
<|im_end|>

Answer any question right away if you can.
Use the video script or transcript to answer the questions.
Gather your thoughts and observations in a list then if needed ask Assistant for internet search

<|im_start|>Human
Here is the video script for this movie
<|im_sep|>AI
This is a movie in which Mr. Bean cheats
<|im_start|>Human
can you find where I can watch this movie in theaters now?
<|im_sep|>{ai_prefix}
1. I do not have that information.
2. This question requires further context.
3. This question requires Internet search.
Assistant, Bing search where you can watch Mr. Bean comedy movie now in which he cheats
<|im_sep|>Assistant
results from internet search
*
<|im_end|>"""
SUFFIX = """

{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

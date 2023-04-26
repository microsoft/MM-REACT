# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}!
We are going to review videos using the script or transcript.
Any time you cannot provide an answer, you can ask my Assistant for help.
Assistant can Stream search video streaming services, and search the Internet
These are the tasks that Assistant can handle: Stream search, Bing search
<|im_end|>

Use the video script or transcript to answer the questions if you can.
Keep the tasks Assistant can handle in mind.
Gather your thoughts and observations in a list and ask Assistant a task

<|im_start|>Human
How old is main character today?
<|im_sep|>{ai_prefix}
1. I do not have that information
2. This question requires Internet search
Assistant, Bing search how old is Brad Pitt
<|im_sep|>Assistant
results from internet search
*
<|im_end|>
<|im_start|>Human
can you find where to watch this episode?
<|im_sep|>{ai_prefix}
1. I cannot provide direct links
2. This question requires Stream search
Assistant, Stream search where you can watch this famous 1995 episode about birds 
<|im_sep|>Assistant
results from internet search
*
<|im_end|>
"""
SUFFIX = """

{chat_history}

Use the video script or transcript to answer the questions if you can.
Keep the tasks Assistant can handle in mind.
Gather your thoughts and observations in a list and ask Assistant a task

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

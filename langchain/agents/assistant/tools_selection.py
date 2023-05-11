# flake8: noqa
PREFIX = """<|im_start|>system
These are the tasks that Assistant can handle: photo editing, facial recognition, OCR, Bing
If there is text in an image, tool is OCR
Image types that have text (sign, label, plan, invoice, receipt, business card, money, table), require OCR tool.
pdf files require OCR tool

Assistant is asked to perform a task: photo editing, facial recognition, OCR, Bing
List the tools and input to each tool for Assistant
<|im_end|>

{system_trigger}
<|im_sep|>Human
1. There are two images in the input
2. The first image is a business card image
3. There is text and numbers in images
4. Reading the text requires OCR
Assistant, do OCR to this business card image to find the text  https://i.ibb.co/tsQ0Myn/00.jpg

Assistant, do OCR to this image to find the text  https://i.ibb.co/YJbmKg4/somX1.png
<|im_sep|>{ai_prefix}
1. OCR, https://i.ibb.co/tsQ0Myn/00.jpg
2. OCR, https://i.ibb.co/YJbmKg4/somX1.png
<|im_sep|>Human
1. This image should be edited
2. This is a photo editing task
Assistant, Move the logo in this business card image to the right  /tmp/path/to/x_d_0(2).jpg
<|im_sep|>{ai_prefix}
1. photo editing, /tmp/path/to/x_d_0(2).jpg
<|im_end|>

<|im_start|>system
{system_trigger}
<|im_end|>
"""
SUFFIX = """
{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

SYSTEM_TRIGGER = """
Assistant is asked to perform a task: photo editing, facial recognition, OCR, Bing
List the tools and input to each tool for Assistant
"""

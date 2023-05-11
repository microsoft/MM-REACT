# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}!
Let me introduce you to Assistant. He is great at understanding what is going on in any image (e.g. jpg, png, jpeg).
Any time there is a new image in our conversation that you want to know about objects in the image you could ask Assistant by addressing him.
<|im_end|>

Keep the last question and conversation in mind
Detect if there is a new image in the input 
If new image, ask Assistant to detect objects in the image
Keep the conversation in mind, List your thoughts and observations

<|im_start|>Human
My prescription https://i.ibb.co/tsQ0Myn/00.jpg
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. The image is new in the conversation
Assistant, what objects do you see in this prescription image? https://i.ibb.co/tsQ0Myn/00.jpg
<|im_sep|>Assistant
Assistant:
https://i.ibb.co/tsQ0Myn/00.jpg
Image description is: a bottle of medicine.

This image contains objects and their descriptions, object tags

List of object descriptions, and their location in this image:
heart 50 61

List of object tags seen in this image:
pills
text
prescription instructions
<|im_sep|>system
In this image 50 61 is the x, y cartesian coordinate of detected heart
<|im_sep|>{ai_prefix}
1. This is a pill bottle
2. There is text in the image
<|im_end|>
<|im_start|>Human
Move the logo in this image to the right https://i.ibb.co/tsQ0Myn/00.jpg
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. The image is not new in the conversation
<|im_end|>

<|im_start|>Human
https://tinyurl.com/foo092001.jpeg
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. The image is new in the conversation
Assistant, what objects do you see in this image? https://tinyurl.com/foo092001.jpeg
<|im_sep|>Assistant
Assistant:
https://tinyurl.com/foo092001.jpeg
Image description is: a peaceful scene
<|im_sep|>{ai_prefix}
1. The image a peaceful sceneray
<|im_end|>

<|im_start|>Human
Apple is my favourite fruit :--)
<|im_sep|>{ai_prefix}
1. There is no image in the input
<|im_end|>
<|im_start|>Human
What is the most expensive type of my favourite fruit in the US?
<|im_sep|>{ai_prefix}
1. There is no image in the input
<|im_end|>

<|im_start|>Human
what do you know about this image? /tmp/path/to/x_d_invoice(2).jpg
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. The image is new in the conversation
Assistant, what objects do you see in this image? /tmp/path/to/x_d_invoice(2).jpg
<|im_sep|>Assistant
Assistant:
/tmp/path/to/x_d_invoice(2).jpg
Image description is: lines and tables
<|im_sep|>{ai_prefix}
1. There are lines and tables in the image
2. The image is likely an invoice
<|im_end|>
"""
SUFFIX = """

<|im_start|>system
Keep the last question and conversation in mind
Detect if there is a new image in the input 
If new image, ask Assistant to detect objects in the image
Keep the conversation in mind, List your thoughts and observations
<|im_end|>

{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

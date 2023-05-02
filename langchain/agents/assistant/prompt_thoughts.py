# flake8: noqa
PREFIX = """<|im_start|>system
Hey {ai_prefix}!
Now let me introduce you to Assistant. He is great at understanding what is going on in any image (e.g. jpg, png, jpeg).
Any time there is an image in our conversation that you want to know about objects description, texts, OCR (optical character recognition), people, celebrities inside of the image you could ask Assistant by addressing him. 

These are the tasks that Assistant can handle for an image: photo editing, celebrities, objects, OCR, Bing
<|im_end|>

Keep the question and conversation in mind.
Gather your thoughts and observations in a list
<|im_start|>Human
My business card https://i.ibb.co/tsQ0Myn/00.jpg
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. This is your business card image
3. This is an image that has text
4. Reading the text requires OCR
<|im_end|>
<|im_start|>Human
Move the logo in this image to the right
<|im_sep|>{ai_prefix}
1. The image should be edited
2. This is a photo editing task
<|im_end|>

<|im_start|>Human
https://tinyurl.com/foo092001.jpeg
<|im_sep|>{ai_prefix}
1. There is an image in the input
<|im_end|>

<|im_start|>Human
Apple is my favourite fruit :--)
<|im_sep|>{ai_prefix}
1. There is no image in the input
2. I keep this in mind
<|im_end|>
<|im_start|>Human
What is the most expensive type of my favourite fruit in the US?
<|im_sep|>{ai_prefix}
1. Your favourite fruit is apple
2. I do not have that information.
3. This question requires Internet search.
<|im_end|>


<|im_start|>Human
What is the result of the first equation in this image: https://i.ibb.co/YJbmKg4/somX1.png
<|im_sep|>{ai_prefix}
1. There is an image in the input
2. This is an image that has text
3. Reading the text requires OCR
<|im_end|>

<|im_start|>Human
When is this photo taken?
<|im_sep|>{ai_prefix}
1. I do not have that information.
2. This question requires Internet image search.
<|im_end|>

<|im_start|>Human
what do you know about this image? /tmp/path/to/x_d_0(2).jpg
<|im_sep|>{ai_prefix}
1. There is an image in the input
<|im_sep|>Assistant
Image description is: a bottle of medicine.

This image contains objects and their descriptions, object tags

List of object descriptions, and their location in this image:
heart 50 61

List of object tags seen in this image:
pills
text
prescription instructions
<|im_sep|>{ai_prefix}
1. This image is likely a pill bottle with labels and is related to heart
2. Looking at the tags this is an image that has text
3. Reading the text requires OCR
<|im_end|>
<|im_start|>Human
where can I buy this medicine? and how much is the price in Euros?
<|im_sep|>{ai_prefix}
1. I do not have that information.
2. This question requires further context.
3. This question requires Internet search.
<|im_end|>
"""
SUFFIX = """

<|im_start|>system
Keep the question and conversation in mind.
Gather your thoughts and observations in a list
<|im_end|>

{chat_history}

<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

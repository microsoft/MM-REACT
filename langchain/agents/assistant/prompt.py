# flake8: noqa
PREFIX = """<|im_start|>system
Human: Hey {ai_prefix}! My name is Human. 
Now let me introduce you to Assistant. He is great at understanding what is going on in any image.
Any time there is an image in our conversation that you want to know about objects description, texts, OCR (optical character recognition), people, celebrities inside of the image you could ask Assistant by addressing him. 
Make sure to provide Assistant with the best concise task that Assistant can handle.

These are the tasks that Assistant can handle for an image: photo editing, celebrities, landmarks, brands, business card, receipt, objects, OCR, Bing
If the task does not fit any of the above, make sure the question has the word objects in it.
To ask about an image without any description, make sure the question has the word objects in it.
To ask about an image that could be a business card, make sure the question has the word business card in it.
To ask about an image that could be a receipt, make sure the question has the word receipt in it.
To ask about an image that likely has text (e.g. text, stamp, currency, money, dollar, paper, banknote, floor plan in the image tags), make sure the question has the word OCR in it.
To ask about the identity of people (celebrities) in an image, make sure the question has the word celebrities in it, to see if any one of them are famous.
<|im_end|>


<|im_start|>{ai_prefix}
This is a business card image.
<|im_sep|>{ai_prefix}
Assistant, what OCR text do you see in this business card?  https://i.ibb.co/tsQ0Myn/00.jpg
<|im_sep|>Assistant
This is an image
This image contains text

List of texts (words) seen in this image:
CONTOSO
Cell: +1 (989) 123-4567
Tel: +1 (989) 213-5674 Fax: +1 (989) 312-6745 4001 1st Ave NE Redmond, WA 98052
Jake Smith Researcher Cloud & AI Department jake.smith@contoso.com https://www.contoso.com/

<|im_sep|>{ai_prefix}
This is a ... business card belonging to ...
<|im_end|>


<|im_start|>{ai_prefix}
This is an image. Assistant, what objects do you see in this image?  https://tinyurl.com/foo092001
<|im_sep|>Assistant
This is an image with description a group of men playing football.

This image contains objects and their descriptions, object tags

List of object descriptions, and their location in this image:
soccer ball 1476 993
shoe 1300 1200

List of object tags seen in this image:
athletic game
football
soccer

<|im_sep|>{ai_prefix}
This is a ... football .. shoe kicking a ball
<|im_end|>

In this example 1476, 993 is the coordinate of soccer ball
In this example 1300, 1200 is the coordinate of shoe


<|im_start|>Human
What is the result of the first equation in this image: https://i.ibb.co/YJbmKg4/somX1.png
<|im_sep|>{ai_prefix}
This is an image with text.
<|im_sep|>{ai_prefix}
Assistant, what is the OCR texts in this image?  https://i.ibb.co/YJbmKg4/somX1.png
<|im_sep|>Assistant
This is an image
This image contains handwritten text

List of texts (words) seen in this image:
4x2+5=
1/sqrt(9)=

<|im_sep|>{ai_prefix}
The equation ...
<|im_end|>


<|im_start|>Human
https://i.ibb.co/XJbmhg4/mY09.png
<|im_sep|>{ai_prefix}
This is an image. Assistant, what objects do you see in this image? https://i.ibb.co/XJbmhg4/mY09.png
<|im_sep|>Assistant
This is an image with description a dog playing with a man.

This image contains objects and their descriptions, object tags

List of object descriptions, and their location in this image:
dog 11 99
person 60 99

List of object tags seen in this image:
animal
zoo
dolphine
person

Detected faces, and their location in this image:
man 12 100

<|im_sep|>{ai_prefix}
There is a face detected in this image.
<|im_sep|>{ai_prefix}
Assistant, are there any celebrities in this image? https://i.ibb.co/XJbmhg4/mY09.png
<|im_end|>


<|im_start|>Human
what do you know about this image? /tmp/path/to/x_d_0(2).jpg
<|im_sep|>{ai_prefix}
This is an image. Assistant, what objects do you see in this image? /tmp/path/to/x_d_0(2).jpg
<|im_sep|>Assistant
This is an image with description a bottle of medicine.

This image contains objects and their descriptions, object tags

List of object descriptions, and their location in this image:
heart 100 201

List of object tags seen in this image:
pills
text
prescription instructions
<|im_sep|>{ai_prefix}
This image is likely a pill bottle with labels.
<|im_sep|>{ai_prefix}
Let me see what is the text
<|im_sep|>{ai_prefix}
Assistant, what is the OCR texts in this image? /tmp/path/to/x_d_0(2).jpg
<|im_sep|>Assistant
This is an image
This image contains text

List of texts (words) seen in this image:
SPRING VALLEY.
Supports Health
SUPPLEMENT

<|im_sep|>{ai_prefix}
This is medicine supplement pills by SPRING VALLEY
<|im_end|>
<|im_start|>Human
where can I buy this medicine? and how much is the price in Euros?
<|im_sep|>{ai_prefix}
I do not have that information.
<|im_sep|>{ai_prefix}
This question requires Bing search. 
<|im_sep|>{ai_prefix}
Assistant, Bing search where can I buy SPRING VALLEY supplement pills? and how much is the price in Euros?
<|im_end|>


<|im_start|>Human
/a/c0%5/XX99096.jpg
<|im_sep|>{ai_prefix}
This is an image. Assistant, what objects do you see in this image? /a/c0%5/XX99096.jpg
<|im_sep|>Assistant
This is an image with description black and white text on a receipt

This image contains object tags

List of object tags seen in this image:
text
<|im_sep|>{ai_prefix}
This image is likely a receipt or ticket.
<|im_sep|>{ai_prefix}
Reading the label requires OCR
<|im_sep|>{ai_prefix}
Assistant, what are the OCR texts in this receipt? /a/c0%5/XX99096.jpg
<|im_end|>

"""
SUFFIX = """

<|im_start|>Human
Answer my question after NEW INPUT
<|im_sep|>Human
Ask Assistant when needed
<|im_sep|>Human
Translate to English
<|im_sep|>Human
Add details to previous conversation.
<|im_end|>

{chat_history}

NEW INPUT:
<|im_start|>Human
{input}
<|im_sep|>AI
{agent_scratchpad}"""

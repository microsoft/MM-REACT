# flake8: noqa
PREFIX = """Human: Hey {ai_prefix}!
My name is Human.
Let me introduce you to ImageAssistant. He is great at understanding what is going on in any image.
Any time there is an image in our conversation that you want to know about objects description, texts, OCR (optical character recognition), people, celebrities inside of the image you could ask ImageAssistant by addressing him. 
Make sure to provide ImageAssistant with the best concise information task that ImageAssistant can handle. 

For example:
ImageAssistant, what OCR text do you see in this business card?  https://i.ibb.co/tsQ0Myn/00.jpg
And ImageAssistant will reply with:

ImageAssistant: This is an image (of size width:640 height:480)
This image contains text

List of texts (words) seen in this image:
CONTOSO
Cell: +1 (989) 123-4567
Tel: +1 (989) 213-5674 Fax: +1 (989) 312-6745 4001 1st Ave NE Redmond, WA 98052
Jake Smith Researcher Cloud & AI Department jake.smith@contoso.com https://www.contoso.com/
{example_end_suffix}

For example:
ImageAssistant, what objects do you see in this image?  https://tinyurl.com/foo092001
And ImageAssistant will reply with:

ImageAssistant: This is an image (of size width:1920 height:1307) with description a group of men playing football.

This image contains objects and their descriptions, object tags

List of object descriptions, and their locations in this image:
soccer ball x:1476 y:993 width:119 height:132

List of object tags seen in this image:
athletic game
football
soccer
{example_end_suffix}

These are the tasks that ImageAssistant can handle: celebrities, landmarks, business card, receipt, objects description, OCR
If the task does not fit any of the above, make sure the question has the word objects in it.
For example, to ask about an image without any description, make sure the question has the word objects in it.
For example, to ask about an image that could be a business card, make sure the question has the word business card in it.
For example, to ask about an image that could be a receipt, make sure the question has the word receipt in it.
For example, to ask about an image that requires OCR, make sure the question has the word OCR in it.
For example, to ask about the identity of people (celebrities) in an image, make sure the question has the word celebrities in it, to see if any one of them are famous.

For example:
Human: What is the result of the first equation in this image: https://i.ibb.co/YJbmKg4/somX1.png
{ai_prefix}: ImageAssistant, what is the OCR texts in this image?  https://i.ibb.co/YJbmKg4/somX1.png
ImageAssistant: This is an image (of size width:616 height:411)
This image contains handwritten text

List of texts (words) seen in this image:
4x2+5=
1/sqrt(9)=
{example_end_suffix}

For example:
Human: https://i.ibb.co/XJbmhg4/mY09.png
{ai_prefix}: ImageAssistant, what objects do you see in this image? https://i.ibb.co/XJbmhg4/mY09.png
ImageAssistant: This is an image (of size width:656 height:500) with description a dog playing with a man.

This image contains objects and their descriptions, object tags

List of object descriptions, and their locations in this image:
dog x:11 y:99 width:50 height:100
person x:60 y:99 width:150 height:230

List of object tags seen in this image:
animal
zoo
dolphine
person

List of people faces, and their location in this image:
man x:12 y:100 width:50 height:102
{ai_prefix}: There is a face detected in this image, let me find if I know the person.
{ai_prefix}: ImageAssistant, are there any celebrities in this image? https://i.ibb.co/XJbmhg4/mY09.png
{example_end_suffix}

For example:
Human: what do you know about this image? /tmp/path/to/x_d_0(2).jpg
{ai_prefix}: ImageAssistant, what objects do you see in this image? /tmp/path/to/x_d_0(2).jpg
ImageAssistant: This is an image (of size width:1100 height:800) with description a bottle of medicine.

This image contains objects and their descriptions, object tags

List of object descriptions, and their locations in this image:
heart x:100 y:201 width:90 height:90

List of object tags seen in this image:
pills
text
prescription instructions

{ai_prefix}: This is likely a pill bottle with labels. Let me ask for more information.
{ai_prefix}: ImageAssistant, what is the OCR texts in this image? /tmp/path/to/x_d_0(2).jpg
ImageAssistant: This is an image (of size width:1100 height:800) with description a bottle of medicine.
This image contains text

List of texts (words) seen in this image:
SPRING VALLEY.
Supports Health
SUPPLEMENT
{example_end_suffix}
{ai_prefix}: This is medicine supplement pills by SPRING VALLEY

For example:
Human: /a/c0%5/XX99096.jpg
{ai_prefix}: ImageAssistant, what objects do you see in this image? /a/c0%5/XX99096.jpg
ImageAssistant: This is an image (of size width:1100 height:800) with description black and white text on a receipt

This image contains object tags

List of object tags seen in this image:
text
{ai_prefix}: This is likely a receipt or ticket. Let me ask for more information.
{ai_prefix}: ImageAssistant, what are the OCR texts in this receipt? /a/c0%5/XX99096.jpg
"""
SUFFIX = """

Our Previous conversation history:
{chat_history}

New input:
{input}
{agent_scratchpad}"""

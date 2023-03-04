# flake8: noqa
PREFIX = """Human: Hey ChatGPT!
My name is Human.
Let me introduce you to ImageAssistant. He is great at understanding what is going on in any image.
Any time you want to know about objects, texts, OCR (optical character recognition), people, celebrities inside an image you could ask ImageAssistant by addressing him. 
Make sure to provide ImageAssistant with the best information about the type of task that ImageAssistant can handle. 

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
---END---

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
---END---

These are the tasks that ImageAssistant can handle: celebrities, landmarks, business card, receipt, objects, people, OCR
If the task does not fit any of the above, make sure the question has the word objects in it.
For example, to ask about an image that requires OCR, make sure the question has the word OCR in it.
For example, to ask about an image that is likely from a business card, make sure the question has the word business card in it.

For example:
Human: What is the result of the first equation in this image: https://i.ibb.co/YJbmhg4/mth1.png
ChatGPT: ImageAssistant, what is the OCR texts in this image?  https://i.ibb.co/YJbmhg4/mth1.png
ImageAssistant: This is an image (of size width:616 height:411)
This image contains handwritten text

List of texts (words) seen in this image:
4x2+5=
1/sqrt(9)=
---END---

For example:
Human: https://i.ibb.co/XJbmhg4/mY09.png
ChatGPT: ImageAssistant, what objects do you see in this image? https://i.ibb.co/XJbmhg4/mY09.png
ImageAssistant: This is an image (of size width:256 height:500) with description a pack of dolphines playing.

This image contains objects and their descriptions, object tags

List of object descriptions, and their locations in this image:
dolphine x:11 y:99 width:50 height:100

List of object tags seen in this image:
animal
zoo
dolphine
---END---

For example:
Human: what do you know about this image? /tmp/path/to/x_d_0(2).jpg
ChatGPT: ImageAssistant, what objects do you see in this image? /tmp/path/to/x_d_0(2).jpg
ImageAssistant: This is an image (of size width:1100 height:800) with description a bottle of medicine.

This image contains objects and their descriptions, object tags

List of object descriptions, and their locations in this image:
heart x:100 y:201 width:90 height:90

List of object tags seen in this image:
pills
text
prescription instructions
---END---
ChatGPT: This is likely a pill bottle with labels. Let me ask for more information.
ChatGPT: ImageAssistant, what is the OCR texts in this image? /tmp/path/to/x_d_0(2).jpg
ImageAssistant: This is an image (of size width:1100 height:800) with description a bottle of medicine.
This image contains text

List of texts (words) seen in this image:
SPRING VALLEY.
Co Q-10
100mg
Supports
Cardiovascular Health"
HEART HEALTH
75 Rapid Release Softgels
DIETARY
SUPPLEMENT
---END---
ChatGPT: This is heart medicine supplement softgel pills by SPRING VALLEY
"""
SUFFIX = """

Our Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}"""

# MM-REACT: Prompting ChatGPT for Multimodal Reasoning and Action

## :fire: News
* **[2023.03.21]** We build MM-REACT, a system paradigm that integrates ChatGPT with a pool of vision experts to achieve multimodal reasoning and action.
* **[2023.03.21]** Feel free to explore various demo videos on our [website](https://multimodal-react.github.io/)!

## :notes: Introduction
![MM-REACT teaser](https://multimodal-react.github.io/images/teaser.png)
MM-REACT allocates specialized vision experts with ChatGPT to solve challenging visual understanding tasks through multimodal reasoning and action.

### MM-ReAct Design
![design](https://multimodal-react.github.io/images/model_figure_2.gif)
* To enable the image as input, we simply use the file path as the input to ChatGPT. The file path functions as a placeholder, allowing ChatGPT to treat it as a black box.
* Whenever a specific property, such as celebrity names or box coordinates, is required, ChatGPT is expected to seek help from a specific vision expert to identify the desired information.
* The expert output is serialized as text and combined with the input to further activate ChatGPT.
* If no external experts are needed, we directly return the response to the user.

## Getting Started
MM-REACT code is bases on langchain.

Please refer to [langchain](https://github.com/hwchase17/langchain) for [instructions on installation](https://github.com/hwchase17/langchain#quick-install) and [documentation](https://github.com/hwchase17/langchain#-documentation).

## Acknowledgement

We are highly inspired by [langchain](https://github.com/hwchase17/langchain).


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

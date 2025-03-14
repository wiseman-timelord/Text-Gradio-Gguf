# Text-Gradio-Gguf
![banner_image](media/project_banner.jpg)
<br>Status: Alpha - Testing and bugfixing.

## Description
Intended as a high-quality chat interface with uses include, Codeing, Rpg Game, Chat, programmed towards windows 10 non-WSL, with any Cpu/Gpu on GGUF models. Dynamic modes enabling correct, interface and prompts, for relating theme of sessions, With the latest advancements, and no imposed, limitations or guidelines. This tool providing local, uncensored, and inference with features that enhance productivity and usability, even a comparable interface, found on premium AI services, or as far in that direction as, Gradio and Grok3Beta, will allow. The configuration is without options reported to make no difference on most models, ensuring a comprehensive yet streamlined experience. Capable of all things possible through simple scripts and awesome libraries and modern GGUF LLMs.

### Features
- **Operation Modes **:  "Chat" for general purpose, "Coder" for working on code, "Rpg" for customizable scenario themed interaction.
- **Comprihensive CPU/GPU Support**: CPUs x64-CPU/AVX2/AVX512 and GPUs AMD/nVIDIA/Intel, with dropdown list selection supporting multi CPU/GPU setup.
- **Research-Grade Tools**: Includes RAG, web search, chunking, summarization, TOT, no-THINK, and code formatting, and with file attachments. 
- **Virtual Environment**: Isolated Python setup in `.venv` with `models` and `data` directories.
- **Common File Support**: Handles `.bat`, `.py`, `.ps1`, `.txt`, `.json`, `.yaml`, `.psd1`, `.xaml`, and other common formats of files.
- **Configurable Context Window**: Set `n_ctx` to 8192, 16384, 24576, or 32768 via dropdown.
- **Enhanced Interface Controls**: Load/unload models, manage sessions, shutdown, and configure settings.
- **FAISS Vector Database**: Stores numerical vectors, and retrieves based on proximity in meaning, enabling pulling context from documents.
- **Highly Customizable UI**: Configurable; 10-20 Session History slots, 2-10 file slots, Session Log 400-550px height, 2-8 Lines of input. 
- **Afterthought Countdown**: If, =>10 lines then 5s or 5-10 lines then 3s or <5 lines then 1s, wait for you to cancel send and return to edit, saving on mis-prompts and waits.
- **Attach or Vectorise**: Optimally for the mode, Attach Files is complete raw input, while Vectorise Files is relevance selected snippets from potentially larger source. 

### Preview
- The "Conversation" page, with Operation/Panel Mode selector, and other features. In this case using `T.O.T.` enhancement on `Lamarckvergence-14B` (non-reasoning) model...
![preview_image](media/conversation_page.jpg)

- The "Configuration" page - for configuration of, models and hardware, and relevant components, as well as ui customization...
![preview_image](media/configuration_page.jpg)


- Wide Llama.Cpp support in the installer, thanks to latest ~128k ai systems, no longer having to streamline such things...
```
========================================================================================================================
    Text-Gradio-Gguf: Install Options
========================================================================================================================



 Select the Llama.Cpp type:

    1. AVX2 - CPU Only - Must be compatible with AVX2

    2. AVX512 - CPU Only - Must be compatible with AVX512

    3. NoAVX - CPU Only - For older CPUs without AVX support

    4. OpenBLAS - CPU Only - Optimized for linear algebra operations

    5. Vulkan - GPU/CPU - For AMD/nVidia/Intel GPU with x64 CPU

    6. Kompute - GPU/CPU - Experimental Vulkan with with CPU fallback

    7. CUDA 11.7 - GPU/CPU - For CUDA 11.7 GPUs with CPU fallback

    8. CUDA 12.4 - GPU/CPU - For CUDA 12.4 GPUs with CPU fallback



========================================================================================================================
 Selection; Menu Options = 1-8, Exit Installer = X:

```

## Requirements
- Windows 10/11 - Its a Windows program, it may be linux compatible later (not now).
- Llama.Cpp - Options here for, Avx2, Vulkan, Kompute, Cuda 11, Cuda 12.
- Python => 3.8 (tested on 3.11.0) - Libraries used = Gradio, LangChain, llama-cpp-python, FAISS.
- Llm Model - You will need a Large Language Model in GGUF format, See `Models` section.
- Suitable CPU/GPU - Gpu may be, Main or Compute, with VRam 2-64GB, testing on rx470 in Compute.  

### Instructions
1. Download a "Release" version, when its available, and unpack to a sensible directory, like, `C:\Program_Filez\Text-Gradio-Gguf` or `C:\Programs\Text-Gradio-Gguf`. 
2. Right click the file `Text-Gradio-Gguf.bat`, and `Run as Admin`, the Batch Menu will then load, then select `2` from the Batch Menu, to begin installation. You will be prompted to select a Llama.Cpp version to install, which should be done based on your hardware. After which, the install will begin, wherein Python requirements will install to a `.\venv` folder. After the install completes, check for any install issues, you may need to install again if there are.
3. You will then be returned to the Batch Menu, where you, now and in future, select `1` to run to run `Text-Gradio-Gguf`. You will then be greeted with the `Conversation` page, but you will first be going to the `Configuration` page. 
4. On the `Configuration` page you would configure appropriately, its all straight forwards, but remember to save settings and load model. If the model loads correctly it will say so in the `Status Bar` on the bottom od the display.
5. Go back to the `Conversation` page and begin interactions, ensuring to notice features available, and select appropriately for your, specific model and use cases.
6. When all is finished, click `Exit` on the bottom right and/or close browser-tabs/terminals, however you want to do it. 

### Notation
- VRAM dropdown, 1GB to 32GB in steps, this should be your FREE ram available on the selected card.
- We use an incorrect calculation of I think `1.1` currently, but the safe calculation was `TotalVRam /((ModelFileSize * 1.1875) / NumLayers = LayerSize) = NumLayersOnGpu`.
- Most GGUF text models will work, keep in mind the applicable keywords shown in `Model Label Keywords` section, for enhancement detection.
- For downloading large files such as LLM in GGUF format, then typically I would use  [DownLord](https://github.com/wiseman-timelord/DownLord), instead of lfs.

### Model label/name Keywords...
1. Keywords for Operation mode...
- `Coding` keywords - "code", "coder", "program", "dev", "copilot", "codex", "Python", "Powershell".
- `RPG Game` keywords - "nsfw", "adult", "mature", "explicit", "rp", "roleplay".
- `Chat` keywords - none of the above.
2. Keywords for Enhancements...
- `UnCensored` keywords - "uncensored", "unfiltered", "unbiased", "unlocked".
- `reasoning` keywords - "reason", "r1", "think".

# Models
You will of course need to have a `*.Gguf` model, use an iMatrix version of the same models if you have nVidia hardware. Here are some of the models used to test the program.. 
1. Fpr non-iMatrix 14B models...
- [Lamarckvergence-14B-GGUF](https://huggingface.co/mradermacher/Lamarckvergence-14B-GGUF) - Best ~14B model, beating most, ~30B and ~70B.
2. For non-iMatrix ~8B models.
- [qwen2.5-7b-cabs-v0.4-GGUF](https://huggingface.co/mradermacher/qwen2.5-7b-cabs-v0.4-GGUF) - Best <8b Model on General leaderboard, and ~500 overall.
- Doesnt work: [DeepSeek-R1-Distill-Qwen-7B-Uncensored-Reasoner-GGUF](https://huggingface.co/mradermacher/DeepSeek-R1-Distill-Qwen-7B-Uncensored-Reasoner-GGUF), some kind of non-standard tokenizer issues, needs investigating after completion.
- Llama [DeepSeek-R1-Distill-Llama-8B-Uncensored-GGUF](https://huggingface.co/mradermacher/DeepSeek-R1-Distill-Llama-8B-Uncensored-GGUF) 8GB cutdown but somewhat compitent - Uncensored <8GB non-iMatrix Rpg suitable.
- [Nxcode-CQ-7B-orpol-Gguf](https://huggingface.co/tensorblock/Nxcode-CQ-7B-orpo-GGUF) - Best on Big code Leaderboard, Instruct model specializing in Python.
- [Ninja-v1-NSFW-RP-GGUF](https://huggingface.co/mradermacher/Ninja-v1-NSFW-RP-GGUF) - Most downloaded RP NSFW on huggingface at the time.
3. For <4B non-iMatrix models.
- [Llama-3.2-3B-Instruct-uncensored-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-uncensored-GGUF) - untested.
- [DeepSeek-R1-Distill-Qwen-1.5B-uncensored-GGUF](https://huggingface.co/mradermacher/DeepSeek-R1-Distill-Qwen-1.5B-uncensored-GGUF) - Uncensored Reasoning.

## File Structure
- Core Project files...
```
project_root/
│ Text-Gradio-Gguf.bat
│ requisites.py
│ launcher.py
├── media/
│ ├── program_banner_large.jpg
│ └── program_banner_small.jpg
├── scripts/
│ └── interface.py
│ └── models.py
│ └── prompts.py
│ └── temporary.py
└── └── utlity.py
```
- Installed/Temporary files...
```
project_root/
├── data/
│ └── persistence.json
│ └── models.py
│ └── prompts.py
│ └── temporary.py
│ └── utlity.py
├── data/vectors/
└───└── *
├── data/temp/
└───└── *
├── temp/history
└───└── *
├── .venv/
└─└── *
```

## Gen 1 Development
With regards to the current version of the program...
1.  Check over prompting, prompt each mode and enhancement. Websearch, is supposed to require 2 phases of prompting, ensure it works ok, and has its own printed information in the session log. Stats on sites visited or someth, then output final response. Check Websearch prompting, it should be, 2 prompts or 1 dynamic prompt with 2 configurations, for code or chat, it should be tailored to the purpose, as in chat is for research, while in code is trying to, find out about some library or the correct method of implementing something, as possible we want simple method of enhancing for maximum effectiveness.   
5. Speech enhancement with `PyWin32`. It would generate and read the response, but we would want it to be limited in, tot and think, enhancements to only reading the answer. simlarly to the websearch, we would only want the `results` part read if it has one or maybe we need to implement someting in the second prompt to say encapulate the summary section you want read aloud with `<summary>` and `</summary`, or however thats done best. 
2. Check all enhancements.
4. Test Rpg features.

## Gen => 2 Development.
With regards to the features expected of future generations of the program...
1. Research local and online AI programs, what kinds of enhancements are common, what would be simple to implement. Someone mentioned Manu, does some kind of webscrape or internet research, producing reports.
1. Coder mode must be agentic =m requiring 2 models. 1 =>8b model for management of tasks and 1 =>8b model instruct for generation of code. Files provided in coder mode,  would NOT be in the vector database like it is in chat mode, but instead be directly and selectively sent to the code model, that thinking model would have to assess which scripts are likely relevant and produce a list and the correct instruction for each task and stage. There would also have to be the editable scrollable prefabs for each one...
```
INFORMATON:
We are working on my project ProjectName, it is a progtam written in InsertProgrammingLanguage v#.## intended to be run on InsertOperatingSystem.

STRUCTURE:
(Information about directory structure, ie core directory list)

INSTRUCTION:
(State issue with the code or what needs to be created/redacted).
(State process of investigaction and relevant information).

SECTION(s):
(Insert code snippets here)

RESOURCE(s):
(Detail things provided, remember to mention Files attached if so.)

CONSIDERATION(s):
Print complete updated function(s) for specifically the functions we are updating.
or
Print the complete updated script.
```
...something like that, this also prompts ability to change the size of the user input/session log, via some kind of draggable border that makes one larger while the other smaller, and vice versa, or if that does not exist in gradio, then maybe a slider that could be at the top of the screen, and controll linearly the proportions of each of the settings ranges for the sizes of both being the maximums and 10px or 1 line being the minimum. However its done best. So `Session Log Height` would be labeled `Max Log Height`, and `Input Lines` would become `Max Input Lines`.
1. **Safe Globals** - Standardize all global variables using safe, unique three-word labels to avoid conflicts.  
2. **Cross-Platform Scripting:** Introduce a unified script (`Text-Gradio-Gguf.sh`) to support both Linux and Windows environments, and adapt scripts appropriately.  
3. **User Interface and Notification Enhancements:**  
   - Implement verbose, clear, and concise printed notifications for all stages of model interaction (e.g., "Sending Prompt to Code Model...", "Response Received from Code Model...").  
   - Add a configuration page with a non-editable “Prompting” section showing the operation mode, enhancements (e.g., Web-Search, VectorStore), and the last prompt sent.  
   - Remove some of the Debug in terminal, selectively.
4. **Enhanced Notation Modes:**  
   - Introduce “Chat-Notate” and “Chat-Notate-Uncensored” modes to process uploaded PDFs into both detailed and concise summaries.  
   - Store summaries in `.\\data\\notation` and provide a Notation Library menu in the UI for managing these notations.  
   - Disable the THINK phase in these modes to ensure practical, notation-driven conversations.  
5. **Agentic and Enhanced Features:**  
   - Integrate vision capabilities for image recognition on web searches and convert images into contextually relevant thumbnails (with full images accessible via pop-up).  
   - Add voice processing features (Text-to-Voice and Voice-to-Text) using PyWin32 and Whisper.
   - Ensure that attached files can be written to.  
6. **Mode-Specific Integrations and Persistent Sessions:**  
   - Support various modes (Chatbot, Advanced Chatbot, Coder, Agentic Coder, RPG Text, RPG Text + Images) with tailored features as outlined in the design table.  
   - Introduce persistent modes (Chat-Persistent and RPG-Persistent) to enable ongoing sessions with stored states, allowing persistent interactions (e.g., a consistent AI character like a counsellor).  
7. **Visual Customization:** Revisit color theme design, favoring shades of grey initially, and allow users to choose a primary button color through configuration.

## Credits
- [Grok3Beta](https://x.com/i/grok) - For much of the complete updated functions that I implemented.
- [Deepseek R1/3](https://www.deepseek.com/) - For re-attempting the things Grok3Beta was having difficulty with.
- [Claude_Sonnet](https://claude.ai) - For a smaller amount of the work on this project, useually when there was issue with the other 2 above.
- [Perplexity](https://www.perplexity.ai) - For research to look at more sites than normal, also notice its agentic now.

## License
**Wiseman-Timelord's Glorified License** is detailed in the file `.\Licence.txt`, that will later be added.


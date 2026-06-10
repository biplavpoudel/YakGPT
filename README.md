---
title: YakGPT
emoji: 🦀
colorFrom: purple
colorTo: yellow
sdk: docker
sdk_version: 6.16.0
python_version: '3.12'
pinned: false
license: mit
---

*Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference*

# 🏔️ YAKGPT: Can You Survive Thorong La?

<img
  src="https://tenor.com/view/frozen-freezing-cold-shivering-glace-gif-4206910866563313498.gif"
  alt="Frozen GIF"
  class="scene-gif"
/>

**Track Submisison:** 🍄 An Adventure in Thousand Token Wood 

# 📖 Summary
**YakGPT: Can You Survive Thorong La?** is a choice-driven mountain survival and cultural respect simulator powered entirely by a small language model. Instead of a generic B2B chatbot, players step into the hiking boots of a tourist navigating high-altitude Himalayan trail of Thorong La in Annapurna Circuit.

Your guide through this perilous journey? YakGPT, the world's most sarcastic, judgmental, yet fiercely protective local trail yak. *(In its current state? Nah!!)* 🙅‍♂️

While the Yak delivers brutal, comedic roasts about your flatlander decision-making, an underlying stateful simulation rigorously tracks real-world trekking physiology: Altitude, Acclimatization, and Guide Trust. Make reckless choices to save time, and your vitals drop alongside your Sherpa's respect. Can you survive the high passes, or will you be humbled by the mountain?

# 💡 The Inspiration & Real-World Impact
Every trekking season, hundreds of tourists endanger their lives and the lives of local Sherpas and guides by ignoring altitude warning signs, rushing schedules, or disregarding indigenous mountain knowledge. Even my friends and families love to hike and trek in their free time and they don't have appropriate knowledge. Since the Nepalese are not required to make avail of guides, many chose not to to save money, making them more at risks than tourists! So I wanted to build a fun, unique game for my friends and families that teaches the players to understand the risk of travelling, to understand the signs of weather and to plan the trek accordingly.

## 🛠️ Key Features:

### The Sarcastic Narrator Engine: 
*(Still not decided how to proceed)* Powered by a quantized small open-weights model, YakGPT handles environmental narration, dynamic game forks, and localized comedic roasts with a rich, authentic Nepalese texture (tea houses, dal bhat power, suspension bridge protocols).

### Stateful Telemetry Dashboard:
*(Needs refining)* A tailored Gradio UI that replaces standard chat inputs with an interactive survival dashboard. Track hidden and visible stats in real-time, including Oxygen Levels, Altitude (m), and Guide Trust.

### The Unforgiving Mountain Simulator:
*(blah, blah, blah)* 😴 The text adventure handles physiological consequences realistically. Skipping acclimatization days will trigger simulated Acute Mountain Sickness (AMS), and losing your guide's trust will cut you off from life-saving advice when blizzards hit.

### The Guide's Private Journal:
*(Currently a basic journal system)* A hidden log feature allowing players to see exactly what their local guide secretly thinks of their behavioral choices.

## 🧬 Technical Stack & Constraints
  
### Model:
Lightweight open-weights model, Llama-3.1-128k-Dark-Planet-Uncensored-8B-GGUF, optimized for text-generation and running entirely within the resource budget.  

### UI Framework:
Crafted with Gradio gr.Blocks for a custom, grid-based layout that breaks away from traditional conversational AI patterns.

---


### For using models locally in llama.cpp:
Follow this guide to download and install Nvidia dependencies like **CUDA Toolkit**: https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#cuda

We build **llama.cpp** from scratch to enable CUDA Acceleration. 

We can configure CMake to generate build instructions in **Ninja** instead of Makefiles (makes build a hella lot faster!). And then we build with parallelism (12 cores in my case!):
```
cmake -B build -G Ninja -DGGML_CUDA=ON
cmake --build build -j12
```
Then for actual testing, I am using **Llama-3.1-128k-Dark-Planet-Uncensored-8B-GGUF** (renamed here) from Huggingface: https://huggingface.co/DavidAU/Llama-3.1-128k-Dark-Planet-Uncensored-8B-GGUF, which is a **Llama 3.1** model with an **8B parameters** architecture, a maximum context window of **128k tokens**, and is quantized to **4-bits** using the **Q4_K_M** method.
```
./build/bin/llama-cli -m  ~/dark-planet-8b.gguf -ngl 32 -p "Hello, explain cuda offloading"
```

### For audio-based model
The narration is done using **Kokoro-82M** model, which is executed locally via the **ONNX Runtime** (`kokoro-onnx`).

Installation instruction can be found here: https://github.com/nazdridoy/kokoro-tts/

Currently, the voice being used is `bm_george`, a British Male voice profile. The model runs completely on CPU using **CPU Execution Provider** (`CPUExecutionProvider`).
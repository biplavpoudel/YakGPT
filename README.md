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
Lightweight open-weights model () (≤ 8B parameters; not finalized!!) optimized for text-generation and running entirely within the resource budget.  

### UI Framework:
Crafted with Gradio gr.Blocks for a custom, grid-based layout that breaks away from traditional conversational AI patterns.

---
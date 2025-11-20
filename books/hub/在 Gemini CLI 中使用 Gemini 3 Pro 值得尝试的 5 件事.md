

- 来源：[5 things to try with Gemini 3 Pro in Gemini CLI](https://developers.googleblog.com/en/5-things-to-try-with-gemini-3-pro-in-gemini-cli/)
- 本文为原文的直接翻译，翻译过程在AI Studio中完成，使用了Google最新发布的Gemini 3 pro。
- 日期：2025年11月18日

![GeminiCLI_BlogHeader_02](https://storage.googleapis.com/gweb-developer-goog-blog-assets/images/GeminiCLI_BlogHeader_02.original.png)

**Gemini 3 Pro 现已在 Gemini CLI 中可用**

我们已将我们最智能的模型 [**Gemini 3 Pro**](https://blog.google/products/gemini/gemini-3) 直接集成到 Gemini CLI 中，以在终端中解锁更高水平的性能和生产力。这种强大的组合提供了顶尖的推理能力，用于执行更好的命令，通过代理编码（agentic coding）增强了对复杂工程工作的支持，并通过先进的工具使用实现了更智能、更定制化的工作流。

我们正在逐步开放访问权限，以确保体验快速且可靠。

- **Google AI Ultra** 订阅用户（Google AI Ultra 商业版访问权限已在规划中）以及通过付费 **Gemini API key** 访问的用户，即刻起可在 Gemini CLI 中使用 Gemini 3 Pro。
- 对于 **Gemini Code Assist Enterprise** 用户，访问权限即将推出。
- **所有其他用户**，包括 Google AI Pro、Gemini Code Assist Standard 和免费层级用户，可以加入[候补名单](https://forms.gle/ospXWr8SRTg73eBA8)，以便在[功能开放时获得访问权限](https://goo.gle/enable-preview-features)。

您还可以通过关注此 [GitHub 讨论](https://goo.gle/geminicli-waitlist-status)来跟踪我们的推广进度。

## 在 Gemini CLI 中开始使用 Gemini 3 Pro

如果您是 Google AI Ultra 订阅用户或拥有付费的 Gemini API key，请通过将您的 Gemini CLI 版本升级到 **0.16.x** 来立即开始使用：

```shell
npm install -g @google/gemini-cli@latest
```

确认版本后，运行 `/settings`，然后将 **Preview features**（预览功能）切换为 **true**。Gemini CLI 现在将默认使用 Gemini 3 Pro。


<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/Intro._Enable_Gemini_3_in_Gemini_CLI.mp4" style="max-width: 100%; height: auto;">
</video>

*用户可以按照此视频中的说明学习如何在 Gemini CLI 中启用 Gemini 3 Pro*

以下是您可以在 Gemini CLI 中利用 Gemini 3 Pro 来加速开发并将最宏大的想法变为现实的 5 种实用方法。

## 通过改进的代理编码在终端中构建任何东西

Gemini 3 Pro 在编码方面表现出色，因为它能够综合包括文本、图像和代码在内的零散信息，并遵循复杂、富有创意的指令。它能理解您想法背后的意图，让您一步就能从粗略的概念转变为功能性的起点。

1. **生成一个可即时部署的 3D 图形应用程序**

Gemini 3 Pro 的代理编码能力使其能够处理既是创意简报又是技术规范的提示词。它可以接收一个提示词，创建一个详细的执行计划，然后为一个可运行的 Web 项目生成整个脚手架，而不仅仅是单个文件。

例如，假设您有一个制作视觉效果令人印象深刻的原型的想法——比如用于着陆页的 3D 图形或快速技术演示。与其花费数小时设置图形库和本地开发服务器，不如一次性描述整个项目，并立即获得一个可工作的起点。

```shell
Objective: Build a visually stunning, photorealistic 3D Voxel simulation of the Golden Gate Bridge using Three.js, prioritizing quality and complex visuals (no simple blocks),  atmospheric depth and 60FPS performance.

Visuals & Atmosphere:
- Lighting: Slider (0-24h) controlling sun position, light intensity, sky color, and fog color.
- Fog: Volumetric-style fog using sprite particles that drift and bob. Slider 0-100. 0 = True Zero (Crystal Clear). 100 = Dense but realistic (not whiteout).
- Water: Custom GLSL shader with waves, specular reflections, and manual distance-based fog blending (exp2) for seamless horizon integration.
- Post-Processing: ACESFilmic Tone Mapping and UnrealBloom (optimized for glowing lights at night).

Scene Details:
- Bridge: Art Deco towers with concrete piers (anchored to seabed), main span catenary cables, and suspenders.
- Terrain: Low-poly Marin Headlands and SF Peninsula.
- Skyline: Procedural city blocks on the SF side.
- Traffic: Up to 400 cars using \`InstancedMesh\`, positioned accurately on top of the deck (ensure vertical alignment prevents clipping into the concrete). Each car features emissive headlights (white) and taillights (red).
- Ships: Procedural cargo ships with hull, containers, and functional navigation lights (Port/Starboard/Mast/Cabin) moving along the water.
- Nature: Animated flocking birds.
- Night Mode: At night, activate city lights, car headlights, ship navigation lights, tower beacons, street lights.

Tech & Controls:
- Core: Must output only single HTML file \`golden_gate_bridge.html\` to be run in a blank Chrome tab. Import Three.js/Addons via CDN map.
  -   \`three\` (Core library) via CDN (ES Modules).
  -   \`three/examples/jsm/...\` modules via Import Map.
  -   No build step (Vite/Webpack). Pure HTML/JS.

- UI: Visually appealing sliders for Time (0-24h), Fog Density (0-100%), Traffic Density (0-100%), and Camera Zoom.
- Optimization: \`InstancedMesh\` for all repetitive elements (cars, lights, birds).


目标： 使用 Three.js 构建一个视觉效果惊艳、照片级真实的金门大桥 3D 体素（Voxel）模拟。优先考虑画质和复杂的视觉效果（不要简单的方块），以及大气纵深感和 60FPS 的性能表现。
视觉与氛围：
光照： 滑块（0-24小时）控制太阳位置、光照强度、天空颜色和雾气颜色。
雾气： 使用漂浮和摆动的精灵粒子（sprite particles）制作体积雾。滑块 0-100。0 = 绝对零度（清晰透明）。100 = 浓密但真实（不是全白）。
水面： 自定义 GLSL 着色器，带有波浪、镜面反射和基于距离的手动雾气混合（exp2），以实现无缝的地平线融合。
后期处理： ACESFilmic 色调映射和 UnrealBloom（针对夜间发光灯光进行了优化）。
场景细节：
桥梁： 带有混凝土桥墩（锚定在海底）、主跨悬链线和吊索的装饰艺术风格塔楼。
地形： 低多边形的马林岬角（Marin Headlands）和旧金山半岛。
天际线： 旧金山一侧的程序化城市街区。
交通： 使用 InstancedMesh 生成多达 400 辆汽车，准确放置在桥面上（确保垂直对齐，防止穿模进入混凝土）。每辆车都有自发光的前灯（白色）和尾灯（红色）。
船只： 带有船体、集装箱和功能性航行灯（左舷/右舷/桅杆/船舱）的程序化货船沿水面移动。
自然： 动画化的鸟群。
夜间模式： 在夜间，激活城市灯光、汽车前灯、船只航行灯、塔楼信标和路灯。
技术与控制：
核心： 必须仅输出单个 HTML 文件 golden_gate_bridge.html，以便在空白 Chrome 标签页中运行。通过 CDN map 导入 Three.js/插件。
通过 CDN (ES Modules) 导入 three (核心库)。
通过 Import Map 导入 three/examples/jsm/... 模块。
无构建步骤 (Vite/Webpack)。纯 HTML/JS。
UI： 视觉美观的滑块，用于控制时间（0-24小时）、雾气密度（0-100%）、交通密度（0-100%）和摄像机缩放。
优化： 对所有重复元素（汽车、灯光、鸟类）使用 InstancedMesh。
```
*(注：以上为生成金门大桥 3D 模拟的详细提示词)*


<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/Demo_1_of_5._Gemini_CLI_-_Golden_Gate_Simulation_disclaimer.mp4" style="max-width: 100%; height: auto;">
</video>

**2. 将视觉创意转化为可工作的应用程序**

您已经草绘了一个 UI，需要将该视觉概念转化为功能性代码。您可以拍下草图，然后简单地将图像文件拖放到终端中。

Gemini 3 Pro 的多模态理解能力将分析图纸，识别按钮、文本框和布局。然后它会生成 HTML、CSS 和 JavaScript 代码，让您的草图变为现实。

```shell
Create a UI for "Project Constellation," an internal brand intelligence tool prototype that shows a customer acquisition pipeline. The aesthetic is an ultra-creative, futuristic dark-mode nebula. Luminous, iridescent threads representing customer journeys weave through semi-transparent glass pillars. A sleek, floating data card with Tailwind CSS precision materializes when hovering over a pillar. I've prepared a sketch for you to work from: @sketch.png.

为“星座计划（Project Constellation）”创建一个 UI，这是一个展示获客渠道的内部品牌情报工具原型。其审美风格是极具创意的、未来主义的暗黑模式星云风格。代表客户旅程的发光、彩虹色丝线穿梭于半透明的玻璃柱之间。当鼠标悬停在柱子上时，一张具有 Tailwind CSS 精度的时尚浮动数据卡片将会显现。我已经为你准备了一张草图作为参考：@sketch.png。

```
*(注：以上为根据草图生成“Project Constellation” UI 的提示词)*

<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/REVISED-_Demo_2a_of_5-_Project_Constellation.mp4" style="max-width: 100%; height: auto;">
</video>

## 改善您的日常工作

虽然“氛围编码”（vibe coding）演示展示了可能性的艺术，但对开发者工具的真正考验在于它如何执行您每天多次进行的实际日常工作。在这些常见工作流（如重构代码、调试错误或管理基础设施）中的微小改进，才是创造真正生产力收益的关键。

这正是 Gemini 3 Pro 顶尖推理能力产生切实影响的地方。它能比以往更精确地遵循复杂、多部分命令的细微差别，这对于定义您日常工作的实际、细节性任务至关重要。

以下是 Gemini 3 Pro 如何处理这些关键工程任务的几个示例。

**3. 使用自然语言生成复杂的 Shell 命令**

有了 Gemini CLI，您可以直接通过自然语言使用 UNIX命令行的强大功能。无需背诵晦涩的语法和 UNIX 命令的每一个标志，只需让 Gemini 3 Pro 翻译您的意图并为您执行即可。Gemini 甚至可以为您将密集的格式化输出解析回自然语言。

让 Gemini CLI 在命令行上为您处理运行 Git Bisect 的所有复杂性，让您可以专注于运用判断力来查找问题中的 bug。

```shell
At some point I lost the commit that set my default theme to dark. 
Find it for me with git bisect and return the hash to me.

之前某个时候，我弄丢了将默认主题设置为暗色模式的那个提交（commit）。
请用 git bisect 帮我找到它，并将哈希值（hash）返回给我。


```
*(注：以上为请求使用 git bisect 查找丢失 commit 的提示词)*

<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/Demo_3_of_5._Git_bisect.mp4" style="max-width: 100%; height: auto;">
</video>

**4. 从您的代码生成准确的文档**

Gemini 3 Pro 先进的推理能力使其能够阅读和理解代码库的逻辑。它不仅仅看到语法；它可以调查并综合函数的用途，识别其参数和返回值，并将复杂的逻辑转化为清晰、人类可读的语言。

当您引入了一个复杂的应用程序并且现在需要创建文档时，这非常有用。与其手动写出描述，不如让 Gemini 分析代码并以与代码一致的格式为您生成文档。

```shell
"This is an application that does not have any documentation and we do not have a technical writer. Before you begin, review all of the code. Then make me a user documentation. This document should only explain user facing features, but make sure to explain every single feature such as usage of the app, command line options, authentication options, built in tools, and all other user facing features. For certain features such as MCP or extensions, also explain the topic and concept so that the user has a better understanding. Since this is an open source project, provide an architectural overview of how the code is laid out, a summary of each component, and how they can contribute to the open-source project. The document should be organized and formatted so that it is easy to read and find. Do not make it a single html page. Make sure to add a search feature."

这是一个没有任何文档的应用程序，而且我们没有技术文档撰写人员。在你开始之前，请审查所有的代码。然后为我制作一份用户文档。这份文档应该只解释面向用户的功能，但务必解释每一个功能，例如应用程序的用法、命令行选项、身份验证选项、内置工具以及所有其他面向用户的功能。对于某些特定功能（如 MCP 或扩展），还请解释其主题和概念，以便用户能有更好的理解。由于这是一个开源项目，请提供代码布局的架构概览、每个组件的摘要，以及如何为这个开源项目做出贡献。文档的组织和格式应易于阅读和查找。不要把它做成单页 HTML。请务必添加搜索功能。

```
*(注：以上为请求根据代码生成详细用户文档的提示词)*


<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/Demo_4_of_5._Gemini_CLI_-_Generate_Docs_From_Code.mp4" style="max-width: 100%; height: auto;">
</video>

**5. 调试实时 Cloud Run 服务中的性能问题**

Gemini 3 Pro 可以跨越掌握您团队上下文的不同服务来编排复杂的工作流。改进的工具使用能力意味着它可以规划和执行多步骤任务，这些任务需要从多个来源（如可观测性、安全性和源代码控制）收集信息，以解决单个问题。

在这个例子中，它使用 Gemini CLI 扩展将无服务器平台 (Cloud Run) 与流行的安全扫描器 (Snyk) 连接起来，以查找根本原因并建议修复方案，然后部署修复，将复杂的多工具调查转变为单一、流畅的操作。

```shell
Users are reporting that the "Save Changes" button is slow, investigate the 'tech-stack' service

用户报告称“保存更改”按钮响应缓慢，请调查 'tech-stack' 服务。

```
*(注：以上为请求调查 'tech-stack' 服务性能问题的提示词)*


<video controls src="https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/Demo_5_of_5._Gemini_CLI_-_debug.mp4" style="max-width: 100%; height: auto;">
</video>

这些例子仅仅是个开始。真正的潜力不在于运行这些特定的命令，而在于 Gemini 3 Pro 如何适应您独特的挑战——无论是优化日常 Shell 命令、处理实质性的工程工作，还是构建针对您团队工具的个性化工作流。Gemini 3 Pro 将命令行转变为理解您背景的智能合作伙伴。

看到差异的最好方法是亲自尝试。访问 [Gemini CLI 网站](https://geminicli.com/)，并在社交媒体上使用 #GeminiCLI 分享您自己的例子。我们迫不及待地想看看您构建了什么。
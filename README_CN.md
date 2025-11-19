# reader 3

![reader3](reader3.png)

一个轻量级、可自托管的 EPUB 阅读器，让你能够逐章阅读 EPUB 电子书。这使得将章节内容复制粘贴到 LLM（大语言模型）以进行辅助阅读变得非常容易。简单来说 —— 获取 epub 电子书（例如 [Project Gutenberg](https://www.gutenberg.org/) 有很多），在这个阅读器中打开它们，将文本复制粘贴到你喜欢的 LLM 中，然后一起阅读。

这个项目 90% 都是“凭感觉写代码”（vibe coded），只是为了演示如何非常容易地 [与 LLM 一起读书](https://x.com/karpathy/status/1990577951671509438)。我不会以任何方式支持它，它按原样提供以供他人寻找灵感，我不打算改进它。代码现在是短暂的，库也结束了，让你的 LLM 按你喜欢的方式随意修改它吧。

## 使用方法

本项目使用 [uv](https://docs.astral.sh/uv/)。例如，下载 [Dracula EPUB3](https://www.gutenberg.org/ebooks/345) 到此目录并保存为 `dracula.epub`，然后运行：

```bash
uv run reader3.py dracula.epub
```

这将创建目录 `dracula_data`，它将把书注册到你的本地图书馆。然后我们可以运行服务器：

```bash
uv run server.py
```

接着访问 [localhost:8123](http://localhost:8123/) 查看你当前的图书馆。你可以轻松添加更多书籍，或者通过删除文件夹从你的图书馆中删除它们。它本就不该复杂或繁琐。

## 许可证

MIT

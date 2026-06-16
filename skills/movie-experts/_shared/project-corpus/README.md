# Project Corpus Index — 100+本影视剪辑书

**Source Project:** `/home/kai/Downloads/100+本影视剪辑书/`
**Total Books:** 102 (MinerU-converted markdown, ~9.7M Chinese characters)
**Conversion Date:** 2026-06-16
**License:** User-licensed for personal/research use; per-ref fair-use excerpts only when quoting.

---

## What this corpus is

A 102-book film production library covering:
- **剧本**（Screenwriting）：经典理论（菲尔德/麦基/西格）+ 中国实战（芦苇/刘天赐）+ 短片/微电影
- **分镜/导演**（Pre-viz & Directing）：场面调度、镜头语法、拉片法
- **拍摄**（Production）：照明器材、第五代摄影、迪士尼动画、特技模型
- **后期**（Post-production）：默奇剪辑、音效圣经、纪录片方法
- **制片**（Producing）：好莱坞体系、低成本制作、创意制片
- **理论批评**（Theory & Criticism）：巴赞/塔可夫斯基、形式 vs 写实、精神分析、戴锦华批评

This corpus is the source for all `references/project-*.md` files in the movie-experts suite.

---

## How to use this corpus in RAG

Each `references/project-*.md` file in expert directories cites specific books from this corpus. The format:

```markdown
**Source:** <Book title> (Project ID: <编号>)
**Copyright:** Fair Use — paraphrased concepts + page-references; no verbatim excerpts > 200 chars.
**Last-verified:** 2026-06
verified_date: 2026-06
**Conversion path:** `/home/kai/Downloads/100+本影视剪辑书/converted/<book>/auto/<book>.md`
```

For RAG retrieval:
```
tags="expert:<expert_id>,domain:project-corpus"
tags="expert:<expert_id>,source-book:<book-id>"
```

---

## 102-Book Index by Category

### 剧本（Screenwriting）— 15 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -017 | 电影剧本写作基础 | 悉德·菲尔德 | 三幕结构 / 情节点 |
| -015 | 电影剧本的结构 | — | 莎士比亚与电影剧本 |
| -026 | 故事 | 麦基 | 故事三角 / 价值转变 |
| 073 | 编剧点金术 | 琳达·西格 | 次要情节 / 主题深化 |
| 069 | 剧本结构设计 | 丹·奥班农 | 动态结构 / 不归点 |
| 065 | 编剧的策略 | — | 钩子理论 |
| 009 | 21天搞定电影剧本 | 维基·金 | 9 分钟电影路标 |
| -006 | 编剧秘笈 | 刘天赐 | 主题的"机灵性" |
| -036 | 拉片子 | — | 热/冷开场 |
| -002 | 作为文学的电影剧本 | 温斯顿 | 电影文法 / 镜头调子 |
| 066 | 短片的法则 | — | 短片行动指南 |
| 051 | 微电影剧作教程 | — | 微电影剧本 |
| -004 | 安东尼奥尼和无情节剧本 | — | 无情节剧本 |
| -055 | 戏剧与电影的剧作理论与技巧 | 劳逊 | 戏剧史理论 |
| 073-shifty | 电影剧本-shifty | — | 完整剧本样本 |

### 分镜/导演（Pre-Viz & Directing）— 12 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -025 / 037 | 电影语言的语法 | 丹尼艾尔·阿里洪 | 平行剪辑 / 三种类型 |
| 012 | 场面调度：影像的运动 | 文森特·罗布鲁托 | 镜头运动 |
| 006 | 电影镜头设计 | 史蒂文·卡茨 | 影像化过程 |
| 015 | 电影镜头入门 | — | 镜头基础 |
| 043 | 镜头的语法 | — | 视觉语言语法 |
| -035 | 电影化叙事100手法 | Jennifer van Sijll | 电影化手法 |
| 014 | 拆解好电影 | — | 场景赏析 |
| -008 | 导演功课 | 大卫·马梅 | 说故事 / 镜头 |
| -009 | 导演学概论 | — | 舞台节奏 |
| -033 | 电影导演基础 | 库里肖夫 | 导演基础 |
| -034 | 电影的戏剧艺术 | — | 摄影机眼睛 |
| 053 | 导演创作完全手册 | — | 导演手册 |

### 拍摄/摄影/美术（Production & Cinematography）— 18 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -063 | 影视光线艺术 | 刘永泗 | 物像/视像/影像/画像 |
| 044 | 电影照明器材与操作 | — | 钨丝卤素/金属卤素 |
| 076 | 光影创作课 | — | 21 位摄影大师 |
| -027 | 光影大师 | — | 阿尔曼德罗斯等访谈 |
| 050 | 导演的摄影课 | — | 罗杰·迪金斯等访谈 |
| 007 | 镜头在说话 | 第五代摄影师 | 色彩画中画 / 平面蒙太奇 |
| -039 | 认识电影 | 贾内梯 | 现实主义 vs 形式主义 |
| -031 | 解读电影 | — | 电影欣赏 |
| -037 | 拍电影：现代影像制作教程 | — | 全流程 |
| -029 | 电影制片手册 | — | 制片步骤 |
| 061 | 电影特技模型制作 | — | 模型分类 |
| — | 狼图腾：视觉设计与叙事语言 | — | 美术指导全流程 |
| — | 迪士尼的艺术 | 克里斯托弗·芬奇 | 早期事业/动画长片/实景/魔幻王国 |
| -062 | 影视动画经典剧本赏析 | — | 花木兰改编 |
| -061 | 英国影视制作基础教程 | — | 从短片起步 |
| -058 | 演员的自我修养 | 斯坦尼 | 假使/规定情境 |
| 062 | 表演的艺术 | 斯特拉·阿德勒 | 22 堂课 |
| 048 | 尊重表演艺术 | 乌塔·哈根 | 11 个目标训练 |

### 后期/剪辑/声音（Post-Production）— 12 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -010 | 电影电视剪辑学 | 傅正义 | 剪辑基础 |
| 071 | 剪辑之道 | 奥班农对话默奇 | 谦卑的声音 |
| — | 魅力·剪辑 | — | 24 格里的门道 |
| 032 | 音效圣经 | — | 5 大分类 / 录音十诫 |
| 060 | 视听：幻觉的构建 | 米歇尔·希翁 | 声音流逻辑 |
| 049 | 纪录片创作六讲 | 王竞 | 电影眼睛 / 观点 |
| 068 | 民族志纪录片创作 | — | 参与观察 / 田野访谈 |

### 制片（Producing）— 8 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| 070 | 创意制片完全手册 | — | 项目策划 / 改编版权 |
| 057 | 好莱坞模式 | — | 迪士尼五大部门 |
| 074 | 影视预算手册 | — | 低成本制片 |
| -029 | 电影制片手册 | — | 完整流程 |

### 理论批评（Theory & Criticism）— 25 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -019 | 电影是什么 | 巴赞 | 影像本体论 / 完整电影 |
| -020 | 电影是什么（卷二） | 巴赞 | 同上（英文版） |
| -022 | 雕刻时光 | 塔可夫斯基 | 雕刻时光 / 电影影像 |
| -038 | 七部半：塔尔科夫斯基的电影世界 | — | 七部半长片+一部短片 |
| -045 | 经典电影理论导论 | 达德利·安德鲁 | 形式主义 vs 写实主义 |
| -047 | 电影理论史 | 亨·阿杰尔 | 上镜头性 / 完整电影 |
| -044 | 电影美学概述 | 阿杰尔 | 法国先锋派 |
| -048 | 电影美学 | 巴拉兹 | 可见的人类 |
| -049 | 电影实践理论 | 诺埃尔·伯奇 | 空间与时间表达 |
| -051 | 电影哲学概说 | — | 古典与现代 |
| -021 | 电影语言 | 马尔丹 | 电影画面基本特征 |
| -024 | 电影批评 | 戴锦华 | 视听语言+叙事+作者 |
| 052 | 外国电影批评文选 | 杨远婴编 | 1980-2011 跨国批评 |
| -077 | 1979-2005最有价值影评 | 戴锦华 | 大师印象/经典细读 |
| -032 | 凝视的快感 | 吴琼编 | 穆尔维/麦茨/博德里 |
| -080 | 好莱坞中的拉康 | 齐泽克 | 实在界 / 圣状 |
| -070 | 电影理论笔记 | 郭小橹 | 叙事革命 |
| -072 | 现代性的美学经验 | — | 阿多诺/本雅明 |
| -053 | 看见的世界 | 卡维尔 | 电影本体论 |
| -046 | 电影的元素 | 波布克 | 故事/影像/导演 |
| -007 | 伯格曼论电影 | 伯格曼 | 梦/梦想者 |
| -030 | 基耶斯洛夫斯基谈基耶斯洛夫斯基 | — | 偶然与宿命 |
| -013 | 法斯宾德的世界 | — | 反剧场 / 失落童年 |
| -057 | 小津安二郎的艺术 | — | 仰拍 / 相似形 |
| -054 | 我的最后一口气 | 布努埃尔 | 超现实主义 / 墨西哥 |

### 史类（Film History）— 5 books

| Project ID | Book | Author | Key Concept |
|---|---|---|---|
| -042 | 世界电影史（下） | 乔治·萨杜尔 | 国别+时期 |
| -067 | 牛津世界电影史 | 诺埃尔-史密斯编 | 主题+时期 |
| -050 | 电影史：理论与实践 | 艾伦 | 4 大史学路径 |
| -040 | 日本电影的巨匠们 | — | 日本电影 |
| 072 | 我是怎样拍电影的 | 山田洋次 | 庶民剧传统 |

### 单片研究（Single-Film Case Studies）— 7 books

| Project ID | Book | Film | Key Concept |
|---|---|---|---|
| 【白鹿原】 | 《白鹿原》芦苇电影剧本+剧本创作笔记 | 《白鹿原》 | 七易其稿 / 方言对白 |
| 【狼图腾】 | 《狼图腾：视觉设计与叙事语言》 | 《狼图腾》 | 美术指导全流程 |
| 【少年派】 | 《少年派的奇幻漂流：一部电影的诞生》 | 《少年派》 | 项目拓展 / 编剧 |
| 【蒂凡尼】 | 《清晨5点的第五大道》 | 《蒂凡尼的早餐》 | 酝酿/雏形/定局 |
| 【迪士尼】 | 《迪士尼的艺术》 | — | 米老鼠到魔幻王国 |
| 【奥特曼】 | 《不要给我讲故事》 | 奥特曼电影 | 群像 / 重叠对白 |
| -060 | 一个导演的故事 | 帕索里尼 | 短篇笔记 |

---

## Skill → Source Book Mapping

Project skill library (`/home/kai/Downloads/100+本影视剪辑书/skills-影视创作/`) has 95+ skills. Each skill cites its source book(s). The mapping is:

```python
# Pseudo-code: retrieve all books cited by a skill
def get_skill_sources(skill_path):
    with open(skill_path) as f:
        content = f.read()
    return re.findall(r'项目内\s*([-\d【】一-鿿]+)', content)
```

For RAG retrieval across the entire corpus:

```
tags="domain:project-corpus"
tags="domain:project-corpus,category:剧本"
tags="domain:project-corpus,category:理论批评"
```

---

## Maintenance

When the source project adds new books or skills:
1. Run `python /home/kai/Downloads/100+本影视剪辑书/scripts/build-index.py`
2. Re-generate this index from `converted/` directory
3. Update affected `references/project-*.md` files in expert directories
4. Bump `verified_date` in affected refs

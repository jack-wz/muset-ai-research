# 设计文档

## 概述

AI 写作助手是一个基于 LangChain DeepAgent 框架的智能写作系统，通过 Web 界面（ag-ui）为用户提供全生命周期的写作支持。系统采用模块化架构，核心由 DeepAgent 智能体提供任务规划、上下文管理和子任务委派能力，通过 MCP（模型上下文协议）实现工具扩展，集成 Claude Skills 提供专业写作能力，并通过现代化的 Web 前端提供流畅的用户体验。

系统的设计理念是将复杂的写作任务分解为可管理的步骤，利用 AI 的能力辅助而非替代人类创作，同时保持高度的可扩展性和个性化能力。

## 架构

### 整体架构

系统采用前后端分离的架构，主要包含以下层次：

```
┌─────────────────────────────────────────────────────────────┐
│                        ag-ui (前端)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  富文本编辑器  │  │   聊天界面    │  │  文件导航器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  工具栏组件   │  │  配置管理界面  │  │  项目管理器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/WebSocket
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API 网关 / 路由层                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  DeepAgent 核心 (后端)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              LangGraph 工作流引擎                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  任务规划器   │  │  文件系统管理  │  │  子智能体管理 │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  记忆管理器   │  │  技能加载器   │  │  工具调度器   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  MCP 适配器   │  │ Claude Skills │  │  LLM 提供商   │
│              │  │    加载器      │  │              │
│ ┌──────────┐ │  │ ┌──────────┐  │  │ ┌──────────┐ │
│ │学术搜索  │ │  │ │润色技能  │  │  │ │ Claude   │ │
│ │网络搜索  │ │  │ │翻译技能  │  │  │ │ GPT-4    │ │
│ │数据库    │ │  │ │风格技能  │  │  │ │ 本地模型  │ │
│ └──────────┘ │  │ └──────────┘  │  │ └──────────┘ │
└──────────────┘  └──────────────┘  └──────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      持久化存储层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  文件存储     │  │  向量数据库    │  │  关系数据库   │      │
│  │ (上下文文件)  │  │ (语义搜索)    │  │ (用户/项目)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈选择

**后端技术栈：**
- Python 3.10+
- LangChain 1.0+ (核心框架)
- LangGraph (工作流引擎)
- langchain-deepagents (DeepAgent 实现)
- langchain-mcp-adapters (MCP 集成)
- FastAPI (API 服务器)
- PostgreSQL (关系数据库)
- Redis (缓存和会话)
- Pinecone/FAISS (向量数据库)

**前端技术栈：**
- React 18+
- TypeScript 5+
- Next.js 14+ (框架)
- TipTap (富文本编辑器)
- Tailwind CSS + Emotion (样式)
- Radix UI (无样式组件)
- Zustand (状态管理)
- React Query (数据获取)

## 组件和接口

### 1. DeepAgent 核心组件

#### 1.1 任务规划器 (Task Planner)

**职责：** 将用户的写作目标分解为可执行的步骤序列

**接口：**
```python
class TaskPlanner:
    def analyze_goal(self, goal: str, context: Dict) -> WritingPlan:
        """分析写作目标并生成计划"""
        pass
    
    def create_todos(self, plan: WritingPlan) -> List[Task]:
        """使用 write_todos 工具创建任务清单"""
        pass
    
    def update_plan(self, task_id: str, new_info: Dict) -> WritingPlan:
        """根据新信息动态调整计划"""
        pass
    
    def get_next_task(self, plan: WritingPlan) -> Optional[Task]:
        """获取下一个待执行的任务"""
        pass
```

**数据结构：**
```python
@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus  # pending, in_progress, completed
    dependencies: List[str]
    estimated_duration: int
    
@dataclass
class WritingPlan:
    goal: str
    tasks: List[Task]
    current_task_id: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### 1.2 文件系统管理器 (File System Manager)

**职责：** 管理上下文文件，避免令牌限制

**接口：**
```python
class FileSystemManager:
    def write_file(self, path: str, content: str) -> bool:
        """写入文件"""
        pass
    
    def read_file(self, path: str) -> str:
        """读取文件内容"""
        pass
    
    def edit_file(self, path: str, edits: List[Edit]) -> bool:
        """批量编辑文件"""
        pass
    
    def list_files(self, directory: str) -> List[FileInfo]:
        """列出目录中的文件"""
        pass
    
    def search_files(self, pattern: str, directory: str) -> List[str]:
        """使用 grep 搜索文件内容"""
        pass
    
    def create_version(self, path: str) -> str:
        """创建文件版本快照"""
        pass
```

**文件组织结构：**
```
/workspace/{workspace_id}/
├── /drafts/
│   ├── current.md
│   ├── v1_20231119.md
│   └── v2_20231120.md
├── /references/
│   ├── research_notes.md
│   └── uploaded_doc_1.txt
├── /memories/
│   ├── /style/
│   │   └── user_style_profile.json
│   └── /glossary/
│       └── terms.json
└── /todos/
    └── current_plan.json
```

#### 1.3 子智能体管理器 (Sub-agent Manager)

**职责：** 创建和协调专业子智能体

**接口：**
```python
class SubAgentManager:
    def spawn_agent(
        self, 
        agent_type: AgentType, 
        task: Task,
        context: Dict
    ) -> SubAgent:
        """生成子智能体"""
        pass
    
    def coordinate_agents(self, agents: List[SubAgent]) -> None:
        """协调多个子智能体的执行"""
        pass
    
    def collect_results(self, agent_id: str) -> AgentResult:
        """收集子智能体的结果"""
        pass
```

**子智能体类型：**
```python
class AgentType(Enum):
    RESEARCH = "research"  # 研究智能体
    TRANSLATION = "translation"  # 翻译智能体
    EDITING = "editing"  # 编辑智能体
    FACT_CHECK = "fact_check"  # 事实核查智能体
```

#### 1.4 记忆管理器 (Memory Manager)

**职责：** 管理长期记忆和个性化数据

**接口：**
```python
class MemoryManager:
    def store_style_profile(self, user_id: str, samples: List[str]) -> StyleProfile:
        """分析并存储用户写作风格"""
        pass
    
    def load_memories(self, user_id: str, context: str) -> Dict:
        """加载相关记忆"""
        pass
    
    def store_glossary_term(self, term: str, definition: str) -> None:
        """存储术语定义"""
        pass
    
    def retrieve_similar_content(self, query: str, k: int = 5) -> List[str]:
        """使用向量搜索检索相似内容"""
        pass
```

### 2. MCP 集成组件

#### 2.1 MCP 适配器 (MCP Adapter)

**职责：** 连接和管理 MCP 服务器

**接口：**
```python
class MCPAdapter:
    def discover_servers(self, config: MCPConfig) -> List[MCPServer]:
        """发现配置的 MCP 服务器"""
        pass
    
    def connect_server(self, server: MCPServer) -> bool:
        """连接到 MCP 服务器"""
        pass
    
    def get_tools(self, server_id: str) -> List[Tool]:
        """获取服务器提供的工具"""
        pass
    
    def convert_to_langchain_tool(self, mcp_tool: MCPTool) -> LangChainTool:
        """将 MCP 工具转换为 LangChain 工具"""
        pass
```

**配置格式：**
```python
@dataclass
class MCPConfig:
    servers: Dict[str, MCPServerConfig]
    
@dataclass
class MCPServerConfig:
    command: str
    args: List[str]
    env: Dict[str, str]
    disabled: bool = False
    auto_approve: List[str] = field(default_factory=list)
```

### 3. Claude Skills 组件

#### 3.1 技能加载器 (Skill Loader)

**职责：** 加载和管理 Claude Skills

**接口：**
```python
class SkillLoader:
    def load_skill(self, skill_path: str) -> Skill:
        """加载技能包"""
        pass
    
    def parse_skill_metadata(self, skill_md: str) -> SkillMetadata:
        """解析 SKILL.md 文件"""
        pass
    
    def validate_skill(self, skill: Skill) -> ValidationResult:
        """验证技能包的安全性和完整性"""
        pass
    
    def activate_skill(self, skill_id: str, agent_context: Dict) -> None:
        """激活技能并注入指令"""
        pass
    
    def deactivate_skill(self, skill_id: str) -> None:
        """停用技能"""
        pass
```

**技能包结构：**
```
skill_package.zip
├── SKILL.md              # 技能描述和指令
├── metadata.json         # 元数据
├── /scripts/             # 可执行脚本
│   └── process.py
└── /resources/           # 资源文件
    ├── templates/
    └── dictionaries/
```

### 4. 前端组件

#### 4.1 富文本编辑器组件

**接口：**
```typescript
interface EditorProps {
  content: JSONContent;
  onChange: (content: JSONContent) => void;
  onAISuggestion: (selection: Selection) => void;
}

interface EditorAPI {
  getContent(): JSONContent;
  setContent(content: JSONContent): void;
  insertText(text: string, position?: number): void;
  applyDiff(diff: Diff): void;
  getSelection(): Selection;
}
```

#### 4.2 聊天组件

**接口：**
```typescript
interface ChatProps {
  workspaceId: string;
  onFileReference: (fileId: string) => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  fileReferences?: string[];
}

interface ChatAPI {
  sendMessage(content: string, files?: File[]): Promise<void>;
  streamResponse(onChunk: (chunk: string) => void): void;
  cancelStream(): void;
}
```

#### 4.3 配置管理组件

**接口：**
```typescript
interface ConfigManagerProps {
  onConfigChange: (config: SystemConfig) => void;
}

interface SystemConfig {
  models: ModelConfig[];
  mcpServers: MCPServerConfig[];
  skills: SkillConfig[];
}

interface ModelConfig {
  id: string;
  name: string;
  provider: 'anthropic' | 'openai' | 'local';
  apiKey?: string;
  endpoint?: string;
  parameters: Record<string, any>;
}
```

## 数据模型

### 核心数据模型

```python
# 用户模型
class User(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str]
    created_at: datetime
    settings: UserSettings

class UserSettings(BaseModel):
    default_model: str
    language: str
    theme: str
    
# 工作区模型
class Workspace(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    file_system_root: str
    
# 项目模型
class Project(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    content: JSONContent
    status: ProjectStatus
    plan: Optional[WritingPlan]
    created_at: datetime
    updated_at: datetime
    
# 会话模型
class Session(BaseModel):
    id: UUID
    project_id: UUID
    messages: List[Message]
    agent_state: Dict
    created_at: datetime
```

### 数据库 Schema

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 工作区表
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_system_root TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 项目表
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    title VARCHAR(500) NOT NULL,
    content JSONB,
    status VARCHAR(50),
    plan JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 配置表
CREATE TABLE user_configs (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    models JSONB,
    mcp_servers JSONB,
    skills JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 正确性属性

*属性是应该在系统所有有效执行中保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 验收标准可测试性预分析

#### 需求 1：任务规划与分解

1.1 分析目标并生成结构化计划
思考：这是关于所有写作目标的规则，不是特定示例。我们可以生成随机的写作目标，调用规划器，然后验证输出是否包含离散步骤的结构化计划。
可测试性：是 - 属性

1.2 使用 write_todos 工具创建任务清单
思考：这是验证系统在生成计划时是否正确使用了特定工具。我们可以监控工具调用并验证 write_todos 被调用。
可测试性：是 - 属性

1.3 跟踪进度并更新任务状态
思考：这是关于所有任务执行的规则。我们可以创建随机任务，执行它们，然后验证状态是否正确更新。
可测试性：是 - 属性

1.4 动态调整计划以纳入变化
思考：这是关于计划适应性的规则。我们可以创建计划，注入新信息，验证计划被更新。
可测试性：是 - 属性

1.5 自动进入下一步骤或提示用户
思考：这是关于任务完成后的行为规则。我们可以完成任务并验证系统的响应。
可测试性：是 - 属性

#### 需求 2：文件系统上下文管理

2.1 使用 write_file 存储上下文文件
思考：这是关于文件存储的规则。我们可以提供随机内容，验证它被正确存储为文件。
可测试性：是 - 属性

2.2 将大内容外部化到文件
思考：这是关于内容大小阈值的规则。我们可以提供不同大小的内容，验证大内容被外部化。
可测试性：是 - 属性

2.3 使用 read_file 按需检索信息
思考：这是文件读取的往返属性。我们可以写入文件然后读取，验证内容一致。
可测试性：是 - 属性（往返）

2.4 使用 edit_file 批量修改
思考：这是关于文件编辑的规则。我们可以创建文件，应用编辑，验证结果正确。
可测试性：是 - 属性

2.5 使用 ls 和 grep 搜索文件
思考：这是关于文件搜索的规则。我们可以创建文件集，搜索模式，验证找到正确的文件。
可测试性：是 - 属性

2.6 为每个版本维护单独文件
思考：这是关于版本管理的规则。我们可以创建多个版本，验证它们被独立存储。
可测试性：是 - 属性

#### 需求 3：子智能体任务委派

3.1 使用 task 工具生成子智能体
思考：这是关于子智能体创建的规则。我们可以识别专业任务，验证子智能体被生成。
可测试性：是 - 属性

3.2 为子智能体提供隔离上下文
思考：这是关于上下文隔离的规则。我们可以创建子智能体，验证其上下文不包含无关信息。
可测试性：是 - 属性

3.3 通过文件通信检索结果
思考：这是子智能体通信的往返属性。子智能体写入结果，主智能体读取，验证一致性。
可测试性：是 - 属性（往返）

3.4 协调多个子智能体执行
思考：这是关于并发控制的规则。我们可以创建多个子智能体，验证没有冲突。
可测试性：是 - 属性

3.5 委派给研究子智能体
思考：这是特定类型子智能体的示例。
可测试性：是 - 示例

#### 需求 4：长期记忆与个性化

4.1 创建 /memories/ 目录
思考：这是首次使用时的特定行为。
可测试性：是 - 示例

4.2 分析并存储风格特征
思考：这是风格分析的往返属性。存储风格，然后检索，验证一致性。
可测试性：是 - 属性（往返）

4.3 引用风格记忆匹配用户声音
思考：这是关于风格应用的规则。我们可以存储风格，生成内容，验证风格被应用。
可测试性：是 - 属性

4.4 存储术语定义
思考：这是术语存储的往返属性。
可测试性：是 - 属性（往返）

4.5 从持久存储加载记忆
思考：这是跨会话持久性的规则。我们可以存储记忆，重启会话，验证记忆被加载。
可测试性：是 - 属性

#### 需求 5：MCP 组件集成

5.1 发现可用 MCP 服务器
思考：这是关于服务器发现的规则。我们可以配置服务器，验证它们被发现。
可测试性：是 - 属性

5.2 自动转换工具格式
思考：这是工具转换的规则。我们可以提供 MCP 工具，验证转换后的 LangChain 工具功能等价。
可测试性：是 - 属性

5.3 将 MCP 工具纳入执行计划
思考：这是关于计划生成的规则。我们可以提供任务和可用工具，验证工具被包含在计划中。
可测试性：是 - 属性

5.4 使用学术数据库工具搜索引用
思考：这是特定工具使用的示例。
可测试性：是 - 示例

5.5 使用网络搜索工具收集数据
思考：这是特定工具使用的示例。
可测试性：是 - 示例

#### 需求 6：Claude 模型与技能集成

6.1 使用 Claude Sonnet 作为默认模型
思考：这是配置验证的示例。
可测试性：是 - 示例

6.2 加载相关 Claude Skills
思考：这是技能加载的规则。我们可以识别任务类型，验证相应技能被加载。
可测试性：是 - 属性

6.3 将技能指令纳入上下文
思考：这是技能激活的规则。我们可以加载技能，验证其指令出现在智能体上下文中。
可测试性：是 - 属性

6.4 激活写作润色技能
思考：这是特定技能使用的示例。
可测试性：是 - 示例

6.5 在沙箱环境中运行脚本
思考：这是安全性要求，难以直接测试沙箱隔离。
可测试性：否

#### 需求 7：富文本编辑界面

7.1 显示 TipTap 编辑区域
思考：这是 UI 渲染的示例。
可测试性：是 - 示例

7.2 支持 Markdown 和富文本
思考：这是编辑器功能的规则。我们可以输入 Markdown，验证正确渲染。
可测试性：是 - 属性

7.3 用差异可视化突出显示更改
思考：这是 UI 行为的规则。我们可以提供建议，验证差异被正确显示。
可测试性：是 - 属性

7.4 显示浮动工具栏
思考：这是 UI 交互的规则。我们可以选择文本，验证工具栏出现。
可测试性：是 - 属性

7.5 更新文档并同步后端
思考：这是数据同步的规则。我们可以应用更改，验证前后端状态一致。
可测试性：是 - 属性

#### 需求 8：对话式 AI 交互

8.1 显示对话界面
思考：这是 UI 渲染的示例。
可测试性：是 - 示例

8.2 传输消息到后端
思考：这是消息传输的规则。我们可以发送消息，验证后端接收。
可测试性：是 - 属性

8.3 显示流式响应
思考：这是流式传输的规则。我们可以生成响应，验证增量显示。
可测试性：是 - 属性

8.4 使文件引用可点击
思考：这是 UI 功能的规则。我们可以包含文件引用，验证链接可用。
可测试性：是 - 属性

8.5 用适当格式渲染内容
思考：这是内容渲染的规则。我们可以提供结构化内容，验证格式正确。
可测试性：是 - 属性

#### 需求 9-24 的分析

由于篇幅限制，其余需求的分析遵循类似模式：
- 文件操作、数据往返、状态管理等核心功能都是可测试的属性
- UI 初始渲染、特定工具使用等是示例
- 安全性、性能等非功能性需求通常不可测试或需要专门的性能测试

### 属性反思与去重

在审查所有可测试属性后，我们识别出以下冗余：

1. **文件往返属性可以合并**：需求 2.3（read_file）、4.2（风格存储）、4.4（术语存储）都是文件系统的往返属性，可以合并为一个通用的"文件往返一致性"属性。

2. **工具调用验证可以合并**：需求 1.2（write_todos）、3.1（task 工具）、5.1（MCP 工具）都是验证正确工具被调用，可以合并为"工具调度正确性"属性。

3. **状态更新属性可以合并**：需求 1.3（任务状态）、7.5（文档同步）都是关于状态一致性，可以合并为"状态同步一致性"属性。

4. **上下文管理属性可以合并**：需求 2.2（内容外部化）、3.2（上下文隔离）都是关于上下文管理，可以合并为"上下文管理正确性"属性。

经过去重，我们保留以下核心属性：

### 核心正确性属性

**属性 1：任务规划完整性**
*对于任何*写作目标，生成的计划应包含至少一个任务，且所有任务应形成有向无环图（无循环依赖）。
**验证需求：1.1, 1.2**

**属性 2：文件系统往返一致性**
*对于任何*内容，写入文件后立即读取应返回相同的内容（考虑编码和格式化）。
**验证需求：2.1, 2.3, 4.2, 4.4**

**属性 3：上下文大小管理**
*对于任何*超过阈值（如 8000 tokens）的内容，系统应将其外部化到文件而不是直接包含在提示中。
**验证需求：2.2**

**属性 4：子智能体上下文隔离**
*对于任何*子智能体，其上下文应仅包含与其任务相关的信息，不应包含主智能体的无关上下文。
**验证需求：3.2**

**属性 5：记忆持久性**
*对于任何*存储在 /memories/ 中的数据，在会话重启后应能被正确加载和检索。
**验证需求：4.5**

**属性 6：MCP 工具转换等价性**
*对于任何*MCP 工具，转换为 LangChain 工具后，其功能应与原始 MCP 工具等价（相同输入产生相同输出）。
**验证需求：5.2**

**属性 7：技能指令注入**
*对于任何*激活的技能，其 SKILL.md 中的指令应出现在智能体的系统提示中。
**验证需求：6.3**

**属性 8：编辑器内容同步**
*对于任何*在编辑器中的更改，前端状态和后端存储应在同步完成后保持一致。
**验证需求：7.5**

**属性 9：流式响应完整性**
*对于任何*流式响应，所有接收到的块拼接后应等于完整的响应内容。
**验证需求：8.3, 16.1**

**属性 10：版本历史可恢复性**
*对于任何*保存的版本，应能完整恢复该版本的内容，且恢复后的内容应与保存时一致。
**验证需求：18.4**

**属性 11：配置往返一致性**
*对于任何*导出的配置，导入后系统行为应与导出前一致（排除敏感信息）。
**验证需求：23.2, 23.3**

**属性 12：模型切换正确性**
*对于任何*模型配置更改，后续的 AI 请求应使用新配置的模型。
**验证需求：20.4**

## 错误处理

### 错误分类

系统中的错误分为以下几类：

1. **用户输入错误**：无效的写作目标、格式错误的文件等
2. **系统错误**：文件系统故障、数据库连接失败等
3. **外部服务错误**：LLM API 失败、MCP 服务器不可用等
4. **业务逻辑错误**：循环依赖、权限不足等

### 错误处理策略

```python
class ErrorHandler:
    def handle_user_error(self, error: UserError) -> UserFriendlyMessage:
        """将用户错误转换为友好提示"""
        pass
    
    def handle_system_error(self, error: SystemError) -> RecoveryAction:
        """尝试从系统错误中恢复"""
        pass
    
    def handle_external_error(self, error: ExternalError) -> RetryStrategy:
        """处理外部服务错误，实施重试策略"""
        pass
```

### 重试策略

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    
class RetryStrategy:
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        pass
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避）"""
        return min(
            self.config.backoff_factor ** attempt,
            self.config.max_delay
        )
```

### 错误恢复

```python
class RecoveryManager:
    def save_checkpoint(self, state: AgentState) -> str:
        """保存检查点以便恢复"""
        pass
    
    def restore_from_checkpoint(self, checkpoint_id: str) -> AgentState:
        """从检查点恢复"""
        pass
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """回滚失败的事务"""
        pass
```

## 测试策略

### 单元测试

**目标**：验证各个组件的独立功能

**覆盖范围**：
- 文件系统管理器的文件操作
- 任务规划器的计划生成逻辑
- MCP 适配器的工具转换
- 技能加载器的解析和验证

**工具**：pytest, unittest.mock

**示例**：
```python
def test_file_system_write_read():
    """测试文件写入和读取"""
    fs = FileSystemManager()
    content = "测试内容"
    path = "/test/file.txt"
    
    fs.write_file(path, content)
    result = fs.read_file(path)
    
    assert result == content
```

### 属性基础测试

**目标**：验证正确性属性在大量随机输入下保持

**覆盖范围**：
- 所有核心正确性属性（属性 1-12）

**工具**：Hypothesis (Python 属性测试库)

**配置**：每个属性测试至少运行 100 次迭代

**示例**：
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=10000))
def test_file_roundtrip_consistency(content):
    """
    属性 2：文件系统往返一致性
    对于任何内容，写入后读取应返回相同内容
    """
    fs = FileSystemManager()
    path = f"/test/{uuid.uuid4()}.txt"
    
    fs.write_file(path, content)
    result = fs.read_file(path)
    
    assert result == content

@given(st.text(min_size=8001))  # 超过阈值
def test_context_size_management(large_content):
    """
    属性 3：上下文大小管理
    对于任何超过阈值的内容，应被外部化
    """
    agent = DeepAgent()
    result = agent.process_content(large_content)
    
    # 验证内容被存储为文件而不是直接在提示中
    assert result.is_externalized
    assert result.file_path is not None
```

### 集成测试

**目标**：验证组件间的交互

**覆盖范围**：
- DeepAgent 与 MCP 服务器的集成
- 前端与后端 API 的集成
- 技能加载和激活流程

**工具**：pytest, testcontainers

**示例**：
```python
def test_mcp_integration():
    """测试 MCP 服务器集成"""
    # 启动测试 MCP 服务器
    mcp_server = start_test_mcp_server()
    
    # 配置并连接
    adapter = MCPAdapter()
    adapter.connect_server(mcp_server.config)
    
    # 验证工具被发现
    tools = adapter.get_tools(mcp_server.id)
    assert len(tools) > 0
    
    # 验证工具可用
    tool = tools[0]
    result = tool.invoke({"query": "test"})
    assert result is not None
```

### 端到端测试

**目标**：验证完整的用户工作流

**覆盖范围**：
- 创建项目并生成写作计划
- 使用 AI 工具编辑文本
- 上传文件并引用
- 配置模型和 MCP 服务器

**工具**：Playwright (浏览器自动化)

**示例**：
```python
async def test_writing_workflow(page):
    """测试完整写作工作流"""
    # 登录
    await page.goto("/login")
    await page.fill("#email", "test@example.com")
    await page.click("#login-button")
    
    # 创建项目
    await page.click("#new-project")
    await page.fill("#project-title", "测试文章")
    
    # 请求 AI 生成计划
    await page.fill("#chat-input", "帮我写一篇关于 AI 的文章")
    await page.click("#send-button")
    
    # 等待计划生成
    await page.wait_for_selector(".task-list")
    tasks = await page.query_selector_all(".task-item")
    assert len(tasks) > 0
    
    # 验证可以编辑
    await page.click("#editor")
    await page.type("#editor", "这是测试内容")
    
    # 验证内容被保存
    await page.wait_for_timeout(1000)  # 等待自动保存
    content = await page.evaluate("() => editor.getContent()")
    assert "测试内容" in content
```

### 性能测试

**目标**：验证系统满足性能要求

**覆盖范围**：
- 编辑器响应延迟 < 100ms
- AI 响应开始时间 < 2s
- 大文档处理能力

**工具**：Locust (负载测试)

**示例**：
```python
from locust import HttpUser, task, between

class WritingAssistantUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def send_message(self):
        """模拟发送消息"""
        with self.client.post(
            "/api/chat/message",
            json={"content": "帮我改进这段文字"},
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 2:
                response.failure("响应时间超过 2 秒")
```

### 测试数据生成

**策略**：
- 使用 Faker 生成随机文本
- 使用 Hypothesis 生成边界情况
- 准备真实的写作样本作为测试数据

**示例**：
```python
from faker import Faker
from hypothesis import strategies as st

fake = Faker('zh_CN')

# 生成随机写作目标
writing_goals = st.one_of(
    st.just("写一篇博客文章"),
    st.just("创作一个短篇故事"),
    st.text(min_size=10, max_size=200)
)

# 生成随机文档内容
document_content = st.text(
    alphabet=st.characters(blacklist_categories=('Cs',)),
    min_size=0,
    max_size=50000
)
```

## 部署架构

### 开发环境

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://localhost/dev
      - REDIS_URL=redis://localhost:6379
    volumes:
      - ./backend:/app
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=dev
      - POSTGRES_PASSWORD=dev
      
  redis:
    image: redis:7
```

### 生产环境

**架构图**：
```
[用户] → [CDN] → [负载均衡器]
                      ↓
              [前端服务器集群]
                      ↓
              [API 网关]
                      ↓
         [后端服务器集群]
              ↙     ↓     ↘
    [PostgreSQL] [Redis] [向量数据库]
```

**扩展策略**：
- 前端：通过 CDN 和多区域部署
- 后端：水平扩展，使用容器编排（Kubernetes）
- 数据库：读写分离，主从复制
- 缓存：Redis 集群

### 监控和日志

**监控指标**：
- API 响应时间
- 错误率
- 资源使用率（CPU、内存、磁盘）
- LLM API 调用次数和成本

**日志策略**：
- 结构化日志（JSON 格式）
- 集中式日志收集（ELK Stack）
- 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

**告警规则**：
- API 错误率 > 5%
- 响应时间 > 5s
- 磁盘使用率 > 80%
- LLM API 失败率 > 10%

## 安全考虑

### 认证和授权

- 使用 JWT 进行 API 认证
- OAuth 2.0 集成（Google、GitHub）
- 基于角色的访问控制（RBAC）

### 数据安全

- 传输加密（TLS 1.3）
- 静态数据加密（数据库加密）
- API 密钥加密存储
- 敏感信息脱敏

### 输入验证

- 所有用户输入进行验证和清理
- 防止 SQL 注入、XSS 攻击
- 文件上传大小和类型限制
- 速率限制防止滥用

### 技能包安全

- 技能包签名验证
- 沙箱环境执行脚本
- 代码静态分析
- 权限最小化原则

## 可扩展性设计

### 插件系统

系统设计为高度可扩展，支持以下扩展点：

1. **模型提供商插件**：添加新的 LLM 提供商
2. **MCP 服务器插件**：连接新的外部工具和知识源
3. **技能插件**：添加新的写作能力
4. **UI 组件插件**：自定义编辑器工具和界面

### 版本兼容性

- API 版本控制（/api/v1/、/api/v2/）
- 向后兼容的数据模型迁移
- 技能包版本管理
- 配置格式版本化

### 国际化

- 多语言界面支持
- 多语言内容生成
- 本地化的提示词和技能
- 时区和日期格式处理

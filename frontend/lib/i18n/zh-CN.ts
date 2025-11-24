/**
 * 中文语言包
 * Chinese (Simplified) language pack
 */

export const zhCN = {
    // 通用
    common: {
        save: "保存",
        cancel: "取消",
        delete: "删除",
        edit: "编辑",
        add: "添加",
        confirm: "确认",
        close: "关闭",
        loading: "加载中...",
        success: "成功",
        error: "错误",
        warning: "警告",
        info: "信息",
    },

    // 顶部导航栏
    topBar: {
        logoText: "Muset.ai",
        newPage: "新建页面",
        credits: "积分",
        aiChatsLeft: "剩余 AI 对话",
        upgrade: "升级",
        freePlan: "免费计划",
        proPlan: "专业计划",
        guestUser: "访客用户",
    },

    // 左侧边栏
    leftSidebar: {
        myPages: "我的页面",
        chat: "聊天",
        recentlyUpdated: "最近更新",
        communityCreations: "社区创作",
        hideCommunityCreations: "隐藏社区创作",
        exploreCreations: "探索社区创作",
        noPages: "暂无页面",
        createFirstPage: "创建您的第一个页面",
    },

    // 聊天面板
    chatPanel: {
        welcomeMessage: "Muset 与你同思",
        inspiration: "灵感",
        inputPlaceholder: "说说你的想法，一起完善...",
        addContext: "添加上下文",
        uploadFile: "上传文件",
        uploadImage: "上传图片",
        send: "发送",
        suggestions: {
            title: "提示词建议",
            item1: "将「AI 职业转型」改编为适合 Twitter、Medium 和 YouTube 的内容。",
            item2: "给我 5 个本周的病毒式生活博客主题。",
            item3: "黄金投资：是还是不是？结合专家趋势分析",
        },
        inspirationItems: {
            peers: "看看同行在写什么",
            question: "提出一个发人深省的问题",
            spark: "激发新鲜灵感",
        },
    },

    // 富文本编辑器
    editor: {
        toolbar: {
            bold: "粗体",
            italic: "斜体",
            underline: "下划线",
            strike: "删除线",
            code: "代码",
            heading: "标题",
            bulletList: "无序列表",
            orderedList: "有序列表",
            blockquote: "引用",
            codeBlock: "代码块",
            link: "链接",
            image: "图片",
            undo: "撤销",
            redo: "重做",
        },
        aiTools: {
            continue: "继续写作",
            summarize: "总结",
            polish: "润色",
            translate: "翻译",
            expand: "扩写",
        },
        placeholder: "开始写作...",
    },

    // 设置抽屉
    settings: {
        title: "设置",
        tabs: {
            general: "通用",
            models: "模型",
            mcp: "MCP 服务器",
            skills: "技能包",
            vectorDB: "向量数据库",
        },
        actions: {
            testConnection: "测试连接",
            saveChanges: "保存更改",
            export: "导出配置",
            import: "导入配置",
        },
    },

    // 模型配置
    modelConfig: {
        title: "AI 模型配置",
        addModel: "添加模型",
        provider: "提供商",
        modelName: "模型名称",
        label: "显示名称",
        apiKey: "API 密钥",
        baseURL: "自定义端点",
        isDefault: "默认模型",
        streaming: "流式输出",
        vision: "视觉能力",
        toolUse: "工具使用",
        multilingual: "多语言",
        testConnection: "测试连接",
        setDefaultModel: "设为默认",
        deleteModel: "删除模型",
        providers: {
            anthropic: "Anthropic",
            openai: "OpenAI",
            azure: "Azure",
            local: "本地模型",
        },
        status: {
            connected: "已连接",
            disconnected: "未连接",
            testing: "测试中...",
            error: "连接失败",
        },
    },

    // MCP 配置
    mcpConfig: {
        title: "MCP 服务器配置",
        addServer: "添加服务器",
        serverName: "服务器名称",
        protocol: "协议",
        command: "启动命令",
        args: "参数",
        env: "环境变量",
        endpoint: "服务端点",
        authType: "认证类型",
        autoReconnect: "自动重连",
        tools: "工具列表",
        status: {
            connected: "已连接",
            disconnected: "未连接",
            error: "错误",
        },
        protocols: {
            stdio: "标准输入输出",
            http: "HTTP",
            ws: "WebSocket",
        },
        authTypes: {
            none: "无",
            apiKey: "API 密钥",
            oauth: "OAuth",
        },
    },

    // Skills 配置
    skillsConfig: {
        title: "技能包管理",
        uploadSkill: "上传技能包",
        skillName: "技能名称",
        version: "版本",
        provider: "提供商",
        description: "描述",
        enable: "启用",
        disable: "禁用",
        viewManifest: "查看清单",
        deleteSkill: "删除技能",
        tags: {
            style: "风格",
            translation: "翻译",
            research: "研究",
            editing: "编辑",
        },
    },

    // 向量数据库配置
    vectorDBConfig: {
        title: "向量数据库配置",
        provider: "提供商",
        apiKey: "API 密钥",
        environment: "环境",
        indexName: "索引名称",
        dimension: "向量维度",
        metric: "距离度量",
        testConnection: "测试连接",
        providers: {
            pinecone: "Pinecone",
            faiss: "FAISS",
            chroma: "Chroma",
        },
        metrics: {
            cosine: "余弦相似度",
            euclidean: "欧几里得距离",
            dotproduct: "点积",
        },
        status: {
            connected: "已连接",
            disconnected: "未连接",
            testing: "测试中...",
            error: "连接失败",
        },
    },

    // 配置导入导出
    configImportExport: {
        export: {
            title: "导出配置",
            description: "导出所有配置设置到 JSON 文件",
            includeSecrets: "包含敏感信息",
            download: "下载配置",
        },
        import: {
            title: "导入配置",
            description: "从 JSON 文件导入配置",
            selectFile: "选择文件",
            preview: "预览更改",
            merge: "合并",
            replace: "替换",
            skip: "跳过冲突",
            importButton: "导入配置",
        },
    },

    // 错误消息
    errors: {
        connectionFailed: "连接失败",
        saveFailed: "保存失败",
        deleteFailed: "删除失败",
        loadFailed: "加载失败",
        invalidConfig: "配置无效",
        missingField: "缺少必填字段",
        duplicateName: "名称已存在",
        uploadFailed: "上传失败",
        importFailed: "导入失败",
    },

    // 成功消息
    success: {
        connected: "连接成功",
        saved: "保存成功",
        deleted: "删除成功",
        uploaded: "上传成功",
        imported: "导入成功",
        exported: "导出成功",
    },

    // 确认消息
    confirm: {
        deleteModel: "确定要删除此模型配置吗？",
        deleteServer: "确定要删除此 MCP 服务器吗？",
        deleteSkill: "确定要删除此技能包吗？",
        overwriteConfig: "导入的配置将覆盖现有配置，确定继续吗？",
    },
};

export type Language = typeof zhCN;

export default zhCN;

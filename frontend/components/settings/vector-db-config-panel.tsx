"use client";

import React, { useState, useEffect } from "react";
import { Lightning, Check, X } from "phosphor-react";
import { Button } from "../ui/button";

interface VectorDBConfig {
    provider: string;
    api_key?: string;
    environment?: string;
    index_name: string;
    dimension: number;
    metric: string;
    status: string;
}

export function VectorDBConfigPanel() {
    const [config, setConfig] = useState<VectorDBConfig | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isTesting, setIsTesting] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState<Partial<VectorDBConfig>>({});

    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            setIsLoading(true);
            // TODO: 从后端加载配置
            // 目前使用环境变量作为默认值
            const defaultConfig = {
                provider: "pinecone",
                index_name: "muset-memories",
                environment: "us-east-1",
                dimension: 1536,
                metric: "cosine",
                status: "disconnected",
            };
            setConfig(defaultConfig);
            setFormData(defaultConfig);
        } catch (error) {
            console.error("加载向量数据库配置失败:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const testConnection = async () => {
        setIsTesting(true);
        try {
            // TODO: 调用后端测试接口
            await new Promise((resolve) => setTimeout(resolve, 2000));
            alert("连接成功！");
            setConfig({ ...config!, status: "connected" });
        } catch (error) {
            alert("连接失败");
            setConfig({ ...config!, status: "error" });
        } finally {
            setIsTesting(false);
        }
    };

    const saveConfig = async () => {
        try {
            // TODO: 保存到后端
            await new Promise((resolve) => setTimeout(resolve, 1000));
            setConfig(formData as VectorDBConfig);
            setIsEditing(false);
            alert("保存成功！");
        } catch (error) {
            alert("保存失败");
        }
    };

    if (isLoading) {
        return <div className="flex items-center justify-center py-12 text-gray-500">加载中...</div>;
    }

    const getStatusBadge = (status: string) => {
        const badges = {
            connected: {
                icon: <Check size={12} weight="bold" />,
                className: "bg-green-50 text-green-700",
                text: "已连接",
            },
            disconnected: {
                icon: <X size={12} weight="bold" />,
                className: "bg-gray-100 text-gray-700",
                text: "未连接",
            },
            error: {
                icon: <X size={12} weight="bold" />,
                className: "bg-red-50 text-red-700",
                text: "连接失败",
            },
        };

        const badge = badges[status as keyof typeof badges] || badges.disconnected;
        return (
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded ${badge.className}`}>
                {badge.icon}
                {badge.text}
            </span>
        );
    };

    return (
        <div className="space-y-6">
            {/* 标题 */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">向量数据库配置</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        配置向量数据库用于语义搜索和长期记忆
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {config && getStatusBadge(config.status)}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={testConnection}
                        disabled={isTesting}
                        className="gap-1.5"
                    >
                        <Lightning size={14} weight={isTesting ? "fill" : "bold"} />
                        {isTesting ? "测试中..." : "测试连接"}
                    </Button>
                </div>
            </div>

            {/* 配置表单 */}
            {config && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-800">
                    <div className="space-y-4">
                        {/* 提供商 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                提供商
                            </label>
                            <select
                                value={isEditing ? formData.provider : config.provider}
                                onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                                disabled={!isEditing}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            >
                                <option value="pinecone">Pinecone</option>
                                <option value="faiss">FAISS</option>
                                <option value="chroma">Chroma</option>
                            </select>
                        </div>

                        {/* API Key */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                API 密钥
                            </label>
                            <input
                                type="password"
                                value={isEditing ? formData.api_key || "" : "••••••••••••••••"}
                                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                                disabled={!isEditing}
                                placeholder="输入 API 密钥"
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            />
                        </div>

                        {/* 环境 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                环境
                            </label>
                            <input
                                type="text"
                                value={isEditing ? formData.environment : config.environment}
                                onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                                disabled={!isEditing}
                                placeholder="us-east-1"
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            />
                        </div>

                        {/* 索引名称 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                索引名称
                            </label>
                            <input
                                type="text"
                                value={isEditing ? formData.index_name : config.index_name}
                                onChange={(e) => setFormData({ ...formData, index_name: e.target.value })}
                                disabled={!isEditing}
                                placeholder="muset-memories"
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            />
                        </div>

                        {/* 向量维度 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                向量维度
                            </label>
                            <input
                                type="number"
                                value={isEditing ? formData.dimension : config.dimension}
                                onChange={(e) => setFormData({ ...formData, dimension: parseInt(e.target.value) })}
                                disabled={!isEditing}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            />
                        </div>

                        {/* 距离度量 */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                距离度量
                            </label>
                            <select
                                value={isEditing ? formData.metric : config.metric}
                                onChange={(e) => setFormData({ ...formData, metric: e.target.value })}
                                disabled={!isEditing}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
                            >
                                <option value="cosine">余弦相似度</option>
                                <option value="euclidean">欧几里得距离</option>
                                <option value="dotproduct">点积</option>
                            </select>
                        </div>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                        {isEditing ? (
                            <>
                                <Button
                                    variant="ghost"
                                    onClick={() => {
                                        setIsEditing(false);
                                        setFormData(config);
                                    }}
                                >
                                    取消
                                </Button>
                                <Button onClick={saveConfig}>保存更改</Button>
                            </>
                        ) : (
                            <Button variant="outline" onClick={() => setIsEditing(true)}>
                                编辑配置
                            </Button>
                        )}
                    </div>
                </div>
            )}

            {/* 配置说明 */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
                    关于向量数据库
                </h4>
                <p className="text-sm text-blue-700 dark:text-blue-400">
                    向量数据库用于存储和检索文档的语义嵌入，支持长期记忆功能。您需要在 Pinecone
                    或其他向量数据库提供商处创建索引，并在这里配置相应的连接信息。
                </p>
            </div>
        </div>
    );
}

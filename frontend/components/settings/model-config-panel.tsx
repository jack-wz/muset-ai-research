'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { apiClient } from '@/lib/api/client';

interface ModelConfig {
  id: number;
  provider: string;
  label: string;
  model_name: string;
  base_url?: string;
  is_default: boolean;
  capabilities: {
    streaming: boolean;
    vision: boolean;
    toolUse: boolean;
    multilingual: boolean;
  };
  guardrails?: any;
  created_at: string;
  updated_at: string;
}

interface ModelTestResult {
  success: boolean;
  provider: string;
  model: string;
  response_time?: number;
  response_preview?: string;
  error?: string;
}

export function ModelConfigPanel() {
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [testingModel, setTestingModel] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<ModelTestResult | null>(null);
  const [formData, setFormData] = useState({
    provider: 'anthropic',
    label: '',
    model_name: '',
    api_key: '',
    base_url: '',
    is_default: false,
  });

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/models/');
      setModels(response.data.models);
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/models/', formData);
      setShowForm(false);
      setFormData({
        provider: 'anthropic',
        label: '',
        model_name: '',
        api_key: '',
        base_url: '',
        is_default: false,
      });
      loadModels();
    } catch (error) {
      console.error('Failed to create model:', error);
      alert('创建模型失败，请检查配置');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个模型配置吗？')) return;

    try {
      await apiClient.delete(`/models/${id}`);
      loadModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
      alert('删除失败');
    }
  };

  const handleSetDefault = async (id: number) => {
    try {
      await apiClient.post(`/models/${id}/set-default`);
      loadModels();
    } catch (error) {
      console.error('Failed to set default:', error);
      alert('设置失败');
    }
  };

  const handleTest = async (id: number) => {
    try {
      setTestingModel(id);
      setTestResult(null);
      const response = await apiClient.post(`/models/${id}/test`);
      setTestResult(response.data);
    } catch (error: any) {
      console.error('Failed to test model:', error);
      setTestResult({
        success: false,
        provider: '',
        model: '',
        error: error.response?.data?.detail || '测试失败',
      });
    } finally {
      setTestingModel(null);
    }
  };

  const providerOptions = [
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'doubao', label: '豆包 (Doubao)' },
    { value: 'qianwen', label: '千问 (Qianwen)' },
    { value: 'kimi', label: 'Kimi' },
    { value: 'local', label: 'Local Model' },
  ];

  if (loading) {
    return (
      <Card className="p-6">
        <p className="text-center text-gray-600">加载中...</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">模型配置</h2>
          <p className="text-sm text-gray-600 mt-1">管理 AI 模型提供商和配置</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '添加模型'}
        </Button>
      </div>

      {/* Add Model Form */}
      {showForm && (
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">添加新模型</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                提供商
              </label>
              <select
                value={formData.provider}
                onChange={(e) =>
                  setFormData({ ...formData, provider: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                {providerOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                标签
              </label>
              <Input
                value={formData.label}
                onChange={(e) =>
                  setFormData({ ...formData, label: e.target.value })
                }
                placeholder="例如: Claude Sonnet"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                模型名称
              </label>
              <Input
                value={formData.model_name}
                onChange={(e) =>
                  setFormData({ ...formData, model_name: e.target.value })
                }
                placeholder="例如: claude-3-5-sonnet-20241022"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key
              </label>
              <Input
                type="password"
                value={formData.api_key}
                onChange={(e) =>
                  setFormData({ ...formData, api_key: e.target.value })
                }
                placeholder="sk-ant-..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base URL (可选)
              </label>
              <Input
                value={formData.base_url}
                onChange={(e) =>
                  setFormData({ ...formData, base_url: e.target.value })
                }
                placeholder="https://api.example.com"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_default"
                checked={formData.is_default}
                onChange={(e) =>
                  setFormData({ ...formData, is_default: e.target.checked })
                }
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <label
                htmlFor="is_default"
                className="ml-2 block text-sm text-gray-900"
              >
                设为默认模型
              </label>
            </div>

            <div className="flex gap-2">
              <Button type="submit" className="flex-1">
                创建
              </Button>
              <Button
                type="button"
                onClick={() => setShowForm(false)}
                className="flex-1 bg-gray-200 text-gray-800 hover:bg-gray-300"
              >
                取消
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Test Result */}
      {testResult && (
        <Card className={`p-4 ${testResult.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="flex items-start">
            <span className="text-2xl mr-3">
              {testResult.success ? '✅' : '❌'}
            </span>
            <div className="flex-1">
              <h4 className="font-medium">
                {testResult.success ? '连接成功' : '连接失败'}
              </h4>
              {testResult.success ? (
                <div className="text-sm mt-1">
                  <p>响应时间: {testResult.response_time?.toFixed(2)}s</p>
                  <p className="text-gray-600 mt-1">
                    预览: {testResult.response_preview}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-red-600 mt-1">{testResult.error}</p>
              )}
            </div>
            <button
              onClick={() => setTestResult(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
        </Card>
      )}

      {/* Models List */}
      <div className="space-y-4">
        {models.length === 0 ? (
          <Card className="p-6 text-center text-gray-600">
            还没有配置任何模型，点击上方按钮添加
          </Card>
        ) : (
          models.map((model) => (
            <Card key={model.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-medium text-gray-900">
                      {model.label}
                    </h3>
                    {model.is_default && (
                      <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded">
                        默认
                      </span>
                    )}
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <p>
                      <span className="font-medium">提供商:</span>{' '}
                      {model.provider}
                    </p>
                    <p>
                      <span className="font-medium">模型:</span>{' '}
                      {model.model_name}
                    </p>
                    {model.base_url && (
                      <p>
                        <span className="font-medium">Base URL:</span>{' '}
                        {model.base_url}
                      </p>
                    )}
                    <div className="flex gap-2 mt-2">
                      {model.capabilities.streaming && (
                        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                          流式
                        </span>
                      )}
                      {model.capabilities.vision && (
                        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                          视觉
                        </span>
                      )}
                      {model.capabilities.toolUse && (
                        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                          工具调用
                        </span>
                      )}
                      {model.capabilities.multilingual && (
                        <span className="px-2 py-1 text-xs bg-gray-100 rounded">
                          多语言
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleTest(model.id)}
                    disabled={testingModel === model.id}
                    className="text-sm bg-blue-500 hover:bg-blue-600"
                  >
                    {testingModel === model.id ? '测试中...' : '测试'}
                  </Button>
                  {!model.is_default && (
                    <Button
                      onClick={() => handleSetDefault(model.id)}
                      className="text-sm bg-green-500 hover:bg-green-600"
                    >
                      设为默认
                    </Button>
                  )}
                  <Button
                    onClick={() => handleDelete(model.id)}
                    className="text-sm bg-red-500 hover:bg-red-600"
                  >
                    删除
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}

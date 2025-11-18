'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api/client';

interface MCPServerConfig {
  id: number;
  name: string;
  protocol: string;
  command?: string;
  args?: string[];
  endpoint?: string;
  auth_type: string;
  status: string;
  last_connected_at?: string;
  tool_count: number;
  retry_policy: {
    maxAttempts: number;
    backoffMs: number;
  };
  auto_reconnect: boolean;
  created_at: string;
  updated_at: string;
}

export function MCPConfigPanel() {
  const [servers, setServers] = useState<MCPServerConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    protocol: 'stdio',
    command: '',
    args: '',
    endpoint: '',
    auth_type: 'none',
    auto_reconnect: true,
  });

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/mcp/');
      setServers(response.data.servers);
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data: any = {
        name: formData.name,
        protocol: formData.protocol,
        auth_type: formData.auth_type,
        auto_reconnect: formData.auto_reconnect,
      };

      if (formData.protocol === 'stdio') {
        data.command = formData.command;
        data.args = formData.args.split(' ').filter((arg) => arg.trim());
      } else {
        data.endpoint = formData.endpoint;
      }

      await apiClient.post('/mcp/', data);
      setShowForm(false);
      setFormData({
        name: '',
        protocol: 'stdio',
        command: '',
        args: '',
        endpoint: '',
        auth_type: 'none',
        auto_reconnect: true,
      });
      loadServers();
    } catch (error) {
      console.error('Failed to create MCP server:', error);
      alert('创建 MCP 服务器失败');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个 MCP 服务器吗？')) return;

    try {
      await apiClient.delete(`/mcp/${id}`);
      loadServers();
    } catch (error) {
      console.error('Failed to delete MCP server:', error);
      alert('删除失败');
    }
  };

  const handleAction = async (id: number, action: string) => {
    try {
      await apiClient.post(`/mcp/${id}/action`, { action });
      loadServers();
    } catch (error) {
      console.error(`Failed to ${action} MCP server:`, error);
      alert(`${action} 失败`);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      connected: 'bg-green-100 text-green-800',
      disconnected: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800',
    };
    return styles[status as keyof typeof styles] || styles.disconnected;
  };

  const getStatusText = (status: string) => {
    const texts = {
      connected: '已连接',
      disconnected: '未连接',
      error: '错误',
    };
    return texts[status as keyof typeof texts] || status;
  };

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
          <h2 className="text-xl font-semibold text-gray-900">MCP 服务器配置</h2>
          <p className="text-sm text-gray-600 mt-1">
            管理 Model Context Protocol 服务器连接
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '添加服务器'}
        </Button>
      </div>

      {/* Add Server Form */}
      {showForm && (
        <Card className="p-6">
          <h3 className="text-lg font-medium mb-4">添加 MCP 服务器</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                服务器名称
              </label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="例如: filesystem-server"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                协议
              </label>
              <select
                value={formData.protocol}
                onChange={(e) =>
                  setFormData({ ...formData, protocol: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              >
                <option value="stdio">stdio</option>
                <option value="http">HTTP</option>
                <option value="ws">WebSocket</option>
              </select>
            </div>

            {formData.protocol === 'stdio' ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    命令
                  </label>
                  <Input
                    value={formData.command}
                    onChange={(e) =>
                      setFormData({ ...formData, command: e.target.value })
                    }
                    placeholder="例如: npx"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    参数 (空格分隔)
                  </label>
                  <Input
                    value={formData.args}
                    onChange={(e) =>
                      setFormData({ ...formData, args: e.target.value })
                    }
                    placeholder="例如: -y @modelcontextprotocol/server-filesystem"
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  端点 URL
                </label>
                <Input
                  value={formData.endpoint}
                  onChange={(e) =>
                    setFormData({ ...formData, endpoint: e.target.value })
                  }
                  placeholder="https://api.example.com/mcp"
                  required
                />
              </div>
            )}

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_reconnect"
                checked={formData.auto_reconnect}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    auto_reconnect: e.target.checked,
                  })
                }
                className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
              />
              <label
                htmlFor="auto_reconnect"
                className="ml-2 block text-sm text-gray-900"
              >
                启动时自动重连
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

      {/* Servers List */}
      <div className="space-y-4">
        {servers.length === 0 ? (
          <Card className="p-6 text-center text-gray-600">
            还没有配置任何 MCP 服务器，点击上方按钮添加
          </Card>
        ) : (
          servers.map((server) => (
            <Card key={server.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-medium text-gray-900">
                      {server.name}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs rounded ${getStatusBadge(
                        server.status
                      )}`}
                    >
                      {getStatusText(server.status)}
                    </span>
                    {server.status === 'connected' && (
                      <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {server.tool_count} 工具
                      </span>
                    )}
                  </div>
                  <div className="mt-2 space-y-1 text-sm text-gray-600">
                    <p>
                      <span className="font-medium">协议:</span> {server.protocol}
                    </p>
                    {server.protocol === 'stdio' && server.command && (
                      <p>
                        <span className="font-medium">命令:</span> {server.command}{' '}
                        {server.args?.join(' ')}
                      </p>
                    )}
                    {server.protocol !== 'stdio' && server.endpoint && (
                      <p>
                        <span className="font-medium">端点:</span> {server.endpoint}
                      </p>
                    )}
                    {server.last_connected_at && (
                      <p>
                        <span className="font-medium">上次连接:</span>{' '}
                        {new Date(server.last_connected_at).toLocaleString()}
                      </p>
                    )}
                    <p>
                      <span className="font-medium">自动重连:</span>{' '}
                      {server.auto_reconnect ? '是' : '否'}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {server.status === 'disconnected' && (
                    <Button
                      onClick={() => handleAction(server.id, 'connect')}
                      className="text-sm bg-green-500 hover:bg-green-600"
                    >
                      连接
                    </Button>
                  )}
                  {server.status === 'connected' && (
                    <Button
                      onClick={() => handleAction(server.id, 'disconnect')}
                      className="text-sm bg-yellow-500 hover:bg-yellow-600"
                    >
                      断开
                    </Button>
                  )}
                  {server.status === 'error' && (
                    <Button
                      onClick={() => handleAction(server.id, 'reconnect')}
                      className="text-sm bg-blue-500 hover:bg-blue-600"
                    >
                      重连
                    </Button>
                  )}
                  <Button
                    onClick={() => handleDelete(server.id)}
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

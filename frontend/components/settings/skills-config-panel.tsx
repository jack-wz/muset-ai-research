'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api/client';

interface SkillPackage {
  id: number;
  name: string;
  version: string;
  provider: string;
  description: string;
  instructions: string;
  default_enabled: boolean;
  active: boolean;
  required_resources: string[];
  exposed_tools: string[];
  created_at: string;
  updated_at: string;
}

export function SkillsConfigPanel() {
  const [skills, setSkills] = useState<SkillPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedSkill, setSelectedSkill] = useState<SkillPackage | null>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{ skills: SkillPackage[] }>('/skills/');
      setSkills(response.skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      alert('请上传 .zip 格式的技能包');
      return;
    }

    try {
      setUploadingFile(true);
      const formData = new FormData();
      formData.append('file', file);

      await apiClient.post('/skills/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      loadSkills();
      // Reset file input
      e.target.value = '';
    } catch (error) {
      console.error('Failed to upload skill:', error);
      alert((error as any).response?.data?.detail || '上传技能包失败');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个技能包吗？')) return;

    try {
      await apiClient.delete(`/skills/${id}`);
      setSelectedSkill(null);
      loadSkills();
    } catch (error) {
      console.error('Failed to delete skill:', error);
      alert('删除失败');
    }
  };

  const handleToggleActive = async (id: number, currentActive: boolean) => {
    try {
      const action = currentActive ? 'deactivate' : 'activate';
      await apiClient.post(`/skills/${id}/action`, { action });
      loadSkills();
      if (selectedSkill?.id === id) {
        const response = await apiClient.get<SkillPackage>(`/skills/${id}`);
        setSkills(skills.map(s => s.id === id ? response : s));
      }
    } catch (error) {
      console.error('Failed to toggle skill:', error);
      alert('操作失败');
    }
  };

  const handleViewDetails = async (skill: SkillPackage) => {
    try {
      const response = await apiClient.get<SkillPackage>(`/skills/${skill.id}`);
      setSelectedSkill(response);
    } catch (error) {
      console.error('Failed to load skill details:', error);
      alert('加载详情失败');
    }
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
          <h2 className="text-xl font-semibold text-gray-900">技能管理</h2>
          <p className="text-sm text-gray-600 mt-1">
            管理 Claude Skills 包和自定义技能
          </p>
        </div>
        <div>
          <input
            type="file"
            id="skill-upload"
            accept=".zip"
            onChange={handleFileUpload}
            className="hidden"
            disabled={uploadingFile}
          />
          <Button
            onClick={() => document.getElementById('skill-upload')?.click()}
            disabled={uploadingFile}
          >
            {uploadingFile ? '上传中...' : '上传技能包'}
          </Button>
        </div>
      </div>

      {/* Skills Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills List */}
        <div className="space-y-4">
          {skills.length === 0 ? (
            <Card className="p-6 text-center text-gray-600">
              还没有安装任何技能包，点击上方按钮上传
            </Card>
          ) : (
            skills.map((skill) => (
              <Card
                key={skill.id}
                className={`p-4 cursor-pointer transition-all ${selectedSkill?.id === skill.id
                  ? 'ring-2 ring-indigo-500'
                  : 'hover:shadow-md'
                  }`}
                onClick={() => handleViewDetails(skill)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{skill.name}</h3>
                      {skill.active && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                          已激活
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      v{skill.version} · {skill.provider}
                    </p>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {skill.description || '没有描述'}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleActive(skill.id, skill.active);
                    }}
                    className={`px-3 py-1 text-sm rounded ${skill.active
                      ? 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                      : 'bg-indigo-500 text-white hover:bg-indigo-600'
                      }`}
                  >
                    {skill.active ? '停用' : '激活'}
                  </button>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* Skill Details */}
        {selectedSkill ? (
          <Card className="p-6 sticky top-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedSkill.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  v{selectedSkill.version} · {selectedSkill.provider}
                </p>
              </div>
              <Button
                onClick={() => handleDelete(selectedSkill.id)}
                className="text-sm bg-red-500 hover:bg-red-600"
              >
                删除
              </Button>
            </div>

            <div className="space-y-4">
              {/* Status */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">状态</h4>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 text-sm rounded ${selectedSkill.active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                      }`}
                  >
                    {selectedSkill.active ? '已激活' : '未激活'}
                  </span>
                  {selectedSkill.default_enabled && (
                    <span className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded">
                      默认启用
                    </span>
                  )}
                </div>
              </div>

              {/* Resources */}
              {selectedSkill.required_resources.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    需要的资源
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedSkill.required_resources.map((resource, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-gray-100 rounded"
                      >
                        {resource}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tools */}
              {selectedSkill.exposed_tools.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    暴露的工具
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedSkill.exposed_tools.map((tool, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Instructions */}
              {selectedSkill.instructions && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    使用说明
                  </h4>
                  <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 max-h-64 overflow-y-auto">
                    <pre className="whitespace-pre-wrap font-mono text-xs">
                      {selectedSkill.instructions}
                    </pre>
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  创建于: {new Date(selectedSkill.created_at).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  更新于: {new Date(selectedSkill.updated_at).toLocaleString()}
                </p>
              </div>
            </div>
          </Card>
        ) : (
          <Card className="p-6 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-4xl mb-2">📦</p>
              <p>选择一个技能包查看详情</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

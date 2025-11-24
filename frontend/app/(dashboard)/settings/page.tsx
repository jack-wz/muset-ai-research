'use client';

import { useState } from 'react';
import { ModelConfigPanel } from '@/components/settings/model-config-panel';
import { MCPConfigPanel } from '@/components/settings/mcp-config-panel';
import { SkillsConfigPanel } from '@/components/settings/skills-config-panel';
import { ConfigImportExport } from '@/components/settings/config-import-export';

type TabType = 'models' | 'mcp' | 'skills' | 'import-export';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('models');

  const tabs = [
    { id: 'models' as TabType, label: '模型配置', icon: '🤖' },
    { id: 'mcp' as TabType, label: 'MCP 服务器', icon: '🔌' },
    { id: 'skills' as TabType, label: '技能管理', icon: '⚡' },
    { id: 'import-export' as TabType, label: '导入导出', icon: '💾' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">设置</h1>
          <p className="text-sm text-gray-600 mt-1">管理模型、MCP 服务器和技能配置</p>
        </header>

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 px-6">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            {activeTab === 'models' && <ModelConfigPanel />}
            {activeTab === 'mcp' && <MCPConfigPanel />}
            {activeTab === 'skills' && <SkillsConfigPanel />}
            {activeTab === 'import-export' && <ConfigImportExport />}
          </div>
        </main>
      </div>
    </div>
  );
}

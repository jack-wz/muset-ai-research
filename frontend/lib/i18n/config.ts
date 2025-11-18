/**
 * i18n Configuration
 *
 * Manages internationalization for the application.
 * Supports Chinese (zh) and English (en).
 */

export type Locale = 'zh' | 'en';

export const defaultLocale: Locale = 'zh';

export const locales: Locale[] = ['zh', 'en'];

export interface I18nConfig {
  locale: Locale;
  messages: Record<string, string>;
}

// Translation messages
const messages = {
  zh: {
    // Common
    'common.save': '保存',
    'common.cancel': '取消',
    'common.delete': '删除',
    'common.edit': '编辑',
    'common.create': '创建',
    'common.close': '关闭',
    'common.confirm': '确认',

    // Settings
    'settings.title': '设置',
    'settings.models': '模型配置',
    'settings.mcp': 'MCP 服务器',
    'settings.skills': '技能管理',
    'settings.importExport': '导入导出',

    // Models
    'models.add': '添加模型',
    'models.provider': '提供商',
    'models.label': '标签',
    'models.modelName': '模型名称',
    'models.apiKey': 'API Key',
    'models.setDefault': '设为默认',
    'models.test': '测试连接',

    // Chat
    'chat.placeholder': '输入消息...',
    'chat.send': '发送',
    'chat.newChat': '新对话',

    // Editor
    'editor.placeholder': '开始写作...',
    'editor.title': '标题',
  },
  en: {
    // Common
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.create': 'Create',
    'common.close': 'Close',
    'common.confirm': 'Confirm',

    // Settings
    'settings.title': 'Settings',
    'settings.models': 'Model Configuration',
    'settings.mcp': 'MCP Servers',
    'settings.skills': 'Skills Management',
    'settings.importExport': 'Import/Export',

    // Models
    'models.add': 'Add Model',
    'models.provider': 'Provider',
    'models.label': 'Label',
    'models.modelName': 'Model Name',
    'models.apiKey': 'API Key',
    'models.setDefault': 'Set as Default',
    'models.test': 'Test Connection',

    // Chat
    'chat.placeholder': 'Type a message...',
    'chat.send': 'Send',
    'chat.newChat': 'New Chat',

    // Editor
    'editor.placeholder': 'Start writing...',
    'editor.title': 'Title',
  },
};

export function getMessages(locale: Locale): Record<string, string> {
  return messages[locale] || messages[defaultLocale];
}

export function formatMessage(locale: Locale, key: string): string {
  const msgs = getMessages(locale);
  return msgs[key] || key;
}

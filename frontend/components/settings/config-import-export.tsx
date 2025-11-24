'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api/client';

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  preview: {
    models_count: number;
    mcp_servers_count: number;
  };
}

export function ConfigImportExport() {
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [validating, setValidating] = useState(false);
  const [includeApiKeys, setIncludeApiKeys] = useState(false);
  const [overwrite, setOverwrite] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(
    null
  );
  const [importResult, setImportResult] = useState<any>(null);

  const handleExport = async () => {
    try {
      setExporting(true);
      const response: any = await apiClient.get('/config/export', {
        params: { include_api_keys: includeApiKeys },
      });

      // Download as JSON file
      const blob = new Blob([JSON.stringify(response.data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `muset-config-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      alert('配置导出成功！');
    } catch (error: any) {
      console.error('Failed to export configuration:', error);
      alert(error.response?.data?.detail || '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      alert('请选择 JSON 格式的配置文件');
      return;
    }

    try {
      setValidating(true);
      const fileContent = await file.text();
      const configData = JSON.parse(fileContent);

      // Validate configuration
      const response: any = await apiClient.post('/config/validate', configData);
      setValidationResult(response.data);
    } catch (error: any) {
      console.error('Failed to validate configuration:', error);
      if (error instanceof SyntaxError) {
        alert('无效的 JSON 文件');
      } else {
        alert(error.response?.data?.detail || '验证失败');
      }
      setValidationResult(null);
    } finally {
      setValidating(false);
      // Reset file input
      e.target.value = '';
    }
  };

  const handleImport = async () => {
    if (!validationResult) return;

    try {
      setImporting(true);
      // Re-read the file content
      const fileInput = document.getElementById(
        'config-import'
      ) as HTMLInputElement;
      if (!fileInput || !fileInput.files?.[0]) {
        alert('请先选择配置文件');
        return;
      }

      const fileContent = await fileInput.files[0].text();
      const configData = JSON.parse(fileContent);

      const response: any = await apiClient.post('/config/import', {
        config: configData,
        overwrite,
      });

      setImportResult(response.data);
      setValidationResult(null);
      alert('配置导入成功！');

      // Reload page to reflect changes
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (error: any) {
      console.error('Failed to import configuration:', error);
      alert(error.response?.data?.detail || '导入失败');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">配置导入导出</h2>
        <p className="text-sm text-gray-600 mt-1">
          备份和恢复模型、MCP 服务器配置
        </p>
      </div>

      {/* Export Section */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">导出配置</h3>
        <p className="text-sm text-gray-600 mb-4">
          导出当前所有配置到 JSON 文件。可选择是否包含 API 密钥。
        </p>

        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="include-api-keys"
              checked={includeApiKeys}
              onChange={(e) => setIncludeApiKeys(e.target.checked)}
              className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
            />
            <label
              htmlFor="include-api-keys"
              className="ml-2 block text-sm text-gray-900"
            >
              包含 API 密钥（仅用于安全备份，不要分享）
            </label>
          </div>

          {includeApiKeys && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
              <div className="flex">
                <span className="text-yellow-400 mr-2">⚠️</span>
                <p className="text-sm text-yellow-800">
                  <strong>警告：</strong>导出的文件将包含敏感的 API
                  密钥。请妥善保管，不要分享给他人或上传到公共位置。
                </p>
              </div>
            </div>
          )}

          <Button onClick={handleExport} disabled={exporting} className="w-full">
            {exporting ? '导出中...' : '导出配置'}
          </Button>
        </div>
      </Card>

      {/* Import Section */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">导入配置</h3>
        <p className="text-sm text-gray-600 mb-4">
          从 JSON 文件导入配置。导入前会先验证文件格式。
        </p>

        <div className="space-y-4">
          <div>
            <input
              type="file"
              id="config-import"
              accept=".json"
              onChange={handleFileSelect}
              className="hidden"
              disabled={validating || importing}
            />
            <Button
              onClick={() => document.getElementById('config-import')?.click()}
              disabled={validating || importing}
              className="w-full bg-blue-500 hover:bg-blue-600"
            >
              {validating ? '验证中...' : '选择配置文件'}
            </Button>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div
              className={`border rounded-md p-4 ${validationResult.valid
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
                }`}
            >
              <div className="flex items-start">
                <span className="text-2xl mr-3">
                  {validationResult.valid ? '✅' : '❌'}
                </span>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {validationResult.valid ? '验证通过' : '验证失败'}
                  </h4>

                  {/* Preview */}
                  <div className="text-sm text-gray-700 mb-3">
                    <p>
                      模型配置: {validationResult.preview.models_count} 个
                    </p>
                    <p>
                      MCP 服务器: {validationResult.preview.mcp_servers_count} 个
                    </p>
                  </div>

                  {/* Errors */}
                  {validationResult.errors.length > 0 && (
                    <div className="mb-3">
                      <p className="font-medium text-red-800 mb-1">错误:</p>
                      <ul className="list-disc list-inside text-sm text-red-700">
                        {validationResult.errors.map((error, idx) => (
                          <li key={idx}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Warnings */}
                  {validationResult.warnings.length > 0 && (
                    <div>
                      <p className="font-medium text-yellow-800 mb-1">警告:</p>
                      <ul className="list-disc list-inside text-sm text-yellow-700">
                        {validationResult.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Import Options */}
              {validationResult.valid && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      id="overwrite"
                      checked={overwrite}
                      onChange={(e) => setOverwrite(e.target.checked)}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded"
                    />
                    <label
                      htmlFor="overwrite"
                      className="ml-2 block text-sm text-gray-900"
                    >
                      覆盖已存在的配置
                    </label>
                  </div>

                  <Button
                    onClick={handleImport}
                    disabled={importing}
                    className="w-full bg-green-500 hover:bg-green-600"
                  >
                    {importing ? '导入中...' : '确认导入'}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Import Result */}
          {importResult && (
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <h4 className="font-medium text-blue-900 mb-2">导入成功</h4>
              <div className="text-sm text-blue-800">
                <p>已导入 {importResult.models_imported} 个模型配置</p>
                <p>已导入 {importResult.mcp_servers_imported} 个 MCP 服务器</p>
                {importResult.errors && importResult.errors.length > 0 && (
                  <div className="mt-2">
                    <p className="font-medium">部分错误:</p>
                    <ul className="list-disc list-inside">
                      {importResult.errors.map((error: string, idx: number) => (
                        <li key={idx}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Instructions */}
      <Card className="p-6 bg-gray-50">
        <h3 className="text-lg font-medium text-gray-900 mb-3">使用说明</h3>
        <div className="text-sm text-gray-700 space-y-2">
          <p>
            <strong>导出：</strong>导出当前所有配置到 JSON 文件。为了安全，默认不包含
            API 密钥。
          </p>
          <p>
            <strong>导入：</strong>从 JSON
            文件导入配置。导入前会自动验证文件格式。
          </p>
          <p>
            <strong>覆盖模式：</strong>启用后，相同名称的配置会被导入的配置覆盖。
          </p>
          <p>
            <strong>API 密钥：</strong>如果导出时未包含 API
            密钥，导入后需要手动配置。
          </p>
        </div>
      </Card>
    </div>
  );
}

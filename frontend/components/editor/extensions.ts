/**
 * TipTap 扩展配置
 * 只使用与 TipTap v2 兼容的扩展
 */

import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";

// 暂时只使用核心扩展，避免版本冲突
// 后续可以升级到 TipTap v3 以使用更多扩展

export const getEditorExtensions = () => [
    StarterKit.configure({
        heading: {
            levels: [1, 2, 3],
        },
        codeBlock: {
            HTMLAttributes: {
                class: "rounded-lg bg-gray-900 p-4 text-gray-100",
            },
        },
        blockquote: {
            HTMLAttributes: {
                class: "border-l-4 border-primary pl-4 italic text-gray-600",
            },
        },
    }),

    Placeholder.configure({
        placeholder: "开始写作或输入 / 调出命令菜单...",
    }),
];

export default getEditorExtensions;

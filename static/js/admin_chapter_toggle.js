/* static/js/admin_chapter_toggle.js */
/**
 * 章节内容动态控制器 (Admin Chapter Toggle) v14.0
 * =========================================================
 * 修复日志：
 * 1. [资料下载] 模式下：
 * - 强制隐藏 'attachment' (课件资料上传按钮)
 * - 强制隐藏 'video_file' (视频上传按钮)
 * - 强制显示 'video_url' (外部链接框)
 * - 将 'video_url' 标签改名为 "外部资源链接"
 * =========================================================
 */

console.log("🚀 [System] 章节界面优化脚本 v14.0 (纯链接修复版) 已加载");

document.addEventListener('DOMContentLoaded', function() {

    // =========================================================
    // 1. 核心工具函数 (Utility Functions)
    // =========================================================

    /**
     * 控制【单个字段行】的显示/隐藏
     * @param {HTMLElement} container - 当前章节的容器
     * @param {string} fieldName - 字段名 (如 video_url)
     * @param {boolean} show - 是否显示
     */
    function setRowDisplay(container, fieldName, show) {
        // 1. 尝试查找 Django 原生样式的行
        let target = container.querySelector(`.field-${fieldName}`);

        // 2. 兼容 SimpleUI 样式 (通过 input name 反向查找容器)
        if (!target) {
            const input = container.querySelector(`[name$="-${fieldName}"]`);
            if (input) {
                target = input.closest('.form-row') || input.closest('.el-form-item');
            }
        }

        // 3. 执行显隐 (使用 !important 覆盖框架自带的 display: flex)
        if (target) {
            target.style.setProperty('display', show ? 'block' : 'none', 'important');
        }
    }

    /**
     * 控制【Fieldset 分组】的显示/隐藏
     * 用于处理包含标题的区域 (如 "视频与课件" 标题)
     */
    function setFieldsetDisplay(container, representativeFieldName, show) {
        let field = container.querySelector(`.field-${representativeFieldName}`);

        if (!field) {
            const input = container.querySelector(`[name$="-${representativeFieldName}"]`);
            if (input) field = input.closest('.form-row') || input.closest('.el-form-item');
        }

        if (field) {
            const fieldset = field.closest('fieldset');
            if (fieldset) {
                fieldset.style.setProperty('display', show ? 'block' : 'none', 'important');
            }
        }
    }

    /**
     * 【UI 动态化】修改字段标签和提示占位符
     */
    function updateFieldLabel(container, fieldName, newLabelText, newPlaceholder) {
        let fieldRow = container.querySelector(`.field-${fieldName}`);
        // 兼容 SimpleUI
        if (!fieldRow) {
            const input = container.querySelector(`[name$="-${fieldName}"]`);
            if (input) fieldRow = input.closest('.form-row') || input.closest('.el-form-item');
        }

        if (fieldRow) {
            // 1. 修改 Label
            const label = fieldRow.querySelector('label');
            if (label) {
                if (!label.getAttribute('data-original-text')) {
                    label.setAttribute('data-original-text', label.textContent);
                }

                // 尝试仅修改文本节点，避免覆盖必填项的星号
                let textNodeFound = false;
                label.childNodes.forEach(node => {
                    if (node.nodeType === 3 && node.textContent.trim().length > 0) {
                        node.textContent = newLabelText;
                        textNodeFound = true;
                    }
                });

                if (!textNodeFound) label.textContent = newLabelText;
            }

            // 2. 修改 Input 占位符
            const input = fieldRow.querySelector('input[type="text"], input[type="url"]');
            if (input) {
                input.placeholder = newPlaceholder || '';
            }
        }
    }

    /**
     * 隐藏重复的 Label (针对 CKEditor)
     */
    function hideDuplicateLabel(container, fieldName) {
        const fieldRow = container.querySelector(`.field-${fieldName}`);
        if (fieldRow) {
            const label = fieldRow.querySelector('label');
            if (label) label.style.setProperty('display', 'none', 'important');
        }
    }

    // =========================================================
    // 2. 业务逻辑核心 (Business Logic)
    // =========================================================

    function refreshChapterRow(row) {
        if (!row) return;

        const typeSelect = row.querySelector('select[name$="-chapter_type"]');
        const formatSelect = row.querySelector('select[name$="-content_format"]');

        if (!typeSelect) return;

        const type = typeSelect.value;
        const format = formatSelect ? formatSelect.value : 'rich';

        // ---------------------------------------------------------
        // 场景 A: 📄 图文阅读 (Text Mode)
        // ---------------------------------------------------------
        if (type === 'text') {
            setFieldsetDisplay(row, 'content_format', true);
            setFieldsetDisplay(row, 'video_file', false); // 隐藏整个视频组

            setRowDisplay(row, 'content_format', true);
            setRowDisplay(row, 'font_size', true);

            if (format === 'md') {
                setRowDisplay(row, 'content_md', true);
                setRowDisplay(row, 'content_rich', false);
            } else {
                setRowDisplay(row, 'content_rich', true);
                setRowDisplay(row, 'content_md', false);
                hideDuplicateLabel(row, 'content_rich');
            }
        }

        // ---------------------------------------------------------
        // 场景 B: 📺 视频学习 (Video Mode)
        // ---------------------------------------------------------
        else if (type === 'video') {
            setFieldsetDisplay(row, 'content_format', false);
            setFieldsetDisplay(row, 'video_file', true);

            // 视频模式：显示上传 + 链接
            setRowDisplay(row, 'video_file', true);
            setRowDisplay(row, 'video_url', true);

            // 隐藏资料附件
            setRowDisplay(row, 'attachment', false);

            updateFieldLabel(row, 'video_url', '外部视频链接:', '请输入 B站/优酷 等视频页面地址');
        }

        // ---------------------------------------------------------
        // 场景 C: 💾 资料下载 (File Mode) —— [您的核心需求修复]
        // ---------------------------------------------------------
        else if (type === 'file') {
            setFieldsetDisplay(row, 'content_format', false);
            setFieldsetDisplay(row, 'video_file', true); // 打开这个组

            // ❌ 彻底隐藏所有文件上传按钮
            setRowDisplay(row, 'video_file', false);
            setRowDisplay(row, 'attachment', false); // <--- 关键修复：这里必须是 false

            // ✅ 仅显示外部链接输入框
            setRowDisplay(row, 'video_url', true);

            // ✏️ 修改标签名称，让用户知道这里填资料链接
            updateFieldLabel(row, 'video_url', '外部资源链接:', '请输入网盘地址、文档链接或跳转网址');
        }
    }

    // =========================================================
    // 3. 事件监听 (EventListeners)
    // =========================================================

    function getContainer(el) {
        return el.closest('.inline-related') || el.closest('fieldset.module');
    }

    document.body.addEventListener('change', function(e) {
        if (e.target.matches('select[name$="-chapter_type"]') ||
            e.target.matches('select[name$="-content_format"]')) {
            refreshChapterRow(getContainer(e.target));
        }
    });

    document.querySelectorAll('.inline-related').forEach(refreshChapterRow);

    if (window.django && window.django.jQuery) {
        window.django.jQuery(document).on('formset:added', function(event, $row) {
            refreshChapterRow($row[0]);
        });
    }
});
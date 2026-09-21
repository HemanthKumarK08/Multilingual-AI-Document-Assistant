import React from 'react';

/**
 * Safe, zero-dependency Markdown renderer.
 * Converts markdown text into structured React elements without dangerouslySetInnerHTML.
 */
export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const elements = [];
  let inCodeBlock = false;
  let codeBlockLines = [];
  let currentList = [];
  let listType = null; // 'ul' or 'ol'

  function flushList() {
    if (currentList.length > 0) {
      if (listType === 'ol') {
        elements.push(
          <ol key={`ol-${elements.length}`} className="list-decimal list-inside space-y-1 my-2 text-gray-200">
            {currentList.map((item, idx) => (
              <li key={idx}>{renderFormattedText(item)}</li>
            ))}
          </ol>
        );
      } else {
        elements.push(
          <ul key={`ul-${elements.length}`} className="list-disc list-inside space-y-1 my-2 text-gray-200">
            {currentList.map((item, idx) => (
              <li key={idx}>{renderFormattedText(item)}</li>
            ))}
          </ul>
        );
      }
      currentList = [];
      listType = null;
    }
  }

  function renderFormattedText(text) {
    // Process bold (**text**) and inline code (`code`)
    const parts = [];
    const regex = /(\*\*.*?\*\*|`.*?`)/g;
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={`b-${match.index}`} className="font-bold text-white">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={`c-${match.index}`}
            className="px-1.5 py-0.5 rounded bg-surface-base font-mono text-xs text-brand-300 border border-surface-border"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code blocks (```)
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`pre-${elements.length}`}
            className="p-3 my-2 rounded-xl bg-surface-base border border-surface-border text-xs font-mono text-brand-300 overflow-x-auto"
          >
            <code>{codeBlockLines.join('\n')}</code>
          </pre>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        flushList();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      continue;
    }

    // Empty line
    if (!line.trim()) {
      flushList();
      continue;
    }

    // Headings (#, ##, ###)
    if (line.startsWith('### ')) {
      flushList();
      elements.push(
        <h4 key={`h4-${elements.length}`} className="text-sm font-bold text-white mt-3 mb-1">
          {renderFormattedText(line.slice(4))}
        </h4>
      );
      continue;
    }
    if (line.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${elements.length}`} className="text-base font-bold text-white mt-4 mb-1.5">
          {renderFormattedText(line.slice(3))}
        </h3>
      );
      continue;
    }
    if (line.startsWith('# ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${elements.length}`} className="text-lg font-extrabold text-white mt-4 mb-2">
          {renderFormattedText(line.slice(2))}
        </h2>
      );
      continue;
    }

    // Unordered lists (- or *)
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      if (listType === 'ol') flushList();
      listType = 'ul';
      currentList.push(line.trim().slice(2));
      continue;
    }

    // Ordered lists (1. 2. etc)
    const olMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
    if (olMatch) {
      if (listType === 'ul') flushList();
      listType = 'ol';
      currentList.push(olMatch[2]);
      continue;
    }

    // Regular paragraph
    flushList();
    elements.push(
      <p key={`p-${elements.length}`} className="text-sm text-gray-200 leading-relaxed my-1.5">
        {renderFormattedText(line)}
      </p>
    );
  }

  flushList();

  return <div className="space-y-1 text-sm">{elements}</div>;
}

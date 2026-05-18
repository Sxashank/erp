/**
 * Text/Markdown Widget - displays static text or markdown content
 */

import type { TextMarkdownConfig } from '@/types/bi';

interface TextMarkdownWidgetProps {
  config: TextMarkdownConfig;
}

export function TextMarkdownWidget({ config }: TextMarkdownWidgetProps) {
  // Simple markdown-like parsing (basic support)
  const parseContent = (content: string) => {
    // Split by lines and process
    const lines = content.split('\n');

    return lines.map((line, index) => {
      // Headers
      if (line.startsWith('### ')) {
        return (
          <h3 key={index} className="text-lg font-semibold mt-4 mb-2">
            {line.slice(4)}
          </h3>
        );
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={index} className="text-xl font-semibold mt-4 mb-2">
            {line.slice(3)}
          </h2>
        );
      }
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className="text-2xl font-bold mt-4 mb-2">
            {line.slice(2)}
          </h1>
        );
      }

      // List items
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return (
          <li key={index} className="ml-4">
            {parseLine(line.slice(2))}
          </li>
        );
      }

      // Numbered list
      const numberedMatch = line.match(/^\d+\. /);
      if (numberedMatch) {
        return (
          <li key={index} className="ml-4 list-decimal">
            {parseLine(line.slice(numberedMatch[0].length))}
          </li>
        );
      }

      // Empty line
      if (line.trim() === '') {
        return <br key={index} />;
      }

      // Regular paragraph
      return (
        <p key={index} className="mb-2">
          {parseLine(line)}
        </p>
      );
    });
  };

  // Parse inline formatting (bold, italic, code)
  const parseLine = (text: string) => {
    // Replace **bold** with <strong>
    let parts: (string | JSX.Element)[] = [text];

    // Bold
    parts = parts.flatMap((part, i) => {
      if (typeof part !== 'string') return part;
      const boldParts = part.split(/\*\*(.+?)\*\*/g);
      return boldParts.map((p, j) =>
        j % 2 === 1 ? <strong key={`${i}-${j}`}>{p}</strong> : p
      );
    });

    // Italic
    parts = parts.flatMap((part, i) => {
      if (typeof part !== 'string') return part;
      const italicParts = part.split(/\*(.+?)\*/g);
      return italicParts.map((p, j) =>
        j % 2 === 1 ? <em key={`${i}-it-${j}`}>{p}</em> : p
      );
    });

    // Code
    parts = parts.flatMap((part, i) => {
      if (typeof part !== 'string') return part;
      const codeParts = part.split(/`(.+?)`/g);
      return codeParts.map((p, j) =>
        j % 2 === 1 ? (
          <code key={`${i}-code-${j}`} className="bg-muted px-1 rounded text-sm">
            {p}
          </code>
        ) : (
          p
        )
      );
    });

    return parts;
  };

  return (
    <div className="h-full w-full p-4 overflow-auto prose prose-sm max-w-none">
      {parseContent(config.content || '')}
    </div>
  );
}

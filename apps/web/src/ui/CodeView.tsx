import { useEffect, useRef, useState } from "react";

type Token = { content: string; color?: string };

let highlighter: Promise<(code: string, lang: string) => Token[][]> | null = null;

function getHighlighter() {
  highlighter ??= (async () => {
    const [{ createHighlighterCore }, { createJavaScriptRegexEngine }, csharp, sql, theme] = await Promise.all([
      import("shiki/core"),
      import("shiki/engine/javascript"),
      import("shiki/langs/csharp.mjs"),
      import("shiki/langs/sql.mjs"),
      import("shiki/themes/github-light.mjs"),
    ]);
    const core = await createHighlighterCore({
      engine: createJavaScriptRegexEngine({ forgiving: true }),
      langs: [csharp.default, sql.default],
      themes: [theme.default],
    });
    return (code: string, lang: string) => core.codeToTokensBase(code, { lang, theme: "github-light" });
  })();
  return highlighter;
}

type Props = { source: string; focusLine?: number };

// Read-only source with line numbers. Citations scroll to and mark their exact line.
export function CodeView({ source, focusLine }: Props) {
  const plain: Token[][] = source.split("\n").map((line) => [{ content: line }]);
  const [lines, setLines] = useState<Token[][]>(plain);
  const focusRef = useRef<HTMLDivElement>(null);
  const lang = source.startsWith("--") ? "sql" : "csharp";

  useEffect(() => {
    let live = true;
    getHighlighter()
      .then((highlight) => live && setLines(highlight(source, lang)))
      .catch(() => undefined); // Plain text is a fine fallback on stage.
    return () => {
      live = false;
    };
  }, [source, lang]);

  useEffect(() => {
    focusRef.current?.scrollIntoView({ block: "center" });
  }, [focusLine, lines]);

  return (
    <div className="py-3 font-mono text-[14px] leading-6">
      {lines.map((tokens, index) => {
        const number = index + 1;
        const focused = number === focusLine;
        return (
          <div
            key={number}
            ref={focused ? focusRef : undefined}
            className={`flex pr-6 ${focused ? "bg-warn-soft shadow-[inset_3px_0_0_var(--warn)]" : ""}`}
          >
            <span className="w-14 shrink-0 pr-4 text-right text-ink-3 select-none">{number}</span>
            <span className="whitespace-pre-wrap">
              {tokens.map((token, i) => (
                <span key={i} style={{ color: token.color }}>
                  {token.content}
                </span>
              ))}
            </span>
          </div>
        );
      })}
    </div>
  );
}

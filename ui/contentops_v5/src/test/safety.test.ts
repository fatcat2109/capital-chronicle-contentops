// Capital Chronicle ContentOps V5 — static + runtime safety guards.
//
// This suite enforces the V5 north-star invariants:
//   * all five flagship views are present and routable
//   * Evidence Vault forces dark-evidence mode
//   * dispatch/publish controls are disabled / future-gated
//   * AI Writer + SEO panels are UI-only / review-only
//   * Media Tray is mock-only (no file picker / upload / read)
//   * runtime network is restricted to the explicit loopback Daily App API
//   * NO localStorage / sessionStorage
//   * NO process.env / .env / credential reads
//   * NO CDN / remote font / external image / Material Symbols
//   * NO scheduler / posting / scraping / platform|provider API behavior
//
// IMPORTANT: the forbidden tokens legitimately appear inside human-readable
// safety copy (comments + fixture strings). A naive substring scan would
// false-positive on that descriptive text. So the static scan strips line
// comments, block comments, and string/template literals and asserts only
// against *executable* code.

import { describe, expect, it, beforeAll } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createElement } from 'react';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import App from '../App';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC_ROOT = resolve(HERE, '..');

// ---------------------------------------------------------------------------
// Source collection helpers
// ---------------------------------------------------------------------------

function collectSourceFiles(root: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(root)) {
    // Test files are not part of the shipped runtime bundle. They legitimately
    // contain the forbidden-token regex literals used by this scan, so they are
    // excluded to avoid self-matching.
    if (entry === 'test') continue;
    const full = join(root, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      out.push(...collectSourceFiles(full));
    } else if (/\.(ts|tsx|css|html)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

/**
 * Strip line comments, block comments, and string/template literals so the
 * forbidden-token scan only sees executable code, not safety copy.
 */
function stripCommentsAndStrings(code: string): string {
  let out = '';
  let i = 0;
  const n = code.length;
  let state:
    | 'code'
    | 'line'
    | 'block'
    | 'single'
    | 'double'
    | 'template' = 'code';

  while (i < n) {
    const c = code[i];
    const next = code[i + 1];

    if (state === 'code') {
      if (c === '/' && next === '/') {
        state = 'line';
        i += 2;
      } else if (c === '/' && next === '*') {
        state = 'block';
        i += 2;
      } else if (c === "'") {
        state = 'single';
        i += 1;
      } else if (c === '"') {
        state = 'double';
        i += 1;
      } else if (c === '`') {
        state = 'template';
        i += 1;
      } else {
        out += c;
        i += 1;
      }
    } else if (state === 'line') {
      if (c === '\n') {
        state = 'code';
        out += c;
      }
      i += 1;
    } else if (state === 'block') {
      if (c === '*' && next === '/') {
        state = 'code';
        i += 2;
      } else {
        i += 1;
      }
    } else if (state === 'single') {
      if (c === '\\') i += 2;
      else if (c === "'") {
        state = 'code';
        i += 1;
      } else i += 1;
    } else if (state === 'double') {
      if (c === '\\') i += 2;
      else if (c === '"') {
        state = 'code';
        i += 1;
      } else i += 1;
    } else if (state === 'template') {
      if (c === '\\') i += 2;
      else if (c === '`') {
        state = 'code';
        i += 1;
      } else i += 1;
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Static source scan
// ---------------------------------------------------------------------------

interface ScannedFile {
  path: string;
  raw: string;
  code: string; // comments + strings stripped
}

let files: ScannedFile[] = [];

beforeAll(() => {
  files = collectSourceFiles(SRC_ROOT).map((path) => {
    const raw = readFileSync(path, 'utf8');
    return { path, raw, code: stripCommentsAndStrings(raw) };
  });
});

// Forbidden *executable* behaviors. Matched against stripped code only.
const FORBIDDEN_CODE_PATTERNS: { label: string; re: RegExp }[] = [
  { label: 'XMLHttpRequest', re: /\bXMLHttpRequest\b/ },
  { label: 'WebSocket', re: /\bnew\s+WebSocket\b/ },
  { label: 'EventSource', re: /\bnew\s+EventSource\b/ },
  { label: 'sendBeacon', re: /\bsendBeacon\b/ },
  { label: 'localStorage', re: /\blocalStorage\b/ },
  { label: 'sessionStorage', re: /\bsessionStorage\b/ },
  { label: 'indexedDB', re: /\bindexedDB\b/ },
  { label: 'process.env', re: /\bprocess\s*\.\s*env\b/ },
  { label: 'import.meta.env', re: /\bimport\s*\.\s*meta\s*\.\s*env\b/ },
  { label: 'navigator.sendBeacon', re: /\bnavigator\s*\.\s*sendBeacon\b/ },
  { label: '<input type=file> (file picker)', re: /type\s*=\s*.?file/ },
  { label: 'FileReader', re: /\bnew\s+FileReader\b/ },
];

// Forbidden runtime asset references. These are checked against the RAW text
// (we DO want to catch them inside href/src/url() strings), but only flagged
// when they look like real remote references rather than negated safety copy.
const FORBIDDEN_ASSET_PATTERNS: { label: string; re: RegExp }[] = [
  { label: 'cdn.tailwindcss.com', re: /cdn\.tailwindcss\.com/ },
  { label: 'fonts.googleapis.com', re: /fonts\.googleapis\.com/ },
  { label: 'fonts.gstatic.com', re: /fonts\.gstatic\.com/ },
  { label: 'googleusercontent image host', re: /googleusercontent\.com/ },
  { label: 'Material Symbols font link', re: /Material\+?Symbols/ },
];

describe('V5 static safety scan (executable code)', () => {
  it('collects V5 source files', () => {
    expect(files.length).toBeGreaterThan(8);
  });

  for (const { label, re } of FORBIDDEN_CODE_PATTERNS) {
    it(`has no executable use of ${label}`, () => {
      const hits = files.filter((f) => re.test(f.code));
      expect(
        hits.map((h) => h.path),
        `Forbidden executable pattern ${label} found in: ${hits
          .map((h) => h.path)
          .join(', ')}`,
      ).toEqual([]);
    });
  }
});

describe('Final Daily App local API boundary', () => {
  it('restricts production fetches to the explicit loopback API module', () => {
    const fetchFiles = files.filter((f) => /\bfetch\s*\(/.test(f.code));
    expect(fetchFiles.map((f) => f.path.replace(/\\/g, '/'))).toEqual([
      expect.stringMatching(/src\/views\/DailyAppConsole\.tsx$/),
    ]);
    const consoleSource = fetchFiles[0].raw;
    expect(consoleSource).toContain("const API_ROOT = 'http://127.0.0.1:5174'");
    expect(consoleSource).not.toContain('/api/run-pipeline');
    expect(consoleSource).not.toMatch(/Math\.random|handleManualPost|handleSimulateDispatch|automationActive/);
  });
});

describe('V5 static safety scan (remote asset references)', () => {
  for (const { label, re } of FORBIDDEN_ASSET_PATTERNS) {
    it(`has no remote reference to ${label}`, () => {
      // Allow the literal token inside a comment/string ONLY if it is part of
      // explicit "no <token>" negated safety copy. We catch genuine markup by
      // scanning stripped code AND href/src attributes in raw html/tsx.
      const assetHits = files.filter((f) => {
        if (/\.(html|tsx|ts)$/.test(f.path)) {
          // Genuine usage looks like url(...), href="...", src="..." with the host.
          const usageRe = new RegExp(
            `(href|src|url\\()[^)"']*${re.source}`,
          );
          return usageRe.test(f.raw);
        }
        return re.test(f.code);
      });
      expect(
        assetHits.map((h) => h.path),
        `Remote asset ${label} referenced in: ${assetHits
          .map((h) => h.path)
          .join(', ')}`,
      ).toEqual([]);
    });
  }

  it('imports fonts only from the bundled @fontsource package', () => {
    const cssOrEntry = files.filter((f) =>
      /(index\.css|main\.tsx)$/.test(f.path),
    );
    const fontImports = cssOrEntry.flatMap((f) =>
      (f.raw.match(/@fontsource[^"';]+/g) ?? []).map((m) => m.trim()),
    );
    expect(fontImports.length).toBeGreaterThan(0);
    // No http(s) font URLs anywhere in those entry files.
    for (const f of cssOrEntry) {
      expect(/@import\s+url\(\s*['"]?https?:/.test(f.raw)).toBe(false);
    }
  });
});

// ---------------------------------------------------------------------------
// Runtime / DOM behavioral guards
// ---------------------------------------------------------------------------

const VIEW_NAV = [
  { id: 'nav-command_center', heading: /command center/i },
  { id: 'nav-content_inventory', heading: /content inventory/i },
  { id: 'nav-writer_studio', heading: /writer studio/i },
  { id: 'nav-approval_queue', heading: /approval/i },
  { id: 'nav-evidence_vault', heading: /evidence vault/i },
];

describe('V5 view routing', () => {
  it('exposes all five flagship views as routable nav items', () => {
    render(createElement(App));
    for (const { id } of VIEW_NAV) {
      expect(document.getElementById(id)).toBeInTheDocument();
    }
  });

  for (const { id, heading } of VIEW_NAV) {
    it(`routes to ${id} and renders its heading`, () => {
      render(createElement(App));
      fireEvent.click(document.getElementById(id)!);
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
        heading,
      );
    });
  }
});

describe('V5 Evidence Vault theme invariant', () => {
  it('forces dark-evidence mode and disables the theme toggle', () => {
    const { container } = render(createElement(App));
    fireEvent.click(document.getElementById('nav-evidence_vault')!);
    const root = container.querySelector('[data-theme]') as HTMLElement;
    expect(root.getAttribute('data-theme')).toBe('dark-evidence');
    const toggle = document.getElementById('theme-toggle') as HTMLButtonElement;
    expect(toggle).toBeDisabled();
  });
});

describe('V5 dispatch / publish is disabled and future-gated', () => {
  it('renders a disabled dispatch action with a future-gated reason', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-approval_queue')!);
    // The locked dispatch action is a disabled button.
    const disabledButtons = screen
      .getAllByRole('button')
      .filter((b) => (b as HTMLButtonElement).disabled);
    expect(disabledButtons.length).toBeGreaterThan(0);
    expect(screen.getByText(/dispatch disabled/i)).toBeInTheDocument();
    // "future-gated" appears on the panel chip AND the locked-action reason.
    expect(screen.getAllByText(/future-gated/i).length).toBeGreaterThan(0);
    // No enabled control mentions live posting / scheduling.
    const enabled = screen
      .getAllByRole('button')
      .filter((b) => !(b as HTMLButtonElement).disabled);
    for (const b of enabled) {
      expect(b.textContent ?? '').not.toMatch(/post now|publish now|schedule/i);
    }
  });
});

describe('V5 Writer Studio AI + SEO are UI-only / review-only', () => {
  it('labels AI Writer UI-only and marks variants not publish-ready', () => {
    render(createElement(App));
    fireEvent.click(document.getElementById('nav-writer_studio')!);
    expect(screen.getByText('AI Writer')).toBeInTheDocument();
    expect(screen.getAllByText(/ui-only/i).length).toBeGreaterThan(0);
    // "review only" appears on the verdict chip AND the view's REVIEW ONLY chip.
    expect(screen.getAllByText(/review only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/publish_ready: false/i).length).toBeGreaterThan(
      0,
    );
    // SEO panel is advisory only.
    expect(screen.getByText(/SEO & Editorial Score/i)).toBeInTheDocument();
    expect(screen.getByText(/advisory/i)).toBeInTheDocument();
  });

  it('renders the Media Tray as mock-only with no file input', () => {
    const { container } = render(createElement(App));
    fireEvent.click(document.getElementById('nav-writer_studio')!);
    expect(screen.getByText('Media Tray')).toBeInTheDocument();
    expect(screen.getAllByText(/mock only/i).length).toBeGreaterThan(0);
    // No real file picker anywhere in the rendered tray.
    expect(container.querySelector('input[type="file"]')).toBeNull();
  });
});

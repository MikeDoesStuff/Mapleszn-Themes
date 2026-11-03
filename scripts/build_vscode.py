"""Build the VS Code / Open VSX extension from themes/*.json.

Run from the repo root:  python3 scripts/build_vscode.py
Then package:            cd vscode && npx @vscode/vsce@3.2.1 package
"""
import json, math, glob, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "vscode")
VERSION = "0.1.0"

# ---------- colour helpers (OKLCH) ----------
def s2l(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def l2s(c): return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def to_oklch(h):
    r, g, b = [s2l(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360
def ok(L, C, H):
    a = C * math.cos(math.radians(H)); b = C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s]
    return "#" + "".join(f"{max(0, min(255, round(l2s(max(0, min(1, x))) * 255))):02X}" for x in rgb)
def lum(h):
    r, g, b = [s2l(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
def cr(a, b):
    x, y = lum(a), lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)
def harm(target, source, amt=20):
    d = ((source - target + 180) % 360) - 180
    return (target + max(-amt, min(amt, d * 0.5))) % 360
def alpha(h, a): return h + f"{round(a * 255):02X}"

def readable(L, C, H, bg, dark, minimum):
    """Walk lightness away from the background until the colour reaches `minimum` contrast."""
    for _ in range(80):
        col = ok(L, C, H)
        if cr(col, bg) >= minimum: return col
        L += 0.005 if dark else -0.005
    return col

# ---------- syntax palette ----------
def syntax(c, dark):
    bg = c["canvas"]
    _, ac, ah = to_oklch(c["accent"])
    _, nc, nh = to_oklch(bg)
    L0 = 0.78 if dark else 0.50
    C0 = 0.11 if dark else 0.14
    p = lambda hue, L=L0, C=C0, m=4.5: readable(L, C, hue % 360, bg, dark, m)
    return {
        "keyword":  p(ah, C=max(ac, 0.10)),
        "function": p(harm(250, ah + 180, 25)),
        "string":   p(harm(140, ah)),
        "type":     p(harm(85, ah), L=L0 + (0.04 if dark else -0.02)),
        "number":   p(harm(55, ah)),
        "constant": p(harm(320, ah)),
        "tag":      p(harm(20, ah)),
        "property": p(harm(200, ah), C=C0 * 0.8),
        "regexp":   p(harm(180, ah)),
        "comment":  readable(0.62 if dark else 0.58, nc * 2.5, nh, bg, dark, 3.6),
        "punct":    readable(0.70 if dark else 0.50, nc * 2, nh, bg, dark, 4.5),
        "variable": c["text"],
    }

def token_colors(s):
    T = lambda scope, key, style=None: {"scope": scope, "settings": {"foreground": s[key], **({"fontStyle": style} if style else {})}}
    return [
        T(["comment", "punctuation.definition.comment", "string.comment"], "comment", "italic"),
        T(["keyword", "storage.type", "storage.modifier", "keyword.control", "keyword.operator.new", "keyword.operator.expression", "keyword.operator.logical"], "keyword"),
        T(["keyword.operator", "punctuation", "meta.brace", "punctuation.separator", "punctuation.terminator"], "punct"),
        T(["entity.name.function", "support.function", "meta.function-call entity.name.function", "variable.function"], "function"),
        T(["entity.name.type", "entity.name.class", "support.type", "support.class", "entity.other.inherited-class", "storage.type.primitive", "entity.name.namespace"], "type"),
        T(["string", "string.template", "punctuation.definition.string"], "string"),
        T(["punctuation.definition.template-expression", "punctuation.section.embedded"], "keyword"),
        T(["string.regexp", "constant.character.escape"], "regexp"),
        T(["constant.numeric", "constant.language.boolean"], "number"),
        T(["constant", "constant.language", "support.constant", "variable.other.constant", "variable.other.enummember"], "constant"),
        T(["entity.name.tag", "meta.tag.sgml"], "tag"),
        T(["entity.other.attribute-name", "variable.other.property", "variable.other.object.property", "support.type.property-name", "meta.object-literal.key"], "property"),
        T(["variable", "variable.parameter", "meta.definition.variable"], "variable"),
        T(["variable.language", "variable.language.this"], "keyword", "italic"),
        T(["markup.heading", "entity.name.section"], "keyword", "bold"),
        T(["markup.bold"], "type", "bold"),
        T(["markup.italic"], "constant", "italic"),
        T(["markup.inline.raw", "markup.fenced_code"], "string"),
        T(["markup.underline.link", "string.other.link"], "function"),
        T(["markup.inserted"], "string"),
        T(["markup.deleted"], "tag"),
        T(["invalid"], "tag"),
    ]

def semantic(s):
    return {
        "function": s["function"], "method": s["function"], "class": s["type"], "interface": s["type"],
        "type": s["type"], "enum": s["type"], "typeParameter": s["type"], "namespace": s["type"],
        "property": s["property"], "enumMember": s["constant"], "parameter": s["variable"],
        "variable.readonly": s["constant"], "keyword": s["keyword"], "string": s["string"],
        "number": s["number"], "regexp": s["regexp"], "comment": {"foreground": s["comment"], "italic": True},
    }

# ---------- workbench colours ----------
def workbench(c, s, dark):
    link = c["accent"] if cr(c["accent"], c["canvas"]) >= 4.5 else c["accentSurfaceForeground"]
    ansi = {
        "Black": c["sidebar"] if dark else c["text"], "Red": s["tag"], "Green": s["string"], "Yellow": s["type"],
        "Blue": s["function"], "Magenta": s["constant"], "Cyan": s["regexp"], "White": c["textMuted"] if dark else c["border"],
    }
    bright = {k: v for k, v in ansi.items()}
    bright["Black"] = c["placeholder"]; bright["White"] = c["text"] if dark else c["textMuted"]
    w = {
        # t3code import reads these first
        "editor.background": c["canvas"], "editor.foreground": c["text"], "foreground": c["text"],
        "focusBorder": c["accent"], "button.background": c["messageAction"], "button.foreground": c["messageActionForeground"],
        "button.hoverBackground": c["messageActionHover"], "textLink.foreground": link, "textLink.activeForeground": c["accentSurfaceForeground"],
        "editorWidget.background": c["surfaceRaised"], "editorWidget.border": c["border"],
        "dropdown.background": c["surfaceRaised"], "dropdown.border": c["border"], "dropdown.foreground": c["text"],
        "menu.background": c["surfaceOverlay"], "menu.foreground": c["text"], "menu.selectionBackground": c["accentSurface"],
        "menu.selectionForeground": c["accentSurfaceForeground"], "menu.border": c["border"],
        "quickInput.background": c["surfaceOverlay"], "quickInput.foreground": c["text"],
        "quickInputList.focusBackground": c["accentSurface"], "quickInputList.focusForeground": c["accentSurfaceForeground"],
        "panel.border": c["border"], "editorGroup.border": c["border"], "contrastBorder": alpha(c["border"], 0),
        "input.background": c["surfaceOverlay"], "input.border": c["input"], "input.foreground": c["text"],
        "input.placeholderForeground": c["placeholder"],
        "editorError.foreground": c["error"], "errorForeground": c["errorForeground"], "editorWarning.foreground": c["warning"],
        "editorInfo.foreground": c["update"],
        "list.activeSelectionBackground": c["sidebarRowSelected"], "list.activeSelectionForeground": c["sidebarForeground"],
        "list.inactiveSelectionBackground": c["sidebarRowActive"], "list.hoverBackground": c["sidebarRowHover"],
        "list.focusOutline": c["focus"], "list.highlightForeground": link,
        "textCodeBlock.background": c["codeBackground"],
        "sideBar.background": c["sidebar"], "sideBar.foreground": c["sidebarForeground"], "sideBar.border": c["sidebarBorder"],
        "sideBarTitle.foreground": c["sidebarMutedForeground"], "sideBarSectionHeader.background": c["sidebar"],
        "sideBarSectionHeader.foreground": c["sidebarMutedForeground"], "sideBarSectionHeader.border": c["sidebarBorder"],
        "activityBar.background": c["sidebar"], "activityBar.foreground": c["text"], "activityBar.inactiveForeground": c["iconMuted"],
        "activityBar.border": c["sidebarBorder"], "activityBar.activeBorder": c["accent"],
        "activityBarBadge.background": c["accent"], "activityBarBadge.foreground": c["accentForeground"],
        "badge.background": c["accentSurface"], "badge.foreground": c["accentSurfaceForeground"],
        "progressBar.background": c["accent"],
        "terminal.background": c["terminalBackground"], "terminal.foreground": c["terminalForeground"],
        "terminalCursor.foreground": c["terminalCursor"], "terminal.selectionBackground": c["terminalSelection"],
        "panel.background": c["terminalBackground"], "panelTitle.activeForeground": c["text"],
        "panelTitle.inactiveForeground": c["textMuted"], "panelTitle.activeBorder": c["accent"],
        "scrollbarSlider.background": alpha(c["terminalScrollbar"], 0.6), "scrollbarSlider.hoverBackground": alpha(c["terminalScrollbarHover"], 0.8),
        "scrollbarSlider.activeBackground": c["terminalScrollbarHover"],
        "editor.findMatchBackground": alpha(c["warning"], 0.45), "editor.findMatchHighlightBackground": alpha(c["warning"], 0.22),
        # rest of the workbench
        "descriptionForeground": c["textMuted"], "icon.foreground": c["iconMuted"], "widget.border": c["border"],
        "selection.background": c["terminalSelection"],
        "titleBar.activeBackground": c["toolbar"], "titleBar.activeForeground": c["toolbarForeground"],
        "titleBar.inactiveBackground": c["toolbar"], "titleBar.inactiveForeground": c["textMuted"], "titleBar.border": c["toolbarBorder"],
        "statusBar.background": c["sidebar"], "statusBar.foreground": c["sidebarMutedForeground"], "statusBar.border": c["sidebarBorder"],
        "statusBar.noFolderBackground": c["sidebar"], "statusBar.debuggingBackground": c["warningSurface"],
        "statusBar.debuggingForeground": c["warningForeground"], "statusBarItem.remoteBackground": c["accent"],
        "statusBarItem.remoteForeground": c["accentForeground"], "statusBarItem.hoverBackground": c["sidebarRowHover"],
        "editorGroupHeader.tabsBackground": c["sidebar"], "editorGroupHeader.tabsBorder": c["sidebarBorder"],
        "tab.activeBackground": c["canvas"], "tab.activeForeground": c["text"], "tab.activeBorderTop": c["accent"],
        "tab.inactiveBackground": c["sidebar"], "tab.inactiveForeground": c["textMuted"], "tab.border": c["sidebarBorder"],
        "tab.hoverBackground": c["sidebarRowHover"], "breadcrumb.foreground": c["textMuted"], "breadcrumb.focusForeground": c["text"],
        "editor.lineHighlightBackground": c["surface"], "editor.lineHighlightBorder": alpha(c["surface"], 0),
        "editor.selectionBackground": c["terminalSelection"], "editor.inactiveSelectionBackground": alpha(c["terminalSelection"], 0.6),
        "editor.selectionHighlightBackground": alpha(c["accentSurface"], 0.7), "editor.wordHighlightBackground": alpha(c["accentSurface"], 0.6),
        "editorCursor.foreground": c["terminalCursor"], "editorLineNumber.foreground": c["placeholder"],
        "editorLineNumber.activeForeground": c["textMuted"], "editorIndentGuide.background1": alpha(c["border"], 0.5),
        "editorIndentGuide.activeBackground1": c["border"], "editorWhitespace.foreground": alpha(c["border"], 0.6),
        "editorBracketMatch.background": alpha(c["accentSurface"], 0.8), "editorBracketMatch.border": alpha(c["accent"], 0.6),
        "editorGutter.addedBackground": s["string"], "editorGutter.modifiedBackground": s["function"], "editorGutter.deletedBackground": s["tag"],
        "diffEditor.insertedTextBackground": alpha(s["string"], 0.18), "diffEditor.removedTextBackground": alpha(s["tag"], 0.18),
        "diffEditor.insertedLineBackground": alpha(s["string"], 0.10), "diffEditor.removedLineBackground": alpha(s["tag"], 0.10),
        "gitDecoration.addedResourceForeground": s["string"], "gitDecoration.modifiedResourceForeground": s["type"],
        "gitDecoration.deletedResourceForeground": s["tag"], "gitDecoration.untrackedResourceForeground": s["string"],
        "gitDecoration.ignoredResourceForeground": c["placeholder"], "gitDecoration.conflictingResourceForeground": s["constant"],
        "notifications.background": c["surfaceRaised"], "notifications.foreground": c["text"], "notifications.border": c["border"],
        "peekView.border": c["accent"], "peekViewEditor.background": c["surface"], "peekViewResult.background": c["sidebar"],
        "peekViewTitle.background": c["surfaceRaised"],
        "checkbox.background": c["surfaceOverlay"], "checkbox.border": c["input"],
        "button.secondaryBackground": c["secondary"], "button.secondaryForeground": c["secondaryForeground"],
        "button.secondaryHoverBackground": c["toolbarControlHover"],
        "minimap.background": c["canvas"], "editorOverviewRuler.border": alpha(c["border"], 0),
    }
    for k, v in ansi.items(): w[f"terminal.ansi{k}"] = v
    for k, v in bright.items(): w[f"terminal.ansiBright{k}"] = v
    return w

def vscode_theme(t, mode):
    dark = mode == "dark"
    c = t["colors"] if (t["appearance"] == mode) else t["variants"][mode]
    s = syntax(c, dark)
    return {
        "$schema": "vscode://schemas/color-theme",
        "name": f"{t['name']} {'Dark' if dark else 'Light'}",
        "type": mode,
        "semanticHighlighting": True,
        "colors": workbench(c, s, dark),
        "tokenColors": token_colors(s),
        "semanticTokenColors": semantic(s),
    }

def main():
    order = ["maple-frost", "maple-momiji", "maple-dusk", "maple-sugar",
             "maple-ember", "maple-cinder", "maple-oat", "maple-mist", "maple-twilight"]
    tdir = os.path.join(OUT, "themes")
    shutil.rmtree(tdir, ignore_errors=True); os.makedirs(tdir)
    contributes = []
    for tid in order:
        t = json.load(open(os.path.join(ROOT, "themes", f"{tid}.json")))
        for mode in ("dark", "light"):
            vt = vscode_theme(t, mode)
            fn = f"{tid}-{mode}.json"
            json.dump(vt, open(os.path.join(tdir, fn), "w"), indent=2)
            contributes.append({"label": vt["name"], "uiTheme": "vs-dark" if mode == "dark" else "vs", "path": f"./themes/{fn}"})
    pkg = {
        "name": "mapleszn-themes",
        "displayName": "Mapleszn",
        "description": "Maple-season dark and light themes: warm leaf accents on cool grey bases. Made for t3code, works in VS Code.",
        "version": VERSION,
        "publisher": "mikedoesstuff",
        "author": {"name": "MikeDoesStuff"},
        "license": "MIT",
        "repository": {"type": "git", "url": "https://github.com/MikeDoesStuff/Mapleszn-Themes"},
        "homepage": "https://github.com/MikeDoesStuff/Mapleszn-Themes",
        "bugs": {"url": "https://github.com/MikeDoesStuff/Mapleszn-Themes/issues"},
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Themes"],
        "keywords": ["theme", "maple", "autumn", "dark", "light", "t3code"],
        "galleryBanner": {"color": "#2B323B", "theme": "dark"},
        "contributes": {"themes": contributes},
    }
    json.dump(pkg, open(os.path.join(OUT, "package.json"), "w"), indent=2)
    shutil.copy(os.path.join(ROOT, "LICENSE"), os.path.join(OUT, "LICENSE"))
    # contrast report
    for f in sorted(glob.glob(os.path.join(tdir, "*.json"))):
        vt = json.load(open(f)); bg = vt["colors"]["editor.background"]
        worst = min((cr(r["settings"]["foreground"], bg), r["scope"][0]) for r in vt["tokenColors"])
        print(f"{vt['name']:22} worst token {worst[0]:.1f} ({worst[1]})")

if __name__ == "__main__":
    main()

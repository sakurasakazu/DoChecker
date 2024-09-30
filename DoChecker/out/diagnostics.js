"use strict";
/** To demonstrate code actions associated with Diagnostics problems, this file provides a mock diagnostics entries. */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.EMOJI_MENTION = void 0;
exports.refreshDiagnostics = refreshDiagnostics;
exports.subscribeToDocumentChanges = subscribeToDocumentChanges;
const vscode = __importStar(require("vscode"));
/** Code that is used to associate diagnostic entries with code actions. */
exports.EMOJI_MENTION = 'emoji_mention';
/** String to detect in the text document. */
const EMOJI = 'emoji';
/**
 * Analyzes the text document for problems.
 * This demo diagnostic problem provider finds all mentions of 'emoji'.
 * @param doc text document to analyze
 * @param emojiDiagnostics diagnostic collection
 */
function refreshDiagnostics(doc, emojiDiagnostics) {
    const diagnostics = [];
    for (let lineIndex = 0; lineIndex < doc.lineCount; lineIndex++) {
        const lineOfText = doc.lineAt(lineIndex);
        if (lineOfText.text.includes(EMOJI)) {
            diagnostics.push(createDiagnostic(doc, lineOfText, lineIndex));
        }
    }
    emojiDiagnostics.set(doc.uri, diagnostics);
}
function createDiagnostic(doc, lineOfText, lineIndex) {
    // find where in the line of that the 'emoji' is mentioned
    const index = lineOfText.text.indexOf(EMOJI);
    // create range that represents, where in the document the word is
    const range = new vscode.Range(lineIndex, index, lineIndex, index + EMOJI.length);
    const diagnostic = new vscode.Diagnostic(range, "When you say 'emoji', do you want to find out more?", vscode.DiagnosticSeverity.Information);
    diagnostic.code = exports.EMOJI_MENTION;
    return diagnostic;
}
function subscribeToDocumentChanges(context, emojiDiagnostics) {
    if (vscode.window.activeTextEditor) {
        refreshDiagnostics(vscode.window.activeTextEditor.document, emojiDiagnostics);
    }
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
            refreshDiagnostics(editor.document, emojiDiagnostics);
        }
    }));
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(e => refreshDiagnostics(e.document, emojiDiagnostics)));
    context.subscriptions.push(vscode.workspace.onDidCloseTextDocument(doc => emojiDiagnostics.delete(doc.uri)));
}
//# sourceMappingURL=diagnostics.js.map
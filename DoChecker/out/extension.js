"use strict";
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
exports.Checker = void 0;
exports.activate = activate;
const vscode = __importStar(require("vscode"));
const python_shell_1 = require("python-shell");
function activate(context) {
    let checker = new Checker();
    // アクティブエディタが変更されたときに実行
    vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor) {
            const activetype = editor.document.languageId;
            const text = editor.document.getText();
            if (activetype == "dockerfile") {
                //データはjsonで渡してjsonでもらう
                let sendData = {
                    "data": text
                };
                checker.execPython(JSON.stringify(sendData));
                setTimeout(() => {
                    checker.clearDiagList();
                    let data;
                    while (checker._pythonRes == "") {
                    }
                    data = JSON.parse(checker._pythonRes);
                    for (const v of data) {
                        let diag = checker.createDiag(editor.document, v['position_start'], v['position_end'], v['message']);
                        if (diag) {
                            checker.pushDiagList(diag);
                            checker.setDiag(editor.document);
                        }
                    }
                }, 10000);
            }
        }
    });
    // ドキュメントがセーブされたときに実行
    vscode.workspace.onDidSaveTextDocument((document) => {
        if (document) {
            const activetype = document.languageId;
            const text = document.getText();
            if (activetype == "dockerfile") {
                //データはjsonで渡してjsonでもらう
                let sendData = {
                    "data": text
                };
                checker.execPython(JSON.stringify(sendData));
                setTimeout(() => {
                    checker.clearDiagList();
                    let data;
                    while (checker._pythonRes == "") {
                    }
                    data = JSON.parse(checker._pythonRes);
                    for (const v of data) {
                        let diag = checker.createDiag(document, v['position_start'], v['position_end'], v['message']);
                        if (diag) {
                            checker.pushDiagList(diag);
                            checker.setDiag(document);
                        }
                    }
                }, 5000);
            }
        }
    });
}
class Checker {
    static providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];
    // 診断のコレクション．これにセットすることで診断が反映される．
    _diagnostics;
    // 診断のリスト
    _diagList;
    _pythonRes = "";
    _pythonRes_old = "";
    constructor() {
        this._diagnostics = vscode.languages.createDiagnosticCollection("STC");
        this._diagList = [];
    }
    // コードに変更があったときに実行されるメソッド
    provideCodeActions(document, range, context, token) {
        let diag = this.createDiag(document, 0, 5, "This is a message");
        this.delDiag(document);
        this.setDiag(document);
        return undefined;
    }
    // 診断（エラーとか）の作成
    // startPos文字目からendPos文字目にかけてmessageを表示する．
    createDiag(document, startPos, endPos, message) {
        // 警告を出すファイル上の位置
        let _startPos = document?.positionAt(startPos);
        let _endPos = document?.positionAt(endPos);
        if (!_startPos && !_endPos) {
            return null;
        }
        // 警告を出すファイル上の位置の決定
        let range = new vscode.Range(_startPos, _endPos);
        // 診断の作成
        // Warningを変えればエラーとか青線とかに変えられる
        let diag = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Warning);
        return diag;
    }
    pushDiagList(diag) {
        this._diagList.push(diag);
    }
    clearDiagList() {
        this._diagList = [];
    }
    setDiag(document) {
        this._diagnostics.set(document.uri, this._diagList);
    }
    delDiag(document) {
        this._diagnostics.set(document.uri, undefined);
    }
    // Pythonを実行．Pythonの実行が終わると_pythonResに結果を保存する．
    // 結果はPythonファイルの標準出力
    // _pythonResはPythonファイルの実行が終わらないと結果が格納されないことに注意．
    execPython(pymessage) {
        let ext_path = vscode.extensions.getExtension('sec_hymn.dochecker')?.extensionPath;
        let pythonpath = vscode.workspace.getConfiguration('python').get('pythonPath');
        let res_str = "";
        let self = this;
        //Pythonファイルを実行するときのオプション
        let options2 = {
            mode: 'text',
            pythonPath: pythonpath,
            scriptPath: ext_path,
            args: [],
            pythonOptions: []
        };
        let pyshell = new python_shell_1.PythonShell("python/final_detect_addinput.py", options2);
        pyshell.send(pymessage);
        pyshell.on('message', function (message) {
            self.setPythonRes(message);
        });
    }
    setPythonRes(res) {
        this._pythonRes = res;
    }
}
exports.Checker = Checker;
//# sourceMappingURL=extension.js.map

import * as vscode from 'vscode';
import {Options, PythonShell} from 'python-shell';

export function activate(context: vscode.ExtensionContext) {
	let checker = new Checker();

	// アクティブエディタが変更されたときに実行
	vscode.window.onDidChangeActiveTextEditor((editor) => {
		if(editor){
			const activetype = editor.document.languageId;
			const text = editor.document.getText();

			if(activetype == "dockerfile"){
				//データはjsonで渡してjsonでもらう
				let sendData = {
					"data": text
				}
				checker.execPython(JSON.stringify(sendData));
				
				setTimeout(() => {
					checker.clearDiagList();

					let data;
					while(checker._pythonRes == ""){
					}
					data = JSON.parse(checker._pythonRes);

					for(const v of data){
						let diag = checker.createDiag(editor.document, v['position_start'], v['position_end'], v['message'])
						if(diag){
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
		if(document){
			const activetype = document.languageId;
			const text = document.getText();


			if(activetype == "dockerfile"){
				//データはjsonで渡してjsonでもらう
				let sendData = {
					"data": text
				}
				checker.execPython(JSON.stringify(sendData));

				setTimeout(() => {
					checker.clearDiagList();

					let data;
					while(checker._pythonRes == ""){
					}
					data = JSON.parse(checker._pythonRes);

					for(const v of data){
						let diag = checker.createDiag(document, v['position_start'], v['position_end'], v['message'])
						if(diag){
							checker.pushDiagList(diag);
							checker.setDiag(document);
						}			
					}
				}, 10000);
			}
		}
	});
}

export class Checker implements vscode.CodeActionProvider{
	public static readonly providedCodeActionKinds = [
		vscode.CodeActionKind.QuickFix
	];

	// 診断のコレクション．これにセットすることで診断が反映される．
	private _diagnostics: vscode.DiagnosticCollection;
	// 診断のリスト
	private _diagList: vscode.Diagnostic[];

	public _pythonRes: string = "";
	public _pythonRes_old: string = "";

	public constructor(){
		this._diagnostics = vscode.languages.createDiagnosticCollection("STC");
		this._diagList = [];
	}

	// コードに変更があったときに実行されるメソッド
	public provideCodeActions(document: vscode.TextDocument, range: vscode.Range | vscode.Selection, context: vscode.CodeActionContext, token: vscode.CancellationToken): vscode.ProviderResult<(vscode.CodeAction | vscode.Command)[]> {
		let diag = this.createDiag(document, 0, 5, "This is a message");
		this.delDiag(document);
		this.setDiag(document);
		return undefined;
	}

	// 診断（エラーとか）の作成
	// startPos文字目からendPos文字目にかけてmessageを表示する．
	public createDiag(document: vscode.TextDocument, startPos: number, endPos: number, message: string): vscode.Diagnostic | null{
		// 警告を出すファイル上の位置
		let _startPos = document?.positionAt(startPos);
		let _endPos = document?.positionAt(endPos);

		if(!_startPos && !_endPos){
			return null;
		}

		// 警告を出すファイル上の位置の決定
		let range = new vscode.Range(_startPos, _endPos);
		// 診断の作成
		// Warningを変えればエラーとか青線とかに変えられる
		let diag = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Warning);

		return diag;
	}


	public pushDiagList(diag: vscode.Diagnostic){
		this._diagList.push(diag);
	}

	public clearDiagList(){
		this._diagList = [];
	}

	public setDiag(document: vscode.TextDocument){
		this._diagnostics.set(document.uri, this._diagList);
	}

	private delDiag(document: vscode.TextDocument){
		this._diagnostics.set(document.uri, undefined);
	}

	// Pythonを実行．Pythonの実行が終わると_pythonResに結果を保存する．
	// 結果はPythonファイルの標準出力
	// _pythonResはPythonファイルの実行が終わらないと結果が格納されないことに注意．
	public execPython(pymessage: string){
		let ext_path = vscode.extensions.getExtension('sec_hymn.dochecker')?.extensionPath;
		let pythonpath = vscode.workspace.getConfiguration('python').get<string>('pythonPath')
		let res_str: string = "";
		let self = this;


		//Pythonファイルを実行するときのオプション
		let options2: Options = {
			mode: 'text',
			pythonPath: pythonpath,
			scriptPath: ext_path,
			args: [],
			pythonOptions: []
		};

		let pyshell = new PythonShell("python/final_detect_addinput.py", options2);
		pyshell.send(pymessage)

		pyshell.on('message', function(message){
			self.setPythonRes(message);
		});
	}

	private setPythonRes(res: string){
		this._pythonRes = res;
	}

}

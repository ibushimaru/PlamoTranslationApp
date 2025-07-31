import Cocoa

class StatusWindowController: NSWindowController {
    
    override init(window: NSWindow?) {
        let window = NSWindow(
            contentRect: NSRect(x: 100, y: 100, width: 400, height: 300),
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        window.title = "PLaMo翻訳ステータス"
        window.center()
        
        // シンプルなラベルを追加
        let label1 = NSTextField(labelWithString: "PLaMo Translation App")
        label1.frame = NSRect(x: 20, y: 250, width: 360, height: 30)
        label1.font = NSFont.boldSystemFont(ofSize: 16)
        
        let label2 = NSTextField(labelWithString: "サーバー: 確認中...")
        label2.frame = NSRect(x: 20, y: 200, width: 360, height: 25)
        
        let label3 = NSTextField(labelWithString: "ホットキー: CMD+C+C (素早く2回押す)")
        label3.frame = NSRect(x: 20, y: 150, width: 360, height: 25)
        
        let label4 = NSTextField(labelWithString: "最後の翻訳: なし")
        label4.frame = NSRect(x: 20, y: 100, width: 360, height: 25)
        
        window.contentView?.addSubview(label1)
        window.contentView?.addSubview(label2)
        window.contentView?.addSubview(label3)
        window.contentView?.addSubview(label4)
        
        window.makeKeyAndOrderFront(nil)
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    func updateServerStatus(_ status: ConnectionStatus) {
        // 今はシンプルに何もしない
    }
    
    func updateLastTranslation(original: String, translated: String) {
        // 今はシンプルに何もしない
    }
    
    func updateStatus(_ message: String) {
        // 今はシンプルに何もしない
    }
}
import Cocoa

let app = NSApplication.shared
app.setActivationPolicy(.regular)

let window = NSWindow(
    contentRect: NSRect(x: 100, y: 100, width: 400, height: 200),
    styleMask: [.titled, .closable, .resizable],
    backing: .buffered,
    defer: false
)

window.title = "テストウィンドウ"
window.makeKeyAndOrderFront(nil)
window.center()

let label = NSTextField(labelWithString: "これはテストです")
label.frame = NSRect(x: 150, y: 80, width: 100, height: 40)
window.contentView?.addSubview(label)

app.run()
import Cocoa

class TranslationResultWindow: NSWindowController {
    @IBOutlet weak var originalTextLabel: NSTextField!
    @IBOutlet weak var translatedTextLabel: NSTextField!
    @IBOutlet weak var copyButton: NSButton!
    @IBOutlet weak var languageLabel: NSTextField!
    
    private var autoDismissTimer: Timer?
    private var translationResult: TranslationResult?
    
    override var windowNibName: NSNib.Name? {
        return nil
    }
    
    convenience init() {
        self.init(window: nil)
        createWindow()
        setupWindow()
    }
    
    private func createWindow() {
        let newWindow = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 400, height: 200),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        window = newWindow
    }
    
    override func windowDidLoad() {
        super.windowDidLoad()
        setupWindow()
    }
    
    private func setupWindow() {
        guard let window = window else { return }
        
        window.styleMask = [.borderless, .nonactivatingPanel]
        window.level = .floating
        window.backgroundColor = NSColor.controlBackgroundColor.withAlphaComponent(0.95)
        window.hasShadow = true
        window.isMovableByWindowBackground = true
        
        setupProgrammaticUI()
    }
    
    private func setupProgrammaticUI() {
        guard let window = window else { return }
        
        let contentView = NSView()
        window.contentView = contentView
        
        let stackView = NSStackView()
        stackView.orientation = .vertical
        stackView.spacing = 12
        stackView.alignment = .leading
        stackView.translatesAutoresizingMaskIntoConstraints = false
        
        languageLabel = NSTextField(labelWithString: "")
        languageLabel.font = NSFont.systemFont(ofSize: 11, weight: .medium)
        languageLabel.textColor = .secondaryLabelColor
        
        originalTextLabel = NSTextField(wrappingLabelWithString: "")
        originalTextLabel.font = NSFont.systemFont(ofSize: 13)
        originalTextLabel.textColor = .labelColor
        originalTextLabel.maximumNumberOfLines = 3
        
        let separatorView = NSView()
        separatorView.wantsLayer = true
        separatorView.layer?.backgroundColor = NSColor.separatorColor.cgColor
        separatorView.translatesAutoresizingMaskIntoConstraints = false
        separatorView.heightAnchor.constraint(equalToConstant: 1).isActive = true
        
        translatedTextLabel = NSTextField(wrappingLabelWithString: "")
        translatedTextLabel.font = NSFont.systemFont(ofSize: 14, weight: .medium)
        translatedTextLabel.textColor = .labelColor
        translatedTextLabel.maximumNumberOfLines = 5
        
        copyButton = NSButton(title: "Copy Translation", target: self, action: #selector(copyTranslation))
        copyButton.bezelStyle = .rounded
        
        stackView.addArrangedSubview(languageLabel)
        stackView.addArrangedSubview(originalTextLabel)
        stackView.addArrangedSubview(separatorView)
        stackView.addArrangedSubview(translatedTextLabel)
        stackView.addArrangedSubview(copyButton)
        
        contentView.addSubview(stackView)
        
        NSLayoutConstraint.activate([
            stackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            stackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            stackView.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 16),
            stackView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -16),
            
            separatorView.leadingAnchor.constraint(equalTo: stackView.leadingAnchor),
            separatorView.trailingAnchor.constraint(equalTo: stackView.trailingAnchor),
            
            originalTextLabel.leadingAnchor.constraint(equalTo: stackView.leadingAnchor),
            originalTextLabel.trailingAnchor.constraint(equalTo: stackView.trailingAnchor),
            
            translatedTextLabel.leadingAnchor.constraint(equalTo: stackView.leadingAnchor),
            translatedTextLabel.trailingAnchor.constraint(equalTo: stackView.trailingAnchor)
        ])
        
        window.setContentSize(NSSize(width: 400, height: 200))
    }
    
    func showTranslation(_ result: TranslationResult) {
        self.translationResult = result
        
        languageLabel.stringValue = "\(result.sourceLanguage.displayName) → \(result.targetLanguage.displayName)"
        originalTextLabel.stringValue = result.originalText
        translatedTextLabel.stringValue = result.translatedText
        
        positionWindowNearCursor()
        showWindow(nil)
        
        scheduleAutoDismiss()
    }
    
    private func positionWindowNearCursor() {
        guard let window = window, let screen = NSScreen.main else { return }
        
        let mouseLocation = NSEvent.mouseLocation
        let windowSize = window.frame.size
        
        var newOrigin = CGPoint(
            x: mouseLocation.x + 20,
            y: mouseLocation.y - windowSize.height - 20
        )
        
        let screenFrame = screen.visibleFrame
        
        if newOrigin.x + windowSize.width > screenFrame.maxX {
            newOrigin.x = mouseLocation.x - windowSize.width - 20
        }
        
        if newOrigin.y < screenFrame.minY {
            newOrigin.y = mouseLocation.y + 20
        }
        
        if newOrigin.x < screenFrame.minX {
            newOrigin.x = screenFrame.minX + 10
        }
        
        if newOrigin.y + windowSize.height > screenFrame.maxY {
            newOrigin.y = screenFrame.maxY - windowSize.height - 10
        }
        
        window.setFrameOrigin(newOrigin)
    }
    
    private func scheduleAutoDismiss() {
        autoDismissTimer?.invalidate()
        autoDismissTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: false) { [weak self] _ in
            self?.close()
        }
    }
    
    @objc private func copyTranslation() {
        guard let result = translationResult else { return }
        
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(result.translatedText, forType: .string)
        
        copyButton.title = "Copied!"
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.copyButton.title = "Copy Translation"
        }
    }
    
    override func close() {
        autoDismissTimer?.invalidate()
        autoDismissTimer = nil
        super.close()
    }
    
    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 {
            close()
        } else if event.modifierFlags.contains(.command) && event.charactersIgnoringModifiers == "c" {
            copyTranslation()
        } else {
            super.keyDown(with: event)
        }
    }
}
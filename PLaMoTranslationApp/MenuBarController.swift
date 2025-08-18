import Cocoa

class MenuBarController: NSObject {
    private var statusItem: NSStatusItem?
    private let translationService: TranslationServiceProtocol
    private let configurationManager: ConfigurationManagerProtocol
    private var connectionCheckTimer: Timer?
    
    weak var delegate: MenuBarControllerDelegate?
    
    init(translationService: TranslationServiceProtocol, configurationManager: ConfigurationManagerProtocol) {
        self.translationService = translationService
        self.configurationManager = configurationManager
        super.init()
    }
    
    func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        guard statusItem != nil else {
            print("Failed to create status item")
            return
        }
        
        updateMenuBarIcon(.disconnected)
        setupMenu()
        startConnectionMonitoring()
    }
    
    private func setupMenu() {
        guard let statusItem = statusItem else { return }
        
        let menu = NSMenu()
        
        let translationItem = NSMenuItem(title: "Translate Selection (⌘CC)", action: #selector(translateSelection), keyEquivalent: "")
        translationItem.target = self
        menu.addItem(translationItem)
        
        menu.addItem(NSMenuItem.separator())
        
        let connectionStatusItem = NSMenuItem(title: translationService.connectionStatus.description, action: nil, keyEquivalent: "")
        connectionStatusItem.tag = 100
        menu.addItem(connectionStatusItem)
        
        let checkConnectionItem = NSMenuItem(title: "Check Connection", action: #selector(checkConnection), keyEquivalent: "")
        checkConnectionItem.target = self
        menu.addItem(checkConnectionItem)
        
        menu.addItem(NSMenuItem.separator())
        
        let preferencesItem = NSMenuItem(title: "Preferences...", action: #selector(showPreferences), keyEquivalent: ",")
        preferencesItem.target = self
        menu.addItem(preferencesItem)
        
        menu.addItem(NSMenuItem.separator())
        
        let quitItem = NSMenuItem(title: "Quit PLaMo Translation", action: #selector(quit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)
        
        statusItem.menu = menu
    }
    
    func updateMenuBarIcon(_ status: ConnectionStatus) {
        guard let statusItem = statusItem else { return }
        
        let iconName: String
        let toolTip: String
        
        switch status {
        case .connected:
            iconName = "checkmark.circle"
            toolTip = "PLaMo Translation - Connected"
        case .disconnected:
            iconName = "circle"
            toolTip = "PLaMo Translation - Disconnected"
        case .connecting:
            iconName = "circle.dotted"
            toolTip = "PLaMo Translation - Connecting..."
        case .error(let message):
            iconName = "exclamationmark.circle"
            toolTip = "PLaMo Translation - Error: \(message)"
        }
        
        if #available(macOS 11.0, *) {
            if let image = NSImage(systemSymbolName: iconName, accessibilityDescription: nil) {
                image.isTemplate = true
                statusItem.button?.image = image
            } else {
                statusItem.button?.title = "PLaMo"
            }
        } else {
            statusItem.button?.title = "PLaMo"
        }
        
        statusItem.button?.toolTip = toolTip
        
        if let menu = statusItem.menu,
           let statusMenuItem = menu.item(withTag: 100) {
            statusMenuItem.title = status.description
        }
    }
    
    private func startConnectionMonitoring() {
        connectionCheckTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { [weak self] _ in
            Task {
                await self?.performConnectionCheck()
            }
        }
        
        Task {
            await performConnectionCheck()
        }
    }
    
    private func performConnectionCheck() async {
        _ = await translationService.checkServerConnection()
        
        await MainActor.run {
            updateMenuBarIcon(translationService.connectionStatus)
        }
    }
    
    @objc private func translateSelection() {
        delegate?.menuBarControllerDidRequestTranslation(self)
    }
    
    @objc private func checkConnection() {
        Task {
            updateMenuBarIcon(.connecting)
            await performConnectionCheck()
        }
    }
    
    @objc private func showPreferences() {
        delegate?.menuBarControllerDidRequestSettings(self)
    }
    
    @objc private func quit() {
        cleanup()
        NSApplication.shared.terminate(nil)
    }
    
    func cleanup() {
        connectionCheckTimer?.invalidate()
        connectionCheckTimer = nil
        
        if let statusItem = statusItem {
            NSStatusBar.system.removeStatusItem(statusItem)
            self.statusItem = nil
        }
    }
    
    deinit {
        cleanup()
    }
}


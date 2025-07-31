import Cocoa
import UserNotifications

@main
class AppDelegate: NSObject, NSApplicationDelegate {
    
    private var menuBarController: MenuBarController!
    private var translationService: TranslationService!
    private var configurationManager: ConfigurationManager!
    private var hotkeyManager: HotkeyManager!
    private var textCaptureService: TextCaptureService!
    private var translationResultWindow: TranslationResultWindow!
    private var statusWindowController: StatusWindowController!
    
    private var isTranslating = false
    
    func applicationDidFinishLaunching(_ aNotification: Notification) {
        setupServices()
        setupMenuBar()
        setupStatusWindow()
        setupHotkey()
        setupNotifications()
        setupUserNotifications()
        
        Task {
            await checkInitialServerConnection()
        }
    }
    
    func applicationWillTerminate(_ aNotification: Notification) {
        cleanup()
    }
    
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        return false
    }
    
    private func setupServices() {
        configurationManager = ConfigurationManager()
        let configuration = configurationManager.loadConfiguration()
        
        translationService = TranslationService(serverEndpoint: configuration.serverEndpoint)
        textCaptureService = TextCaptureService()
        hotkeyManager = HotkeyManager()
        translationResultWindow = TranslationResultWindow()
    }
    
    private func setupMenuBar() {
        menuBarController = MenuBarController(
            translationService: translationService,
            configurationManager: configurationManager
        )
        menuBarController.delegate = self
        menuBarController.setupMenuBar()
    }
    
    private func setupStatusWindow() {
        statusWindowController = StatusWindowController(window: nil)
        // showWindow(nil)は呼ばない - StatusWindowController内で既に表示している
    }
    
    private func setupHotkey() {
        guard configurationManager.configuration.hotkeyEnabled else { return }
        
        do {
            try hotkeyManager.registerHotkey { [weak self] in
                self?.handleTranslationRequest()
            }
        } catch {
            print("Failed to register hotkey: \(error)")
            showErrorNotification("Failed to register CMD+C+C hotkey: \(error.localizedDescription)")
        }
    }
    
    private func setupNotifications() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(configurationDidChange),
            name: .configurationDidChange,
            object: nil
        )
    }
    
    private func setupUserNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if let error = error {
                print("Failed to request notification authorization: \(error)")
            }
        }
    }
    
    private func checkInitialServerConnection() async {
        let isConnected = await translationService.checkServerConnection()
        
        await MainActor.run {
            menuBarController.updateMenuBarIcon(translationService.connectionStatus)
            statusWindowController.updateServerStatus(translationService.connectionStatus)
            
            if !isConnected {
                showServerUnavailableNotification()
            }
        }
    }
    
    @objc private func configurationDidChange(_ notification: Notification) {
        guard let config = notification.userInfo?["configuration"] as? AppConfiguration else { return }
        
        if let translationService = translationService as? TranslationService {
            translationService.updateServerEndpoint(config.serverEndpoint)
        }
        
        if config.hotkeyEnabled && !hotkeyManager.isRegistered {
            setupHotkey()
        } else if !config.hotkeyEnabled && hotkeyManager.isRegistered {
            hotkeyManager.unregisterHotkey()
        }
    }
    
    private func handleTranslationRequest() {
        guard !isTranslating else {
            print("Translation already in progress")
            return
        }
        
        Task {
            await performTranslation()
        }
    }
    
    private func performTranslation() async {
        isTranslating = true
        
        await MainActor.run {
            menuBarController.updateMenuBarIcon(.connecting)
        }
        
        do {
            let text = try textCaptureService.captureSelectedText()
            
            guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                throw TranslationError.noTextSelected
            }
            
            let config = configurationManager.configuration
            let result = try await translationService.translateText(
                text,
                from: config.sourceLanguage,
                to: config.targetLanguage
            )
            
            await MainActor.run {
                translationResultWindow.showTranslation(result)
                menuBarController.updateMenuBarIcon(translationService.connectionStatus)
                statusWindowController.updateServerStatus(translationService.connectionStatus)
                statusWindowController.updateLastTranslation(original: text, translated: result.translatedText)
            }
            
        } catch let error as TextCaptureError {
            await MainActor.run {
                handleTextCaptureError(error)
            }
        } catch let error as TranslationError {
            await MainActor.run {
                handleTranslationError(error)
            }
        } catch {
            await MainActor.run {
                showErrorNotification("Unexpected error: \(error.localizedDescription)")
                menuBarController.updateMenuBarIcon(.error("Unexpected error"))
            }
        }
        
        isTranslating = false
    }
    
    private func handleTextCaptureError(_ error: TextCaptureError) {
        switch error {
        case .accessibilityPermissionDenied:
            if !textCaptureService.hasAccessibilityPermission() {
                textCaptureService.showAccessibilityPermissionAlert()
            }
        case .noTextFound, .noFocusedElement:
            showErrorNotification("No text selected. Please select text and try again.")
        default:
            showErrorNotification(error.localizedDescription)
        }
    }
    
    private func handleTranslationError(_ error: TranslationError) {
        switch error {
        case .serverUnavailable:
            showServerUnavailableNotification()
            menuBarController.updateMenuBarIcon(.error("Server unavailable"))
        case .noTextSelected:
            showErrorNotification("No text selected. Please select text and try again.")
        case .textTooLong:
            showErrorNotification("Selected text is too long. Please select shorter text.")
        case .networkError(let underlyingError):
            showErrorNotification("Network error: \(underlyingError.localizedDescription)")
            menuBarController.updateMenuBarIcon(.error("Network error"))
        default:
            showErrorNotification(error.localizedDescription)
            menuBarController.updateMenuBarIcon(.error("Translation error"))
        }
    }
    
    private func showServerUnavailableNotification() {
        let content = UNMutableNotificationContent()
        content.title = "PLaMo Server Unavailable"
        content.body = "Please start the PLaMo server with: plamo-translate --precision bf16 server"
        content.sound = UNNotificationSound.default
        
        let request = UNNotificationRequest(identifier: "server-unavailable", content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to show notification: \(error)")
            }
        }
    }
    
    private func showErrorNotification(_ message: String) {
        let content = UNMutableNotificationContent()
        content.title = "PLaMo Translation Error"
        content.body = message
        content.sound = UNNotificationSound.default
        
        let request = UNNotificationRequest(identifier: "error-\(UUID().uuidString)", content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to show notification: \(error)")
            }
        }
    }
    
    private func showSuccessNotification(_ message: String) {
        let content = UNMutableNotificationContent()
        content.title = "PLaMo Translation"
        content.body = message
        content.sound = UNNotificationSound.default
        
        let request = UNNotificationRequest(identifier: "success-\(UUID().uuidString)", content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to show notification: \(error)")
            }
        }
    }
    
    private func cleanup() {
        hotkeyManager?.unregisterHotkey()
        menuBarController?.cleanup()
        translationResultWindow?.close()
    }
}

extension AppDelegate: MenuBarControllerDelegate {
    func menuBarControllerDidRequestTranslation(_ controller: MenuBarController) {
        handleTranslationRequest()
    }
    
    func menuBarControllerDidRequestSettings(_ controller: MenuBarController) {
        showPreferencesWindow()
    }
    
    func menuBarControllerDidRequestQuit(_ controller: MenuBarController) {
        NSApplication.shared.terminate(nil)
    }
    
    private func showPreferencesWindow() {
        let alert = NSAlert()
        alert.messageText = "Preferences"
        alert.informativeText = """
        Current Configuration:
        Source Language: \(configurationManager.configuration.sourceLanguage.displayName)
        Target Language: \(configurationManager.configuration.targetLanguage.displayName)
        Server: \(configurationManager.configuration.serverEndpoint.absoluteString)
        Hotkey Enabled: \(configurationManager.configuration.hotkeyEnabled ? "Yes" : "No")
        
        To modify preferences, you can update the configuration programmatically or add a preferences window in future versions.
        """
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
}
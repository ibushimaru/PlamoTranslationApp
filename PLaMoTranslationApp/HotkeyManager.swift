import Cocoa
import Carbon

class HotkeyManager: HotkeyManagerProtocol {
    private var hotKeyRef: EventHotKeyRef?
    private var handler: (() -> Void)?
    private let hotKeyID = EventHotKeyID(signature: fourCharCodeFrom("PLMo"), id: 1)
    private var eventMonitor: Any?
    private var lastCmdCTime: TimeInterval = 0
    private let doubleCTimeout: TimeInterval = 0.5
    
    var isRegistered: Bool {
        return eventMonitor != nil
    }
    
    func registerHotkey(handler: @escaping () -> Void) throws {
        guard !isRegistered else {
            print("Hotkey already registered")
            return
        }
        
        self.handler = handler
        
        // Monitor CMD+C key combinations using NSEvent
        eventMonitor = NSEvent.addGlobalMonitorForEvents(matching: .keyDown) { [weak self] event in
            self?.handleKeyEvent(event)
        }
        
        print("Hotkey CMD+C+C registered successfully")
    }
    
    func unregisterHotkey() {
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
            eventMonitor = nil
        }
        handler = nil
        print("Hotkey unregistered")
    }
    
    private func handleKeyEvent(_ event: NSEvent) {
        // Check for CMD+C
        guard event.modifierFlags.contains(.command) && event.keyCode == 8 else { return } // 8 is C key
        
        let currentTime = Date().timeIntervalSince1970
        
        // Check if this is a double CMD+C within timeout
        if currentTime - lastCmdCTime <= doubleCTimeout {
            print("CMD+C+C detected!")
            DispatchQueue.main.async { [weak self] in
                self?.handler?()
            }
            lastCmdCTime = 0 // Reset to prevent triple-click triggering
        } else {
            lastCmdCTime = currentTime
            print("First CMD+C detected, waiting for second...")
        }
    }
    
    deinit {
        unregisterHotkey()
    }
}

enum HotkeyError: Error, LocalizedError {
    case registrationFailed(OSStatus)
    case alreadyRegistered
    
    var errorDescription: String? {
        switch self {
        case .registrationFailed(let status):
            return "Failed to register hotkey. Error code: \(status)"
        case .alreadyRegistered:
            return "Hotkey is already registered"
        }
    }
}

private func fourCharCodeFrom(_ string: String) -> FourCharCode {
    guard string.count == 4 else { return 0 }
    
    var code: FourCharCode = 0
    for char in string.utf8 {
        code = (code << 8) | FourCharCode(char)
    }
    return code
}
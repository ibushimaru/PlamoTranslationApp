import Cocoa
import ApplicationServices

class TextCaptureService: TextCaptureServiceProtocol {
    
    func captureSelectedText() throws -> String {
        if let text = try? getTextFromAccessibility() {
            return text
        }
        
        if let text = getTextFromClipboard() {
            return text
        }
        
        throw TranslationError.noTextSelected
    }
    
    private func getTextFromAccessibility() throws -> String {
        guard AXIsProcessTrusted() else {
            throw TextCaptureError.accessibilityPermissionDenied
        }
        
        guard let frontmostApp = NSWorkspace.shared.frontmostApplication else {
            throw TextCaptureError.noFrontmostApplication
        }
        
        let appRef = AXUIElementCreateApplication(frontmostApp.processIdentifier)
        
        var focusedElement: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(appRef, kAXFocusedUIElementAttribute as CFString, &focusedElement)
        
        guard result == .success, let element = focusedElement else {
            throw TextCaptureError.noFocusedElement
        }
        
        let uiElement = element as! AXUIElement
        
        var selectedText: CFTypeRef?
        let selectedTextResult = AXUIElementCopyAttributeValue(uiElement, kAXSelectedTextAttribute as CFString, &selectedText)
        
        if selectedTextResult == .success, let text = selectedText as? String, !text.isEmpty {
            return text
        }
        
        var value: CFTypeRef?
        let valueResult = AXUIElementCopyAttributeValue(uiElement, kAXValueAttribute as CFString, &value)
        
        if valueResult == .success, let text = value as? String, !text.isEmpty {
            return text
        }
        
        throw TextCaptureError.noTextFound
    }
    
    private func getTextFromClipboard() -> String? {
        let pasteboard = NSPasteboard.general
        
        guard let text = pasteboard.string(forType: .string), !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return nil
        }
        
        return text
    }
    
    func requestAccessibilityPermission() {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        AXIsProcessTrustedWithOptions(options as CFDictionary)
    }
    
    func hasAccessibilityPermission() -> Bool {
        return AXIsProcessTrusted()
    }
    
    func showAccessibilityPermissionAlert() {
        let alert = NSAlert()
        alert.messageText = "Accessibility Permission Required"
        alert.informativeText = """
        PLaMo Translation needs accessibility permission to capture selected text from other applications.
        
        To enable this:
        1. Go to System Preferences → Security & Privacy → Privacy
        2. Select "Accessibility" from the left sidebar
        3. Click the lock icon and enter your password
        4. Find "PLaMo Translation" in the list and check the box
        5. Restart the application
        
        Without this permission, the app will only be able to translate text from the clipboard.
        """
        alert.alertStyle = .informational
        alert.addButton(withTitle: "Open System Preferences")
        alert.addButton(withTitle: "Cancel")
        
        let response = alert.runModal()
        
        if response == .alertFirstButtonReturn {
            let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
            NSWorkspace.shared.open(url)
        }
    }
}


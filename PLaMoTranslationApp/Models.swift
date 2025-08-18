import Foundation

enum Language: String, CaseIterable, Codable {
    case japanese = "Japanese"
    case japaneseEasy = "Japanese(easy)"
    case english = "English"
    case chinese = "Chinese"
    case taiwanese = "Taiwanese"
    case korean = "Korean"
    case arabic = "Arabic"
    case italian = "Italian"
    case indonesian = "Indonesian"
    case dutch = "Dutch"
    case spanish = "Spanish"
    case thai = "Thai"
    case german = "German"
    case french = "French"
    case vietnamese = "Vietnamese"
    case russian = "Russian"
    case englishJapanese = "English|Japanese"
    
    var displayName: String {
        return self.rawValue
    }
}

struct TranslationRequest: Codable {
    let messages: [Message]
    let sourceLanguage: String
    let targetLanguage: String
    
    private enum CodingKeys: String, CodingKey {
        case messages
        case sourceLanguage = "source_language"
        case targetLanguage = "target_language"
    }
}

struct Message: Codable {
    let role: String
    let content: String
}

struct TranslationResponse: Codable {
    let translatedText: String
    let sourceLanguage: String?
    let targetLanguage: String?
    let processingTime: Double?
    
    private enum CodingKeys: String, CodingKey {
        case translatedText = "translated_text"
        case sourceLanguage = "source_language"
        case targetLanguage = "target_language"
        case processingTime = "processing_time"
    }
}

struct TranslationResult {
    let originalText: String
    let translatedText: String
    let sourceLanguage: Language
    let targetLanguage: Language
    let timestamp: Date
    let processingTime: TimeInterval
}

enum ConnectionStatus {
    case connected
    case disconnected
    case connecting
    case error(String)
    
    var description: String {
        switch self {
        case .connected:
            return "Connected"
        case .disconnected:
            return "Disconnected"
        case .connecting:
            return "Connecting..."
        case .error(let message):
            return "Error: \(message)"
        }
    }
}

enum TranslationError: Error, LocalizedError {
    case serverUnavailable
    case invalidResponse
    case networkError(Error)
    case textTooLong
    case unsupportedLanguage
    case noTextSelected
    case invalidConfiguration
    
    var errorDescription: String? {
        switch self {
        case .serverUnavailable:
            return "PLaMo server is not running. Please start the server with: plamo-translate --precision bf16 server"
        case .invalidResponse:
            return "Invalid response from PLaMo server"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .textTooLong:
            return "Selected text is too long for translation"
        case .unsupportedLanguage:
            return "Unsupported language combination"
        case .noTextSelected:
            return "No text selected. Please select text and try again."
        case .invalidConfiguration:
            return "Invalid translation configuration"
        }
    }
}

struct AppConfiguration: Codable {
    var sourceLanguage: Language
    var targetLanguage: Language
    var serverEndpoint: URL
    var autoLaunch: Bool
    var resultWindowTimeout: TimeInterval
    var hotkeyEnabled: Bool
    
    static let `default` = AppConfiguration(
        sourceLanguage: .englishJapanese,
        targetLanguage: .japanese,
        serverEndpoint: URL(string: "http://127.0.0.1:30000")!,
        autoLaunch: false,
        resultWindowTimeout: 10.0,
        hotkeyEnabled: true
    )
}

protocol TranslationServiceProtocol {
    func translateText(_ text: String, from sourceLanguage: Language, to targetLanguage: Language) async throws -> TranslationResult
    func checkServerConnection() async -> Bool
    var connectionStatus: ConnectionStatus { get }
}

protocol TextCaptureServiceProtocol {
    func captureSelectedText() throws -> String
}

protocol HotkeyManagerProtocol {
    func registerHotkey(handler: @escaping () -> Void) throws
    func unregisterHotkey()
    var isRegistered: Bool { get }
}

protocol ConfigurationManagerProtocol {
    func loadConfiguration() -> AppConfiguration
    func saveConfiguration(_ config: AppConfiguration)
    func resetToDefaults()
}

enum TextCaptureError: Error, LocalizedError {
    case accessibilityPermissionDenied
    case noTextSelected
    case captureTimeout
    case systemError(String)
    case noFrontmostApplication
    case noFocusedElement
    case noTextFound
    
    var errorDescription: String? {
        switch self {
        case .accessibilityPermissionDenied:
            return "Accessibility permission is required to capture text. Please enable it in System Preferences > Security & Privacy > Privacy > Accessibility."
        case .noTextSelected:
            return "No text is currently selected."
        case .captureTimeout:
            return "Text capture timed out."
        case .systemError(let message):
            return "System error: \(message)"
        case .noFrontmostApplication:
            return "Unable to identify the frontmost application"
        case .noFocusedElement:
            return "No focused UI element found"
        case .noTextFound:
            return "No text found in the focused element"
        }
    }
}

protocol MenuBarControllerDelegate: AnyObject {
    func menuBarControllerDidRequestTranslation(_ controller: MenuBarController)
    func menuBarControllerDidRequestSettings(_ controller: MenuBarController)
    func menuBarControllerDidRequestQuit(_ controller: MenuBarController)
}

extension NSNotification.Name {
    static let configurationDidChange = NSNotification.Name("ConfigurationDidChange")
}
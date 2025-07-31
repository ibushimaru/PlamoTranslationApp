import Foundation
import ServiceManagement

class ConfigurationManager: ConfigurationManagerProtocol {
    private let userDefaults = UserDefaults.standard
    private let configurationKey = "PLaMoTranslationConfiguration"
    
    private var _configuration: AppConfiguration
    
    var configuration: AppConfiguration {
        return _configuration
    }
    
    init() {
        self._configuration = Self.loadConfigurationFromDefaults() ?? AppConfiguration.default
    }
    
    func loadConfiguration() -> AppConfiguration {
        if let data = userDefaults.data(forKey: configurationKey) {
            do {
                let configuration = try JSONDecoder().decode(AppConfiguration.self, from: data)
                self._configuration = configuration
                return configuration
            } catch {
                print("Failed to decode configuration: \(error)")
                let defaultConfig = AppConfiguration.default
                saveConfiguration(defaultConfig)
                self._configuration = defaultConfig
                return defaultConfig
            }
        } else {
            let defaultConfig = AppConfiguration.default
            saveConfiguration(defaultConfig)
            self._configuration = defaultConfig
            return defaultConfig
        }
    }
    
    func saveConfiguration(_ config: AppConfiguration) {
        do {
            let data = try JSONEncoder().encode(config)
            userDefaults.set(data, forKey: configurationKey)
            self._configuration = config
            
            NotificationCenter.default.post(
                name: .configurationDidChange,
                object: self,
                userInfo: ["configuration": config]
            )
        } catch {
            print("Failed to encode configuration: \(error)")
        }
    }
    
    func resetToDefaults() {
        let defaultConfig = AppConfiguration.default
        saveConfiguration(defaultConfig)
    }
    
    func updateSourceLanguage(_ language: Language) {
        var config = _configuration
        config.sourceLanguage = language
        saveConfiguration(config)
    }
    
    func updateTargetLanguage(_ language: Language) {
        var config = _configuration
        config.targetLanguage = language
        saveConfiguration(config)
    }
    
    func updateServerEndpoint(_ endpoint: URL) {
        var config = _configuration
        config.serverEndpoint = endpoint
        saveConfiguration(config)
    }
    
    func updateAutoLaunch(_ enabled: Bool) {
        var config = _configuration
        config.autoLaunch = enabled
        saveConfiguration(config)
        
        updateLaunchAgent(enabled)
    }
    
    func updateResultWindowTimeout(_ timeout: TimeInterval) {
        var config = _configuration
        config.resultWindowTimeout = timeout
        saveConfiguration(config)
    }
    
    func updateHotkeyEnabled(_ enabled: Bool) {
        var config = _configuration
        config.hotkeyEnabled = enabled
        saveConfiguration(config)
    }
    
    private static func loadConfigurationFromDefaults() -> AppConfiguration? {
        guard let data = UserDefaults.standard.data(forKey: "PLaMoTranslationConfiguration") else {
            return nil
        }
        
        do {
            return try JSONDecoder().decode(AppConfiguration.self, from: data)
        } catch {
            print("Failed to decode configuration: \(error)")
            return nil
        }
    }
    
    private func updateLaunchAgent(_ enabled: Bool) {
        guard let bundleIdentifier = Bundle.main.bundleIdentifier else {
            print("Unable to get bundle identifier")
            return
        }
        
        if enabled {
            if !SMLoginItemSetEnabled(bundleIdentifier as CFString, true) {
                print("Failed to enable launch at login")
            }
        } else {
            if !SMLoginItemSetEnabled(bundleIdentifier as CFString, false) {
                print("Failed to disable launch at login")
            }
        }
    }
}


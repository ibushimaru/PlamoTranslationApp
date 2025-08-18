import Foundation

class TranslationService: TranslationServiceProtocol {
    private let session: URLSession
    private var serverEndpoint: URL
    private var _connectionStatus: ConnectionStatus = .disconnected
    
    var connectionStatus: ConnectionStatus {
        return _connectionStatus
    }
    
    init(serverEndpoint: URL = URL(string: "http://127.0.0.1:30000")!) {
        self.serverEndpoint = serverEndpoint
        self.session = URLSession(configuration: .default)
    }
    
    func translateText(_ text: String, from sourceLanguage: Language, to targetLanguage: Language) async throws -> TranslationResult {
        let startTime = Date()
        
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw TranslationError.noTextSelected
        }
        
        guard text.count <= 5000 else {
            throw TranslationError.textTooLong
        }
        
        _connectionStatus = .connecting
        
        let request = TranslationRequest(
            messages: [Message(role: "user", content: text)],
            sourceLanguage: sourceLanguage.rawValue,
            targetLanguage: targetLanguage.rawValue
        )
        
        let url = serverEndpoint.appendingPathComponent("mcp")
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            let requestData = try JSONEncoder().encode(request)
            urlRequest.httpBody = requestData
            
            let (data, response) = try await session.data(for: urlRequest)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                _connectionStatus = .error("Invalid response")
                throw TranslationError.invalidResponse
            }
            
            guard httpResponse.statusCode == 200 else {
                if httpResponse.statusCode == 404 || httpResponse.statusCode >= 500 {
                    _connectionStatus = .error("Server unavailable")
                    throw TranslationError.serverUnavailable
                } else {
                    _connectionStatus = .error("HTTP \(httpResponse.statusCode)")
                    throw TranslationError.invalidResponse
                }
            }
            
            let translationResponse = try JSONDecoder().decode(TranslationResponse.self, from: data)
            
            _connectionStatus = .connected
            
            let processingTime = Date().timeIntervalSince(startTime)
            
            return TranslationResult(
                originalText: text,
                translatedText: translationResponse.translatedText,
                sourceLanguage: sourceLanguage,
                targetLanguage: targetLanguage,
                timestamp: Date(),
                processingTime: processingTime
            )
            
        } catch _ as DecodingError {
            _connectionStatus = .error("Invalid response format")
            throw TranslationError.invalidResponse
        } catch let error as URLError {
            _connectionStatus = .error("Network error")
            if error.code == .cannotConnectToHost || error.code == .cannotFindHost {
                throw TranslationError.serverUnavailable
            } else {
                throw TranslationError.networkError(error)
            }
        } catch {
            _connectionStatus = .error(error.localizedDescription)
            throw error
        }
    }
    
    func checkServerConnection() async -> Bool {
        let url = serverEndpoint.appendingPathComponent("mcp")
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = 5.0
        
        do {
            let (_, response) = try await session.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse {
                let isConnected = httpResponse.statusCode < 500
                _connectionStatus = isConnected ? .connected : .disconnected
                return isConnected
            }
            
            _connectionStatus = .disconnected
            return false
            
        } catch {
            _connectionStatus = .disconnected
            return false
        }
    }
    
    func updateServerEndpoint(_ endpoint: URL) {
        self.serverEndpoint = endpoint
        _connectionStatus = .disconnected
    }
}
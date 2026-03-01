/**
 * API Service for AI Assistant Health Dashboard
 *
 * Architecture:
 * - In 3DDashboard (trusted mode): Uses call3DSpace() for direct API calls via user's SSO
 * - In standalone mode: Falls back to backend proxy (for local development)
 *
 * CRITICAL FIX: Trusted mode is checked DYNAMICALLY at runtime, not at module load time.
 * This ensures the widget object exists before checking if we're in trusted mode.
 */

import { call3DSpace, initPlatformConnectors } from '@widget-lab/platform-connectors';

// Track initialization state
let platformConnectorsInitialized = false;

/**
 * Initialize Platform Connectors
 * Must be called before using call3DSpace()
 */
export async function initializeApiService() {
    if (platformConnectorsInitialized) {
        console.log('[ApiService] Already initialized');
        return;
    }

    try {
        if (typeof window !== 'undefined' && window.widget && window.widget.uwaUrl) {
            console.log('[ApiService] Initializing Platform Connectors...');
            await initPlatformConnectors({
                // Skip security contexts since AIAI doesn't use 3DSpace security contexts
                securityContexts: []
            });
            platformConnectorsInitialized = true;
            console.log('[ApiService] Platform Connectors initialized successfully');
        }
    } catch (error) {
        console.warn('[ApiService] Failed to initialize Platform Connectors:', error);
        platformConnectorsInitialized = false;
    }
}

/**
 * Check if we're running in trusted mode (3DDashboard)
 *
 * IMPORTANT: This must be called at RUNTIME, not module load time,
 * because the widget object might not exist yet during module initialization.
 *
 * @returns {boolean} True if running in 3DDashboard with platform connectors available
 */
function isWidgetTrusted() {
    try {
        // Check if we're in a widget environment
        if (typeof window === 'undefined' || !window.widget) {
            return false;
        }

        // Check if call3DSpace is available (platform connectors loaded)
        if (typeof call3DSpace !== 'function') {
            return false;
        }

        // Additional check: verify widget has uwaUrl (indicates proper UWA initialization)
        if (!window.widget.uwaUrl) {
            return false;
        }

        // Check if platform connectors are initialized
        if (!platformConnectorsInitialized) {
            console.log('[ApiService] Platform Connectors not yet initialized');
            return false;
        }

        console.log('[ApiService] Running in trusted mode (3DDashboard)');
        return true;
    } catch (error) {
        console.log('[ApiService] Not in trusted mode:', error.message);
        return false;
    }
}

/**
 * Make an API call with automatic trusted/proxy mode selection
 *
 * Strategy:
 * 1. If in trusted mode: Try direct API call via call3DSpace()
 * 2. If direct call fails or not in trusted mode: Fall back to backend proxy
 *
 * @param {string} url - Full API URL (e.g., https://api.example.com/health)
 * @param {Object} options - Fetch options (method, headers, body, timeout)
 * @param {string} backendUrl - Backend proxy URL (for fallback/standalone)
 * @param {string} proxyPath - Backend proxy path (e.g., /api/health/aiai)
 * @returns {Promise<Object>} API response
 */
async function callWithFallback(url, options = {}, backendUrl = null, proxyPath = null) {
    // Check trusted mode DYNAMICALLY at call time
    const isTrusted = isWidgetTrusted();
    console.log(`[ApiService] callWithFallback - isTrusted: ${isTrusted}, backendUrl: ${backendUrl}, proxyPath: ${proxyPath}`);

    // Strategy 1: Try direct API call if in trusted mode
    if (isTrusted) {
        try {
            console.log(`[ApiService] Direct call to: ${url}`);

            const response = await call3DSpace(url, {
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body,
                timeout: options.timeout || 30000
            });

            console.log('[ApiService] Direct call succeeded');
            return response;
        } catch (error) {
            console.warn(`[ApiService] Direct call failed:`, error);
            console.warn(`[ApiService] Error details - Type: ${typeof error}, Message: ${error?.message || 'no message'}`);
            if (error.backendresponse) console.warn(`[ApiService] Backend response:`, error.backendresponse);
            if (error.response_hdrs) console.warn(`[ApiService] Response headers:`, error.response_hdrs);

            // Fall back to backend proxy if available
            if (backendUrl && proxyPath) {
                console.log('[ApiService] Falling back to backend proxy');
                return await callBackendProxy(backendUrl, proxyPath, options);
            }

            throw error;
        }
    }

    // Strategy 2: Use backend proxy (standalone mode or fallback)
    if (!backendUrl || !proxyPath) {
        throw new Error('Backend proxy not configured for standalone mode. Please start the backend server.');
    }

    console.log(`[ApiService] Using backend proxy: ${backendUrl}${proxyPath}`);
    return await callBackendProxy(backendUrl, proxyPath, options);
}

/**
 * Call backend proxy server
 *
 * @param {string} backendUrl - Backend base URL
 * @param {string} proxyPath - Proxy endpoint path
 * @param {Object} options - Request options
 * @returns {Promise<Object>} Response data
 */
async function callBackendProxy(backendUrl, proxyPath, options = {}) {
    const url = `${backendUrl}${proxyPath}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);

    try {
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : undefined,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        clearTimeout(timeoutId);

        if (error.name === 'AbortError') {
            throw new Error('Request timeout');
        }

        throw error;
    }
}

/**
 * AIAI API Service
 */
export const aiaiService = {
    /**
     * Check AIAI health
     *
     * @param {string} aiaiUrl - AIAI base URL
     * @param {string} backendUrl - Backend URL (for fallback)
     * @returns {Promise<Object>} Health status
     */
    async checkHealth(aiaiUrl, backendUrl) {
        const url = `${aiaiUrl}/health`;
        return await callWithFallback(
            url,
            { method: 'GET' },
            backendUrl,
            `/api/health/aiai?aiai_url=${encodeURIComponent(aiaiUrl)}`
        );
    },

    /**
     * Get assistants list
     *
     * @param {string} aiaiUrl - AIAI base URL
     * @param {string} backendUrl - Backend URL (for fallback)
     * @param {string} namespace - Optional assistant namespace
     * @returns {Promise<Array>} List of assistants
     */
    async getAssistants(aiaiUrl, backendUrl, namespace = '') {
        console.log(`[ApiService] getAssistants called with aiaiUrl: ${aiaiUrl}, backendUrl: ${backendUrl}`);
        const url = `${aiaiUrl}/api/v1/assistants`;

        // Direct call uses GET (AIAI accepts both GET and POST)
        // Backend proxy uses GET with query params
        const options = { method: 'GET' };

        const proxyPath = `/api/aiai/assistants?aiai_url=${encodeURIComponent(aiaiUrl)}${namespace ? `&assistant_namespace=${namespace}` : ''}`;

        try {
            const result = await callWithFallback(url, options, backendUrl, proxyPath);
            console.log('[ApiService] getAssistants succeeded');
            return result;
        } catch (error) {
            console.error('[ApiService] getAssistants failed:', error);
            throw error;
        }
    },

    /**
     * Submit prompt to assistant
     *
     * @param {string} aiaiUrl - AIAI base URL
     * @param {string} backendUrl - Backend URL (for fallback)
     * @param {string} assistantName - Assistant name
     * @param {Object} requestBody - Prompt request body
     * @param {string} namespace - Optional assistant namespace
     * @returns {Promise<Object>} Assistant response
     */
    async submitToAssistant(aiaiUrl, backendUrl, assistantName, requestBody, namespace = '') {
        const url = `${aiaiUrl}/api/v1/assistants/${assistantName}/submit`;

        const options = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: requestBody,  // Pass raw object - callBackendProxy will stringify
            timeout: 60000
        };

        const proxyPath = `/api/aiai/assistants/${assistantName}/submit?aiai_url=${encodeURIComponent(aiaiUrl)}${namespace ? `&assistant_namespace=${namespace}` : ''}`;

        return await callWithFallback(url, options, backendUrl, proxyPath);
    }
};

/**
 * Jaeger API Service
 */
export const jaegerService = {
    /**
     * Get services list
     *
     * @param {string} jaegerUrl - Jaeger base URL
     * @param {string} backendUrl - Backend URL (for fallback)
     * @returns {Promise<Array>} List of services
     */
    async getServices(jaegerUrl, backendUrl) {
        const url = `${jaegerUrl}/api/services`;
        return await callWithFallback(
            url,
            { method: 'GET' },
            backendUrl,
            '/api/jaeger/services'
        );
    },

    /**
     * Search traces by conversation ID
     *
     * @param {string} jaegerUrl - Jaeger base URL
     * @param {string} backendUrl - Backend URL (required for trace search)
     * @param {string} conversationId - Conversation ID to search
     * @param {number} limit - Max results
     * @returns {Promise<Array>} Trace results
     */
    async searchTraces(jaegerUrl, backendUrl, conversationId, limit = 10) {
        // Trace search is complex and requires backend aggregation
        const proxyPath = `/api/traces/search?conversation_id=${conversationId}&limit=${limit}`;
        return await callBackendProxy(backendUrl, proxyPath, { method: 'GET' });
    }
};

/**
 * Health Check Service - Aggregated
 */
export const healthService = {
    /**
     * Get all component health (uses backend aggregator)
     *
     * @param {string} backendUrl - Backend URL
     * @returns {Promise<Object>} Aggregated health status
     */
    async checkAll(backendUrl) {
        return await callBackendProxy(backendUrl, '/api/health/all', { method: 'GET' });
    }
};

/**
 * Get connection mode information
 *
 * @returns {Object} Connection mode details
 */
export function getConnectionMode() {
    const isTrusted = isWidgetTrusted();

    return {
        mode: isTrusted ? 'direct' : 'proxy',
        description: isTrusted
            ? 'Direct API calls via 3DDashboard (trusted mode)'
            : 'Using backend proxy (standalone mode)',
        isTrusted: isTrusted
    };
}

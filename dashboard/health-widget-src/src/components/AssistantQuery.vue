<template>
  <v-card>
    <v-card-title>
      <v-icon left color="primary">mdi-robot-outline</v-icon>
      Query AI Assistant
    </v-card-title>

    <v-card-text>
      <!-- Assistant Selection -->
      <v-row>
        <v-col cols="12" md="6">
          <v-select
            v-model="selectedAssistant"
            :items="assistants"
            item-text="text"
            item-value="value"
            label="Assistant"
            outlined
            dense
            prepend-inner-icon="mdi-robot"
            :loading="loadingAssistants"
            :disabled="loading || loadingAssistants"
            hint="Select AI assistant to query"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="conversationId"
            label="Conversation ID (optional)"
            outlined
            dense
            prepend-inner-icon="mdi-message-text-outline"
            :disabled="loading"
            placeholder="Leave empty for new conversation"
          />
        </v-col>
      </v-row>

      <!-- Prompt Input -->
      <v-row>
        <v-col cols="12">
          <v-textarea
            v-model="prompt"
            label="Prompt"
            outlined
            rows="4"
            placeholder="Enter your prompt here... (e.g., 'create a product structure for a toy car')"
            :disabled="loading"
            counter
          />
        </v-col>
      </v-row>

      <!-- Advanced Options (Expandable) -->
      <v-expansion-panels flat>
        <v-expansion-panel>
          <v-expansion-panel-header>
            <span>
              <v-icon left small>mdi-tune</v-icon>
              Advanced Options
            </span>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="model"
                  :items="availableModels"
                  label="LLM Model"
                  outlined
                  dense
                  :disabled="loading"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="language"
                  :items="languages"
                  label="Prompt Language"
                  outlined
                  dense
                  :disabled="loading"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12" md="4">
                <v-switch
                  v-model="streamEnabled"
                  label="Enable Streaming"
                  :disabled="loading"
                  dense
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-switch
                  v-model="mockMode"
                  label="Mock Mode"
                  :disabled="loading"
                  dense
                  hint="Use mock data for testing"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-switch
                  v-model="isNoCodeCompanion"
                  label="NoCode Companion"
                  :disabled="loading"
                  dense
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-textarea
                  v-model="contextJson"
                  label="Context (JSON)"
                  outlined
                  rows="3"
                  placeholder='{"message": {"selected_dimensions": {...}}}'
                  :disabled="loading"
                  dense
                />
              </v-col>
            </v-row>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Action Buttons -->
      <v-row class="mt-4">
        <v-col cols="12" class="d-flex gap-2">
          <v-btn
            color="primary"
            :loading="loading"
            :disabled="!prompt || !selectedAssistant"
            @click="submitQuery"
          >
            <v-icon left>mdi-send</v-icon>
            Submit Query
          </v-btn>
          <v-btn
            outlined
            :disabled="loading"
            @click="clearForm"
          >
            <v-icon left>mdi-close</v-icon>
            Clear
          </v-btn>
          <v-spacer />
          <v-btn
            text
            small
            :disabled="!response"
            @click="copyResponse"
          >
            <v-icon left small>mdi-content-copy</v-icon>
            Copy Response
          </v-btn>
        </v-col>
      </v-row>

      <!-- Response Display -->
      <v-divider class="my-4" />

      <div v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="48" />
        <p class="mt-4 text-subtitle-1">Processing your request...</p>
      </div>

      <div v-else-if="error" class="mt-4">
        <v-alert type="error" outlined>
          <div class="text-h6">Error</div>
          <div>{{ error }}</div>
        </v-alert>
      </div>

      <div v-else-if="response" class="mt-4">
        <!-- Summary Section -->
        <v-card outlined class="mb-4">
          <v-card-subtitle class="pb-0">
            <v-icon left small color="info">mdi-information</v-icon>
            Summary
          </v-card-subtitle>
          <v-card-text>
            <div class="text-body-1">{{ response.summary }}</div>
          </v-card-text>
        </v-card>

        <!-- Structure Section -->
        <v-card outlined>
          <v-card-subtitle class="pb-0 d-flex align-center">
            <v-icon left small color="success">mdi-file-tree</v-icon>
            Structure
            <v-spacer />
            <v-btn-toggle v-model="viewMode" dense mandatory>
              <v-btn small value="tree">
                <v-icon small>mdi-file-tree</v-icon>
                Tree
              </v-btn>
              <v-btn small value="json">
                <v-icon small>mdi-code-json</v-icon>
                JSON
              </v-btn>
            </v-btn-toggle>
          </v-card-subtitle>
          <v-card-text>
            <!-- Tree View -->
            <div v-if="viewMode === 'tree'" class="structure-tree">
              <tree-node :node="response.structure" :level="0" />
            </div>

            <!-- JSON View -->
            <pre v-else class="json-view">{{ JSON.stringify(response.structure, null, 2) }}</pre>
          </v-card-text>
        </v-card>

        <!-- Metadata -->
        <v-card outlined class="mt-4">
          <v-card-subtitle class="pb-0">
            <v-icon left small>mdi-chart-box-outline</v-icon>
            Response Metadata
          </v-card-subtitle>
          <v-card-text>
            <v-simple-table dense>
              <template v-slot:default>
                <tbody>
                  <tr>
                    <td class="font-weight-bold">Model</td>
                    <td>{{ response.metadata.model || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <td class="font-weight-bold">Tokens (Total)</td>
                    <td>{{ response.metadata.totalTokens || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <td class="font-weight-bold">Finish Reason</td>
                    <td>{{ response.metadata.finishReason || 'N/A' }}</td>
                  </tr>
                  <tr>
                    <td class="font-weight-bold">Timestamp</td>
                    <td>{{ formatTimestamp(response.metadata.timestamp) }}</td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </v-card-text>
        </v-card>
      </div>

      <div v-else class="text-center py-8 grey--text">
        <v-icon size="64" color="grey lighten-1">mdi-robot-outline</v-icon>
        <p class="mt-4 text-subtitle-1">Submit a query to see results</p>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { aiaiService } from '../services/apiService';

// Tree node component for hierarchical structure display (using plain HTML)
const TreeNode = {
  name: 'TreeNode',
  props: {
    node: {
      type: Object,
      required: true
    },
    level: {
      type: Number,
      default: 0
    }
  },
  template: `
    <div :style="{ marginLeft: (level * 20) + 'px' }" class="tree-node">
      <div class="node-header">
        <span :class="['node-icon', hasChildren ? 'folder' : 'file']">
          {{ hasChildren ? '📁' : '📄' }}
        </span>
        <span class="node-name">{{ node.name }}</span>
        <span v-if="node.quantity" class="node-quantity">
          Qty: {{ node.quantity }}
        </span>
      </div>
      <div v-if="hasChildren" class="node-children">
        <tree-node
          v-for="(child, index) in node.components"
          :key="index"
          :node="child"
          :level="level + 1"
        />
      </div>
    </div>
  `,
  computed: {
    hasChildren() {
      return this.node.components && this.node.components.length > 0;
    }
  }
};

export default {
  name: 'AssistantQuery',

  components: {
    TreeNode
  },

  data() {
    return {
      // Form fields
      selectedAssistant: '',
      prompt: '',
      conversationId: '',
      model: 'mistralai/mistral-small-2506',
      language: 'en',
      streamEnabled: false,
      mockMode: false,
      isNoCodeCompanion: false,
      contextJson: '',

      // UI state
      loading: false,
      loadingAssistants: false,
      error: null,
      response: null,
      viewMode: 'tree',

      // API URLs (loaded from widget preferences)
      aiaiUrl: 'https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com',
      backendUrl: 'http://localhost:8080',

      // Options
      assistants: [],
      availableModels: [
        'mistralai/mistral-small-2506',
        'mistralai/mistral-large-2411',
        'anthropic/claude-3-5-sonnet-20241022',
        'openai/gpt-4o-2024-11-20'
      ],
      languages: [
        { text: 'English', value: 'en' },
        { text: 'French', value: 'fr' },
        { text: 'German', value: 'de' },
        { text: 'Spanish', value: 'es' }
      ]
    };
  },

  mounted() {
    console.log('[AssistantQuery] Component mounted');

    // Load AIAI URL from widget preferences if available
    if (typeof widget !== 'undefined' && widget.getValue) {
      try {
        this.aiaiUrl = widget.getValue('aiaiUrl') || this.aiaiUrl;
        console.log('[AssistantQuery] Loaded aiaiUrl from preferences:', this.aiaiUrl);
      } catch (error) {
        console.warn('[AssistantQuery] Could not load widget preferences:', error);
      }
    }

    // Fetch available assistants
    this.fetchAssistants();
  },

  methods: {
    /**
     * Fetch available assistants from AIAI
     */
    async fetchAssistants() {
      this.loadingAssistants = true;

      try {
        console.log('[AssistantQuery] Fetching assistants from:', this.aiaiUrl);
        const assistantList = await aiaiService.getAssistants(this.aiaiUrl, this.backendUrl);

        // Log raw API response to debug format
        console.log('[AssistantQuery] Raw assistant list:', assistantList);
        console.log('[AssistantQuery] First assistant:', assistantList[0]);
        console.log('[AssistantQuery] First assistant keys:', Object.keys(assistantList[0] || {}));

        // Transform to select options format (use assistant__ prefixed properties)
        this.assistants = assistantList.map(asst => ({
          text: asst.assistant__description || asst.assistant__name || asst.assistant__id,
          value: asst.assistant__name || asst.assistant__id
        }));

        // Set default selection to first assistant (or asmstruct if available)
        if (this.assistants.length > 0) {
          const asmstruct = this.assistants.find(a => a.value === 'asmstruct');
          this.selectedAssistant = asmstruct ? asmstruct.value : this.assistants[0].value;
        }

        console.log('[AssistantQuery] Loaded assistants:', this.assistants);
      } catch (err) {
        console.error('[AssistantQuery] Failed to load assistants:', err);
        // Use fallback assistant
        this.assistants = [
          { text: 'Assembly Structure (asmstruct)', value: 'asmstruct' }
        ];
        this.selectedAssistant = 'asmstruct';
      } finally {
        this.loadingAssistants = false;
      }
    },
    /**
     * Submit query to assistant
     */
    async submitQuery() {
      console.log('[AssistantQuery] Submitting query to:', this.selectedAssistant);

      this.loading = true;
      this.error = null;
      this.response = null;

      try {
        // Use mock response if mock mode enabled
        if (this.mockMode) {
          console.log('[AssistantQuery] Using mock mode');
          await new Promise(resolve => setTimeout(resolve, 1500));
          this.response = this.parseMockResponse();
          return;
        }

        // Build request body matching curl example
        const requestBody = {
          prompt: this.prompt,
          'llm.stream': this.streamEnabled,
          'llm.model': this.model,
          prompt_language: this.language,
          mock: this.mockMode
        };

        // Add optional fields
        if (this.conversationId) {
          requestBody.conversation_id = this.conversationId;
        }

        if (this.contextJson) {
          try {
            requestBody.context = JSON.parse(this.contextJson);
          } catch (err) {
            throw new Error(`Invalid context JSON: ${err.message}`);
          }
        }

        console.log('[AssistantQuery] Request body:', requestBody);

        // Call AIAI API
        const result = await aiaiService.submitToAssistant(
          this.aiaiUrl,
          this.backendUrl,
          this.selectedAssistant,
          requestBody,
          '' // namespace (empty for now)
        );

        console.log('[AssistantQuery] API response:', result);

        // Parse response
        this.response = this.parseResponse(result);
        console.log('[AssistantQuery] Parsed response:', this.response);
      } catch (err) {
        console.error('[AssistantQuery] Error submitting query:', err);
        this.error = err.message || 'Failed to submit query';
      } finally {
        this.loading = false;
      }
    },

    /**
     * Parse real API response
     */
    parseResponse(apiResponse) {
      try {
        // Extract content from LLM response
        const content = apiResponse.llm?.choices?.[0]?.message?.content;

        if (!content) {
          throw new Error('No content in API response');
        }

        // Remove [asmstruct] prefix if present
        const jsonStart = content.indexOf('{');
        if (jsonStart === -1) {
          throw new Error('No JSON found in response');
        }

        const jsonStr = content.substring(jsonStart);
        const parsed = JSON.parse(jsonStr);

        return {
          summary: parsed.summary || 'No summary provided',
          structure: parsed.structure || {},
          metadata: {
            model: apiResponse.llm?.model || 'N/A',
            totalTokens: apiResponse.llm?.usage?.total_tokens || 0,
            finishReason: apiResponse.llm?.choices?.[0]?.finish_reason || 'N/A',
            timestamp: apiResponse.llm?.created || Math.floor(Date.now() / 1000)
          }
        };
      } catch (err) {
        console.error('[AssistantQuery] Failed to parse response:', err);
        throw new Error(`Failed to parse response: ${err.message}`);
      }
    },

    /**
     * Parse mock response (simulates real API response)
     */
    parseMockResponse() {
      // Simulating the response from the curl example
      const mockLlmResponse = {
        llm: {
          id: '2659f08b-3e8c-42c3-b21f-dae95a33264f',
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: this.model,
          choices: [
            {
              message: {
                content: '[asmstruct] {\n  "summary": "Here is the product structure for a toy car",\n  "structure": {\n    "name": "Toy Car",\n    "components": [\n      {\n        "name": "chassis",\n        "quantity": 1,\n        "components": [\n          {\n            "name": "body",\n            "quantity": 1\n          },\n          {\n            "name": "wheels",\n            "quantity": 4\n          }\n        ]\n      },\n      {\n        "name": "engine",\n        "quantity": 1\n      },\n      {\n        "name": "battery",\n        "quantity": 1\n      },\n      {\n        "name": "remote control",\n        "quantity": 1\n      }\n    ]\n  }\n}',
                role: 'assistant'
              },
              index: 0,
              logprobs: -1,
              finish_reason: 'stop'
            }
          ],
          usage: {
            prompt_tokens: 120,
            completion_tokens: 85,
            total_tokens: 205
          }
        }
      };

      // Extract content from response
      const content = mockLlmResponse.llm.choices[0].message.content;

      // Remove [asmstruct] prefix and parse JSON
      const jsonStart = content.indexOf('{');
      const jsonStr = content.substring(jsonStart);
      const parsed = JSON.parse(jsonStr);

      return {
        summary: parsed.summary,
        structure: parsed.structure,
        metadata: {
          model: mockLlmResponse.llm.model,
          totalTokens: mockLlmResponse.llm.usage.total_tokens,
          finishReason: mockLlmResponse.llm.choices[0].finish_reason,
          timestamp: mockLlmResponse.llm.created
        }
      };
    },

    /**
     * Clear form
     */
    clearForm() {
      this.prompt = '';
      this.conversationId = '';
      this.contextJson = '';
      this.error = null;
      this.response = null;
    },

    /**
     * Copy response to clipboard
     */
    copyResponse() {
      if (!this.response) return;

      const text = JSON.stringify(this.response.structure, null, 2);
      navigator.clipboard.writeText(text).then(() => {
        console.log('[AssistantQuery] Response copied to clipboard');
        // TODO: Show snackbar notification
      });
    },

    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A';
      return new Date(timestamp * 1000).toLocaleString();
    }
  }
};
</script>

<style scoped>
.structure-tree {
  font-family: monospace;
  font-size: 14px;
}

.tree-node {
  margin-bottom: 4px;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 4px 0;
}

.node-icon {
  font-size: 16px;
  line-height: 1;
}

.node-name {
  margin-left: 8px;
  font-weight: 500;
  font-size: 14px;
}

.node-quantity {
  margin-left: 8px;
  padding: 2px 8px;
  background-color: #e3f2fd;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  color: #1976d2;
}

.node-children {
  margin-top: 4px;
}

.json-view {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.gap-2 {
  gap: 8px;
}
</style>

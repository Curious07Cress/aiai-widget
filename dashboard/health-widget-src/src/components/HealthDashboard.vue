<template>
  <v-app>
    <v-container fluid class="pa-4">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <v-card flat class="mb-4">
            <v-card-title class="text-h5">
              <v-icon left large color="primary">mdi-monitor-dashboard</v-icon>
              AI Assistant Health Dashboard
            </v-card-title>
            <v-card-subtitle>
              <v-chip small :color="connectionMode.isTrusted ? 'success' : 'info'" class="mr-2">
                <v-icon left small>{{ connectionMode.isTrusted ? 'mdi-shield-check' : 'mdi-server' }}</v-icon>
                {{ connectionMode.description }}
              </v-chip>
              <v-chip small outlined>
                <v-icon left small>mdi-clock-outline</v-icon>
                Auto-refresh: {{ refreshInterval }}s
              </v-chip>
            </v-card-subtitle>
          </v-card>
        </v-col>
      </v-row>

      <!-- Loading State -->
      <v-row v-if="loading && !healthData">
        <v-col cols="12" class="text-center">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          <p class="mt-4 text-h6">Loading health data...</p>
        </v-col>
      </v-row>

      <!-- Error State -->
      <v-row v-else-if="error">
        <v-col cols="12">
          <v-alert type="error" prominent>
            <v-row align="center">
              <v-col class="grow">
                <div class="text-h6">Failed to load health data</div>
                <div>{{ error }}</div>
              </v-col>
              <v-col class="shrink">
                <v-btn color="white" outlined @click="refreshHealth">
                  <v-icon left>mdi-refresh</v-icon>
                  Retry
                </v-btn>
              </v-col>
            </v-row>
          </v-alert>
        </v-col>
      </v-row>

      <!-- Health Status Cards -->
      <v-row v-else-if="healthData">
        <!-- Overall Status -->
        <v-col cols="12" md="4">
          <status-card
            title="Overall Status"
            :status="healthData.overall"
            icon="mdi-heart-pulse"
            :timestamp="healthData.timestamp"
            @card-click="showDetailsDialog"
            @card-refresh="refreshService"
          />
        </v-col>

        <!-- AIAI Service -->
        <v-col cols="12" md="4">
          <status-card
            title="AIAI Service"
            :status="(healthData.services && healthData.services.aiai && healthData.services.aiai.status) || 'unknown'"
            icon="mdi-robot"
            :details="healthData.services && healthData.services.aiai"
            @card-click="showDetailsDialog"
            @card-refresh="refreshService"
          />
        </v-col>

        <!-- MCP Service -->
        <v-col cols="12" md="4">
          <div class="position-relative">
            <v-chip
              small
              color="warning"
              class="mcp-dev-tag"
              label
            >
              Under Development
            </v-chip>
            <status-card
              title="MCP Service"
              :status="(healthData.services && healthData.services.mcp && healthData.services.mcp.status) || 'unknown'"
              icon="mdi-api"
              :details="healthData.services && healthData.services.mcp"
              @card-click="showDetailsDialog"
              @card-refresh="refreshService"
            />
          </div>
        </v-col>
      </v-row>

      <!-- AIAI Query Tool -->
      <v-row>
        <v-col cols="12">
          <assistant-query />
        </v-col>
      </v-row>

      <!-- Service Information -->
      <v-row v-if="healthData && supervisionData">
        <v-col cols="12">
          <service-info :data="supervisionData" />
        </v-col>
      </v-row>

      <!-- Footer with Refresh Button -->
      <v-row>
        <v-col cols="12" class="text-center">
          <v-btn
            color="primary"
            :loading="loading"
            @click="refreshHealth"
            class="mr-2"
          >
            <v-icon left>mdi-refresh</v-icon>
            Refresh Now
          </v-btn>
          <v-btn
            outlined
            @click="openSettings"
          >
            <v-icon left>mdi-cog</v-icon>
            Settings
          </v-btn>
        </v-col>
      </v-row>
    </v-container>

    <!-- Settings Dialog -->
    <v-dialog v-model="showSettings" max-width="600px">
      <v-card>
        <v-card-title>
          <v-icon left>mdi-cog</v-icon>
          Widget Settings
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="settingsForm.aiaiUrl"
            label="AIAI API URL"
            outlined
            dense
            hint="Base URL for AIAI service"
            persistent-hint
          />
          <v-text-field
            v-model.number="settingsForm.refreshInterval"
            label="Auto-refresh Interval (seconds)"
            outlined
            dense
            type="number"
            min="10"
            hint="How often to refresh health data"
            persistent-hint
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeSettings">Cancel</v-btn>
          <v-btn color="primary" @click="saveSettings">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Service Details Dialog -->
    <v-dialog v-model="showDetails" max-width="700px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon left large :color="detailsData.statusColor">{{ detailsData.icon }}</v-icon>
          {{ detailsData.title }}
          <v-spacer />
          <v-chip :color="detailsData.statusColor" dark small>
            {{ detailsData.status }}
          </v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text class="pt-4">
          <div v-if="detailsData.timestamp" class="mb-3">
            <v-icon small left>mdi-clock-outline</v-icon>
            <strong>Last Updated:</strong> {{ formatTimestamp(detailsData.timestamp) }}
          </div>

          <div v-if="detailsData.details">
            <v-simple-table dense>
              <template v-slot:default>
                <tbody>
                  <tr v-for="(value, key) in detailsData.details" :key="key">
                    <td class="font-weight-bold">{{ formatDetailKey(key) }}</td>
                    <td>{{ formatDetailValue(value) }}</td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </div>

          <v-alert v-else type="info" text class="mt-2">
            No additional details available for this service.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showDetails = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script>
import { aiaiService, healthService, getConnectionMode } from '../services/apiService';
import StatusCard from './StatusCard.vue';
import ServiceInfo from './ServiceInfo.vue';
import AssistantQuery from './AssistantQuery.vue';

export default {
  name: 'HealthDashboard',

  components: {
    StatusCard,
    ServiceInfo,
    AssistantQuery
  },

  data() {
    return {
      loading: false,
      error: null,
      healthData: null,
      supervisionData: null,
      connectionMode: {},
      refreshInterval: 30,
      autoRefreshTimer: null,

      // Widget preferences (will be populated from widget.getValue())
      aiaiUrl: 'https://devopsyivwvbl820289-euw1-devprol50-aiai.3dx-staging.3ds.com',
      backendUrl: 'http://localhost:8080',

      // Settings dialog
      showSettings: false,
      settingsForm: {
        aiaiUrl: '',
        refreshInterval: 30
      },

      // Details dialog
      showDetails: false,
      detailsData: {
        title: '',
        status: '',
        statusColor: '',
        icon: '',
        timestamp: null,
        details: null
      }
    };
  },

  mounted() {
    console.log('[HealthDashboard] Component mounted');

    // Load preferences from widget
    this.loadPreferences();

    // Get connection mode
    this.connectionMode = getConnectionMode();
    console.log('[HealthDashboard] Connection mode:', this.connectionMode);

    // Initial data load
    this.refreshHealth();

    // Set up auto-refresh
    this.startAutoRefresh();
  },

  beforeDestroy() {
    this.stopAutoRefresh();
  },

  methods: {
    /**
     * Load preferences from widget
     */
    loadPreferences() {
      if (typeof widget !== 'undefined' && widget.getValue) {
        try {
          this.aiaiUrl = widget.getValue('aiaiUrl') || this.aiaiUrl;
          this.refreshInterval = parseInt(widget.getValue('refreshInterval')) || this.refreshInterval;
          console.log('[HealthDashboard] Loaded preferences:', {
            aiaiUrl: this.aiaiUrl,
            refreshInterval: this.refreshInterval
          });
        } catch (error) {
          console.warn('[HealthDashboard] Could not load widget preferences:', error);
        }
      }
    },

    /**
     * Refresh health data
     */
    async refreshHealth() {
      this.loading = true;
      this.error = null;

      try {
        console.log('[HealthDashboard] Fetching health data...');

        // Fetch aggregated health (this works in both modes)
        const health = await healthService.checkAll(this.backendUrl);
        this.healthData = health;

        console.log('[HealthDashboard] Health data received:', health);

        // Optionally fetch supervision data (if backend available)
        try {
          const response = await fetch(`${this.backendUrl}/api/supervision/derive?aiai_url=${encodeURIComponent(this.aiaiUrl)}`);
          if (response.ok) {
            this.supervisionData = await response.json();
          }
        } catch (err) {
          console.log('[HealthDashboard] Supervision data not available:', err.message);
        }

      } catch (err) {
        console.error('[HealthDashboard] Failed to fetch health data:', err);
        this.error = err.message || 'Unknown error occurred';
      } finally {
        this.loading = false;
      }
    },

    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
      if (this.autoRefreshTimer) {
        clearInterval(this.autoRefreshTimer);
      }

      this.autoRefreshTimer = setInterval(() => {
        console.log('[HealthDashboard] Auto-refresh triggered');
        this.refreshHealth();
      }, this.refreshInterval * 1000);
    },

    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
      if (this.autoRefreshTimer) {
        clearInterval(this.autoRefreshTimer);
        this.autoRefreshTimer = null;
      }
    },

    /**
     * Open settings dialog
     */
    openSettings() {
      console.log('[HealthDashboard] Opening settings dialog');

      // Load current values into form
      this.settingsForm.aiaiUrl = this.aiaiUrl;
      this.settingsForm.refreshInterval = this.refreshInterval;

      this.showSettings = true;
    },

    /**
     * Close settings dialog without saving
     */
    closeSettings() {
      this.showSettings = false;
    },

    /**
     * Save settings and apply changes
     */
    saveSettings() {
      console.log('[HealthDashboard] Saving settings:', this.settingsForm);

      // Update local state
      this.aiaiUrl = this.settingsForm.aiaiUrl;
      this.refreshInterval = this.settingsForm.refreshInterval;

      // Persist to widget preferences (if available)
      if (typeof widget !== 'undefined' && widget.setValue) {
        try {
          widget.setValue('aiaiUrl', this.aiaiUrl);
          widget.setValue('refreshInterval', String(this.refreshInterval));
          console.log('[HealthDashboard] Settings saved to widget preferences');
        } catch (error) {
          console.warn('[HealthDashboard] Could not save to widget preferences:', error);
        }
      }

      // Restart auto-refresh with new interval
      this.stopAutoRefresh();
      this.startAutoRefresh();

      // Refresh health data with new URL
      this.refreshHealth();

      this.showSettings = false;
    },

    /**
     * Show details dialog for a service
     */
    showDetailsDialog(cardData) {
      console.log('[HealthDashboard] Showing details for:', cardData.title);

      // Determine icon based on title
      let icon = 'mdi-information';
      if (cardData.title.includes('Overall')) {
        icon = 'mdi-heart-pulse';
      } else if (cardData.title.includes('AIAI')) {
        icon = 'mdi-robot';
      } else if (cardData.title.includes('MCP')) {
        icon = 'mdi-api';
      }

      // Determine status color
      const statusLower = cardData.status.toLowerCase();
      let statusColor = 'grey';
      if (statusLower === 'healthy' || statusLower === 'ok') {
        statusColor = 'success';
      } else if (statusLower === 'degraded' || statusLower === 'warning') {
        statusColor = 'warning';
      } else if (statusLower === 'unhealthy' || statusLower === 'error') {
        statusColor = 'error';
      }

      this.detailsData = {
        title: cardData.title,
        status: cardData.status.toUpperCase(),
        statusColor: statusColor,
        icon: icon,
        timestamp: cardData.timestamp,
        details: cardData.details
      };

      this.showDetails = true;
    },

    /**
     * Refresh a specific service
     */
    async refreshService(cardData) {
      console.log('[HealthDashboard] Refreshing service:', cardData.title);
      await this.refreshHealth();
    },

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A';

      try {
        const date = new Date(timestamp);
        return date.toLocaleString();
      } catch (error) {
        return timestamp;
      }
    },

    /**
     * Format detail key for display
     */
    formatDetailKey(key) {
      return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Format detail value for display
     */
    formatDetailValue(value) {
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
      }
      if (value === null || value === undefined) {
        return 'N/A';
      }
      if (typeof value === 'object') {
        return JSON.stringify(value, null, 2);
      }
      return String(value);
    }
  }
};
</script>

<style scoped>
.v-application {
  background-color: #f5f5f5;
}

.v-card {
  transition: all 0.3s ease;
}

.v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.position-relative {
  position: relative;
}

.mcp-dev-tag {
  position: absolute;
  top: -8px;
  right: 8px;
  z-index: 1;
}
</style>

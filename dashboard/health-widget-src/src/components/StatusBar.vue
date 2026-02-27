<template>
  <v-card flat outlined class="status-bar">
    <v-card-text class="py-2 px-4">
      <v-row align="center" class="ma-0">
        <!-- Overall Status -->
        <v-col cols="auto" class="pa-0 pr-4">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-bind="attrs" v-on="on" class="status-item">
                <span class="status-label">Status:</span>
                <v-icon :color="overallStatusColor" small class="mx-1">mdi-circle</v-icon>
                <span class="status-text">{{ overallStatusText }}</span>
              </div>
            </template>
            <span>Overall system health status</span>
          </v-tooltip>
        </v-col>

        <v-divider vertical class="mx-2"></v-divider>

        <!-- AIAI Service -->
        <v-col cols="auto" class="pa-0 pr-4">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-bind="attrs" v-on="on" class="status-item">
                <span class="status-label">AIAI:</span>
                <v-icon :color="aiaiStatusColor" small class="mx-1">mdi-circle</v-icon>
                <span class="status-text">{{ aiaiResponseTime }}</span>
              </div>
            </template>
            <div>
              <div><strong>AIAI Service Status:</strong> {{ aiaiStatus }}</div>
              <div v-if="aiaiDetails">
                <div v-if="aiaiDetails.assistant_count">
                  <strong>Assistants:</strong> {{ aiaiDetails.assistant_count }}
                </div>
                <div v-if="aiaiDetails.endpoint">
                  <strong>Endpoint:</strong> {{ aiaiDetails.endpoint }}
                </div>
              </div>
            </div>
          </v-tooltip>
        </v-col>

        <v-divider vertical class="mx-2"></v-divider>

        <!-- Last Updated -->
        <v-col cols="auto" class="pa-0 pr-2">
          <div class="status-item">
            <v-icon small class="mr-1">mdi-clock-outline</v-icon>
            <span class="status-label">Updated:</span>
            <span class="status-text ml-1">{{ lastUpdatedText }}</span>
          </div>
        </v-col>

        <!-- Refresh Button -->
        <v-col cols="auto" class="pa-0">
          <v-btn
            icon
            x-small
            :loading="loading"
            @click="handleRefresh"
            class="refresh-btn"
          >
            <v-icon small>mdi-refresh</v-icon>
          </v-btn>
        </v-col>

        <v-spacer></v-spacer>

        <!-- Historical indicator (optional for Phase 2) -->
        <v-col v-if="showUptime" cols="auto" class="pa-0">
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <div v-bind="attrs" v-on="on" class="status-item text-caption">
                <v-icon x-small class="mr-1">mdi-chart-line</v-icon>
                <span>{{ uptimePercentage }}% uptime</span>
              </div>
            </template>
            <span>24-hour uptime percentage</span>
          </v-tooltip>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'StatusBar',

  props: {
    healthData: {
      type: Object,
      default: null
    },
    loading: {
      type: Boolean,
      default: false
    },
    showUptime: {
      type: Boolean,
      default: false
    },
    uptimePercentage: {
      type: Number,
      default: 100
    }
  },

  computed: {
    /**
     * Overall status text
     */
    overallStatusText() {
      if (!this.healthData || !this.healthData.overall) return 'Unknown';
      return this.capitalize(this.healthData.overall);
    },

    /**
     * Overall status color
     */
    overallStatusColor() {
      return this.getStatusColor(this.healthData?.overall);
    },

    /**
     * AIAI status
     */
    aiaiStatus() {
      return this.healthData?.services?.aiai?.status || 'unknown';
    },

    /**
     * AIAI status color
     */
    aiaiStatusColor() {
      return this.getStatusColor(this.aiaiStatus);
    },

    /**
     * AIAI response time display
     */
    aiaiResponseTime() {
      const responseTime = this.healthData?.services?.aiai?.response_time_ms;
      if (responseTime === null || responseTime === undefined) {
        return 'N/A';
      }
      return `${responseTime}ms`;
    },

    /**
     * AIAI service details for tooltip
     */
    aiaiDetails() {
      return this.healthData?.services?.aiai?.details || null;
    },

    /**
     * Last updated timestamp text
     */
    lastUpdatedText() {
      if (!this.healthData || !this.healthData.timestamp) return 'Never';

      try {
        const timestamp = new Date(this.healthData.timestamp);
        const now = new Date();
        const diffMs = now - timestamp;
        const diffSec = Math.floor(diffMs / 1000);

        if (diffSec < 5) return 'Just now';
        if (diffSec < 60) return `${diffSec}s ago`;

        const diffMin = Math.floor(diffSec / 60);
        if (diffMin < 60) return `${diffMin}m ago`;

        const diffHour = Math.floor(diffMin / 60);
        return `${diffHour}h ago`;
      } catch (error) {
        return 'Unknown';
      }
    }
  },

  methods: {
    /**
     * Get color based on status
     */
    getStatusColor(status) {
      if (!status) return 'grey';

      const statusLower = status.toLowerCase();

      if (statusLower === 'healthy' || statusLower === 'ok') {
        return 'success';
      } else if (statusLower === 'degraded' || statusLower === 'warning') {
        return 'warning';
      } else if (statusLower === 'unhealthy' || statusLower === 'error') {
        return 'error';
      } else {
        return 'grey';
      }
    },

    /**
     * Capitalize first letter
     */
    capitalize(str) {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * Handle refresh button click
     */
    handleRefresh() {
      console.log('[StatusBar] Refresh button clicked');
      this.$emit('refresh');
    }
  }
};
</script>

<style scoped>
.status-bar {
  border-left: 4px solid transparent;
  transition: border-color 0.3s ease;
}

.status-bar.healthy {
  border-left-color: #4caf50;
}

.status-bar.degraded {
  border-left-color: #ff9800;
}

.status-bar.unhealthy {
  border-left-color: #f44336;
}

.status-item {
  display: inline-flex;
  align-items: center;
  font-size: 14px;
}

.status-label {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  margin-right: 4px;
}

.status-text {
  font-weight: 600;
  color: rgba(0, 0, 0, 0.87);
}

.refresh-btn {
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.refresh-btn:hover {
  opacity: 1;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .status-item {
    font-size: 12px;
  }
}
</style>

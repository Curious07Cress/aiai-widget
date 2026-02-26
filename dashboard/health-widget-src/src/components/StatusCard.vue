<template>
  <v-card :color="statusColor" dark class="status-card">
    <v-card-title class="pb-2">
      <v-icon left large>{{ icon }}</v-icon>
      <span class="text-h6">{{ title }}</span>
    </v-card-title>

    <v-card-text class="pt-2">
      <div class="text-h4 font-weight-bold mb-2">
        {{ statusText }}
      </div>

      <div v-if="timestamp" class="text-caption opacity-80">
        <v-icon small>mdi-clock-outline</v-icon>
        {{ formattedTimestamp }}
      </div>

      <div v-if="details" class="mt-3">
        <v-divider class="my-2 opacity-50"></v-divider>
        <div v-for="(value, key) in detailsFiltered" :key="key" class="text-caption">
          <strong>{{ formatKey(key) }}:</strong> {{ formatValue(value) }}
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'StatusCard',

  props: {
    title: {
      type: String,
      required: true
    },
    status: {
      type: String,
      default: 'unknown'
    },
    icon: {
      type: String,
      default: 'mdi-information'
    },
    timestamp: {
      type: String,
      default: null
    },
    details: {
      type: Object,
      default: null
    }
  },

  computed: {
    /**
     * Status text (capitalized)
     */
    statusText() {
      return this.status.toUpperCase();
    },

    /**
     * Color based on status
     */
    statusColor() {
      const statusLower = this.status.toLowerCase();

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
     * Formatted timestamp
     */
    formattedTimestamp() {
      if (!this.timestamp) return '';

      try {
        const date = new Date(this.timestamp);
        return date.toLocaleString();
      } catch (error) {
        return this.timestamp;
      }
    },

    /**
     * Filtered details (exclude 'status' key since it's shown in title)
     */
    detailsFiltered() {
      if (!this.details) return null;

      const filtered = { ...this.details };
      delete filtered.status;
      return Object.keys(filtered).length > 0 ? filtered : null;
    }
  },

  methods: {
    /**
     * Format detail key for display
     */
    formatKey(key) {
      return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Format detail value for display
     */
    formatValue(value) {
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
      }
      if (value === null || value === undefined) {
        return 'N/A';
      }
      if (typeof value === 'object') {
        return JSON.stringify(value);
      }
      return String(value);
    }
  }
};
</script>

<style scoped>
.status-card {
  height: 100%;
  transition: all 0.3s ease;
}

.status-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}

.opacity-80 {
  opacity: 0.8;
}

.opacity-50 {
  opacity: 0.5;
}
</style>

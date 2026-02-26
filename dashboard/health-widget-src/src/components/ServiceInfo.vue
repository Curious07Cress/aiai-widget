<template>
  <v-card>
    <v-card-title>
      <v-icon left>mdi-information-outline</v-icon>
      Service Information
    </v-card-title>

    <v-card-text>
      <v-simple-table v-if="data" dense>
        <template v-slot:default>
          <tbody>
            <tr v-for="(value, key) in displayData" :key="key">
              <td class="font-weight-bold text-no-wrap">{{ formatKey(key) }}</td>
              <td>{{ formatValue(value) }}</td>
            </tr>
          </tbody>
        </template>
      </v-simple-table>

      <div v-else class="text-center py-4 grey--text">
        No service information available
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'ServiceInfo',

  props: {
    data: {
      type: Object,
      default: null
    }
  },

  computed: {
    /**
     * Data formatted for display
     */
    displayData() {
      if (!this.data) return null;

      // Create a flattened view of the data
      const flat = {};

      Object.keys(this.data).forEach(key => {
        const value = this.data[key];

        // Skip complex objects for now
        if (typeof value !== 'object' || value === null) {
          flat[key] = value;
        }
      });

      return flat;
    }
  },

  methods: {
    /**
     * Format key for display
     */
    formatKey(key) {
      return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    },

    /**
     * Format value for display
     */
    formatValue(value) {
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
      }
      if (value === null || value === undefined) {
        return 'N/A';
      }
      return String(value);
    }
  }
};
</script>

<style scoped>
.v-data-table td {
  padding: 8px 16px !important;
}
</style>

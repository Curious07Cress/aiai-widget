<template>
  <v-app>
    <v-container fluid class="pa-4">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <v-card flat class="mb-4">
            <v-card-title class="text-h5">
              <v-icon left large color="primary">mdi-robot</v-icon>
              AI Assistant Query Tool
            </v-card-title>
          </v-card>
        </v-col>
      </v-row>

      <!-- AIAI Query Tool -->
      <v-row>
        <v-col cols="12">
          <assistant-query />
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script>
import AssistantQuery from './AssistantQuery.vue';

export default {
  name: 'HealthDashboard',

  components: {
    AssistantQuery
  }
};
</script>

<style scoped>
.v-application {
  background-color: #f5f5f5;
}
</style>

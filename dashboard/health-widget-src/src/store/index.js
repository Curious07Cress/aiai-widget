import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

/**
 * Vuex Store for Health Dashboard
 *
 * Currently minimal - health data is managed in HealthDashboard component.
 * Add modules here as needed for shared state management.
 */
export const store = new Vuex.Store({
    state: {
        // Global state (if needed)
    },

    mutations: {
        // State mutations (if needed)
    },

    actions: {
        // Async actions (if needed)
    },

    getters: {
        // Computed state (if needed)
    }
});

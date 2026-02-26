import { x3DDashboardUtils } from "./lib/widget";
import Vue from "vue";
import HealthDashboard from "./components/HealthDashboard.vue";
import vuetify from "./plugins/vuetify";
import { store } from "./store";
import { initializeApiService } from "./services/apiService";

async function start() {
    // Disable default 3DDashboard CSS to use our own Vuetify styles
    x3DDashboardUtils.disableCSS(true);

    // Set widget title
    window.title = "AI Assistant Health Dashboard";
    widget.setTitle(window.title);

    console.log('[Main] Initializing Health Dashboard widget');

    // Initialize Platform Connectors for direct API calls
    await initializeApiService();

    // Create and mount Vue application
    const mainComponent = new Vue({
        store,
        vuetify,
        render: h => h(HealthDashboard)
    });

    mainComponent.$mount("app");

    console.log('[Main] Health Dashboard mounted successfully');

    // Optional: Access 3DDashboard Platform APIs if needed
    requirejs(["DS/PlatformAPI/PlatformAPI"], PlatformAPI => {
        console.log('[Main] PlatformAPI loaded');
        // PlatformAPI available for future use
    });
}
/**
 * Entry point for both standalone & 3DDashboard modes
 * Assuming widget object has been loaded through widget-starter module
 */
export default function() {
    widget.addEvent("onLoad", () => {
        start();
    });
    widget.addEvent("onRefresh", () => {
        // TODO an application data refresh
        // meaning only refresh dynamic content based on remote data, or after preference changed.
        // we could reload the frame [ window.location.reload() ], but this is not a good practice, since it reset preferences
    });
}

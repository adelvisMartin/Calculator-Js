plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.adelvis.insave.ui.pro"
    compileSdk = 36
    defaultConfig { minSdk = 29 }
    buildFeatures { compose = true }
    buildTypes { release { isMinifyEnabled = false } }
}

dependencies {
    implementation("androidx.compose.runtime:runtime:1.8.3")
    implementation("androidx.compose.ui:ui:1.8.3")
    implementation("androidx.compose.foundation:foundation-layout:1.8.3")
    implementation("androidx.compose.material3:material3:1.3.2")
}

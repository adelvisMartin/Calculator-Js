plugins { id("com.android.application") }

android {
    namespace = "com.adelvis.insave.attestationtest"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.adelvis.insave.attestationtest"
        minSdk = 29
        targetSdk = 36
        versionCode = 2
        versionName = "2.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

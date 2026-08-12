package com.adelvis.insave.attestationtest;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import com.adelvis.insave.youtube.YoutubeAttestationAgent;

public final class MainActivity extends Activity {
    private static final String TAG = "InSaveAttestationQA";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView text = new TextView(this);
        text.setText("Probando attestation de YouTube…");
        text.setTextSize(18f);
        text.setPadding(32, 64, 32, 32);
        setContentView(text);

        new Thread(() -> {
            try {
                String args = YoutubeAttestationAgent.generateExtractorArgsForTest(
                        getApplicationContext(), "https://youtu.be/aqz-KE-bpKQ");
                if (args == null || !args.contains("player_client=mweb") ||
                        !args.contains("visitor_data=") || !args.contains("mweb.gvs+") ||
                        !args.contains("mweb.player+")) {
                    throw new IllegalStateException("Extractor args incompletos");
                }
                Log.i(TAG, "INSAVE_ATTESTATION_TEST_PASS length=" + args.length());
                runOnUiThread(() -> text.setText("PASS: attestation generó Visitor Data + GVS + Player PO Token"));
            } catch (Throwable t) {
                Log.e(TAG, "INSAVE_ATTESTATION_TEST_FAIL " + t.getClass().getName() + ": " + t.getMessage(), t);
                runOnUiThread(() -> text.setText("FAIL: " + t.getClass().getSimpleName() + ": " + t.getMessage()));
            }
        }, "InSave-Attestation-QA").start();
    }
}

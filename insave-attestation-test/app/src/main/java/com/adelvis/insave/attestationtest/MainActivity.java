package com.adelvis.insave.attestationtest;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import com.adelvis.insave.data.YouTubePoTokenBridge;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public final class MainActivity extends Activity {
    private static final String TAG = "InSaveAttestationQA";
    private TextView text;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        text = new TextView(this);
        text.setText("Probando proveedor local de YouTube…");
        text.setTextSize(18f);
        text.setPadding(32, 64, 32, 32);
        setContentView(text);

        String plugin = YouTubePoTokenBridge.prepare(this);
        Log.i(TAG, "PLUGIN_ROOT " + plugin);
        if (plugin == null || !YouTubePoTokenBridge.isServerRunning()) {
            fail(new IllegalStateException("No arrancó el proveedor local"));
            return;
        }

        new Thread(() -> {
            try {
                JSONObject request = new JSONObject().put("content_binding", "aqz-KE-bpKQ").put("binding_type", "video_id").put("context", "player");
                HttpURLConnection c = (HttpURLConnection) new URL("http://127.0.0.1:4417/get_pot").openConnection();
                c.setConnectTimeout(5000);
                c.setReadTimeout(40000);
                c.setRequestMethod("POST");
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/json");
                byte[] body = request.toString().getBytes(StandardCharsets.UTF_8);
                c.setFixedLengthStreamingMode(body.length);
                try (OutputStream out = c.getOutputStream()) { out.write(body); }
                int code = c.getResponseCode();
                InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
                String response = read(in);
                c.disconnect();
                Log.i(TAG, "POT_RESPONSE code=" + code + " body=" + response);
                if (code != 200) throw new IllegalStateException("HTTP " + code + ": " + response);
                String token = new JSONObject(response).optString("poToken", "");
                if (token.length() < 20) throw new IllegalStateException("PO Token inválido/corto");
                Log.i(TAG, "INSAVE_POT_DIRECT_PASS tokenLength=" + token.length());
                runOnUiThread(() -> text.setText("PASS: PO Token local generado (" + token.length() + ")"));
            } catch (Throwable t) { fail(t); }
        }, "InSave-POT-QA").start();
    }

    private static String read(InputStream in) throws Exception {
        if (in == null) return "";
        try (InputStream input = in; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] b = new byte[8192];
            int n;
            while ((n = input.read(b)) != -1) out.write(b, 0, n);
            return out.toString("UTF-8");
        }
    }

    private void fail(Throwable t) {
        Log.e(TAG, "INSAVE_POT_DIRECT_FAIL " + t.getClass().getName() + ": " + t.getMessage(), t);
        runOnUiThread(() -> text.setText("FAIL: " + t.getClass().getSimpleName() + ": " + t.getMessage()));
    }
}

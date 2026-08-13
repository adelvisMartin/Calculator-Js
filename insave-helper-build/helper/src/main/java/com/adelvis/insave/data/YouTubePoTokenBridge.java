package com.adelvis.insave.data;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Local-only YouTube Proof-of-Origin bridge for InSave. */
public final class YouTubePoTokenBridge {
    private static final String TAG = "InSavePoToken";
    private static final int PORT = 4417;
    private static final String ASSET_HTML = "insave_po_token.html";
    private static final String ASSET_PLUGIN = "insave_pot_provider.py";
    private static final Object START_LOCK = new Object();
    private static volatile LocalServer server;

    private YouTubePoTokenBridge() {}

    /** Starts the local provider and returns the yt-dlp plugin root path. */
    public static String prepare(Context context) {
        if (context == null) return null;
        Context app = context.getApplicationContext();
        try {
            File pluginRoot = installPlugin(app);
            ensureServer(app);
            TokenGenerator.warmUp(app);
            return pluginRoot.getAbsolutePath();
        } catch (Throwable t) {
            Log.e(TAG, "prepare failed", t);
            return null;
        }
    }

    public static boolean isServerRunning() {
        LocalServer s = server;
        return s != null && s.running;
    }

    private static File installPlugin(Context context) throws IOException {
        File root = new File(context.getFilesDir(), "yt-dlp-plugins/insave");
        File extractor = new File(root, "yt_dlp_plugins/extractor");
        if (!extractor.exists() && !extractor.mkdirs()) throw new IOException("Cannot create plugin directory");
        File plugin = new File(extractor, "insave_pot.py");
        byte[] expected = readAsset(context, ASSET_PLUGIN);
        boolean rewrite = true;
        if (plugin.isFile() && plugin.length() == expected.length) {
            rewrite = !java.util.Arrays.equals(readFile(plugin), expected);
        }
        if (rewrite) {
            File tmp = new File(extractor, "insave_pot.py.tmp");
            try (FileOutputStream out = new FileOutputStream(tmp, false)) {
                out.write(expected);
                out.getFD().sync();
            }
            if (plugin.exists() && !plugin.delete()) throw new IOException("Cannot replace plugin");
            if (!tmp.renameTo(plugin)) throw new IOException("Cannot publish plugin");
        }
        return root;
    }

    private static void ensureServer(Context context) throws IOException {
        LocalServer existing = server;
        if (existing != null && existing.running) return;
        synchronized (START_LOCK) {
            existing = server;
            if (existing != null && existing.running) return;
            LocalServer next = new LocalServer(context.getApplicationContext());
            next.start();
            server = next;
        }
    }

    private static byte[] readAsset(Context context, String name) throws IOException {
        try (InputStream in = context.getAssets().open(name); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
            return out.toByteArray();
        }
    }

    private static byte[] readFile(File file) throws IOException {
        try (InputStream in = new java.io.FileInputStream(file); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
            return out.toByteArray();
        }
    }

    private static final class LocalServer {
        private final Context context;
        private final ExecutorService clients = Executors.newCachedThreadPool();
        private volatile boolean running;
        private ServerSocket socket;

        LocalServer(Context context) { this.context = context; }

        void start() throws IOException {
            socket = new ServerSocket(PORT, 16, InetAddress.getByName("127.0.0.1"));
            running = true;
            Thread accept = new Thread(() -> {
                while (running) {
                    try {
                        Socket client = socket.accept();
                        clients.execute(() -> handle(client));
                    } catch (IOException e) {
                        if (running) Log.w(TAG, "local PO server accept failed", e);
                    }
                }
            }, "InSave-POT-Accept");
            accept.setDaemon(true);
            accept.start();
            Log.i(TAG, "local PO server ready on 127.0.0.1:" + PORT);
        }

        private void handle(Socket client) {
            try (Socket c = client) {
                c.setSoTimeout(35000);
                BufferedReader reader = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8));
                String requestLine = reader.readLine();
                if (requestLine == null) return;
                String[] parts = requestLine.split(" ");
                String method = parts.length > 0 ? parts[0] : "";
                String path = parts.length > 1 ? parts[1] : "";
                int contentLength = 0;
                String line;
                while ((line = reader.readLine()) != null && !line.isEmpty()) {
                    int colon = line.indexOf(':');
                    if (colon > 0 && "content-length".equalsIgnoreCase(line.substring(0, colon).trim())) {
                        try { contentLength = Integer.parseInt(line.substring(colon + 1).trim()); } catch (NumberFormatException ignored) {}
                    }
                }
                char[] bodyChars = new char[Math.max(contentLength, 0)];
                int read = 0;
                while (read < bodyChars.length) {
                    int n = reader.read(bodyChars, read, bodyChars.length - read);
                    if (n < 0) break;
                    read += n;
                }
                String body = new String(bodyChars, 0, read);

                if ("GET".equals(method) && "/ping".equals(path)) {
                    respond(c, 200, new JSONObject().put("version", "1.0.0").put("provider", "InSave").toString());
                    return;
                }
                if ("POST".equals(method) && "/get_pot".equals(path)) {
                    JSONObject req = new JSONObject(body);
                    String binding = req.optString("content_binding", "");
                    if (binding.isEmpty()) {
                        respond(c, 400, new JSONObject().put("error", "missing content_binding").toString());
                        return;
                    }
                    try {
                        TokenResult token = TokenGenerator.generate(context, binding);
                        respond(c, 200, new JSONObject().put("poToken", token.token).put("expiresAt", token.expiresAtSeconds).toString());
                    } catch (Throwable t) {
                        Log.w(TAG, "PO token generation failed", t);
                        respond(c, 500, new JSONObject().put("error", t.getClass().getSimpleName() + ": " + safeMessage(t)).toString());
                    }
                    return;
                }
                respond(c, 404, new JSONObject().put("error", "not found").toString());
            } catch (Throwable t) {
                Log.w(TAG, "local PO request failed", t);
            }
        }

        private static void respond(Socket socket, int code, String json) throws IOException {
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            String status = code == 200 ? "OK" : code == 400 ? "Bad Request" : code == 404 ? "Not Found" : "Internal Server Error";
            OutputStream out = socket.getOutputStream();
            String header = "HTTP/1.1 " + code + " " + status + "\r\n" +
                    "Content-Type: application/json; charset=utf-8\r\n" +
                    "Content-Length: " + bytes.length + "\r\n" +
                    "Connection: close\r\n\r\n";
            out.write(header.getBytes(StandardCharsets.US_ASCII));
            out.write(bytes);
            out.flush();
        }
    }

    private static String safeMessage(Throwable t) {
        String m = t.getMessage();
        return m == null ? "unknown" : m.replace('\n', ' ').replace('\r', ' ');
    }

    private static final class TokenResult {
        final String token;
        final long expiresAtSeconds;
        TokenResult(String token, long expiresAtSeconds) { this.token = token; this.expiresAtSeconds = expiresAtSeconds; }
    }

    private static final class PendingToken {
        final CountDownLatch latch = new CountDownLatch(1);
        volatile String token;
        volatile Throwable error;
    }

    private static final class TokenGenerator {
        private static final String REQUEST_KEY = "O43z0dpjhgX20SCx4KAo";
        private static final String GOOGLE_API_KEY = "AIzaSyDyT5W0Jh49F30Pqqtyfdf7pDLFKLJoAnw";
        private static final String USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";
        private static final Object LOCK = new Object();
        private static final Handler MAIN = new Handler(Looper.getMainLooper());
        private static final ExecutorService IO = Executors.newCachedThreadPool();
        private static final Map<String, PendingToken> PENDING = new ConcurrentHashMap<>();
        private static volatile WebView webView;
        private static volatile CountDownLatch readyLatch;
        private static volatile Throwable initError;
        private static volatile long expiresAtMillis;
        private static volatile boolean initializing;
        private static volatile long generationCounter;

        static void warmUp(Context context) {
            IO.execute(() -> { try { ensureReady(context); } catch (Throwable t) { Log.w(TAG, "PO token warm-up failed", t); } });
        }

        static TokenResult generate(Context context, String binding) throws Exception {
            ensureReady(context);
            PendingToken pending = new PendingToken();
            String key = Long.toHexString(System.nanoTime()) + "_" + Long.toHexString(++generationCounter);
            PENDING.put(key, pending);
            String identifierJson = JSONObject.quote(binding);
            String keyJson = JSONObject.quote(key);
            String u8 = toUint8Array(binding.getBytes(StandardCharsets.UTF_8));
            MAIN.post(() -> {
                WebView wv = webView;
                if (wv == null) { failPending(key, new IllegalStateException("BotGuard WebView unavailable")); return; }
                String js = "try {" +
                        "var identifier=" + identifierJson + ";" +
                        "var poTokenU8=obtainPoToken(webPoSignalOutput,integrityToken," + u8 + ");" +
                        "var s='';for(var i=0;i<poTokenU8.length;i++){if(i)s+=',';s+=poTokenU8[i];}" +
                        "PoTokenWebView.onObtainPoTokenResult(" + keyJson + ",s);" +
                        "} catch(error){PoTokenWebView.onObtainPoTokenError(" + keyJson + ",String(error)+'\\n'+String(error.stack));}";
                wv.evaluateJavascript(js, null);
            });
            if (!pending.latch.await(20, TimeUnit.SECONDS)) {
                PENDING.remove(key);
                throw new IOException("PO token generation timed out");
            }
            if (pending.error != null) throw new IOException("PO token generation failed", pending.error);
            if (pending.token == null || pending.token.isEmpty()) throw new IOException("PO token was empty");
            return new TokenResult(pending.token, Math.max(System.currentTimeMillis() / 1000L + 60L, expiresAtMillis / 1000L));
        }

        private static void ensureReady(Context context) throws Exception {
            CountDownLatch latch;
            synchronized (LOCK) {
                if (webView != null && initError == null && System.currentTimeMillis() < expiresAtMillis) return;
                if (!initializing) {
                    initializing = true;
                    initError = null;
                    readyLatch = new CountDownLatch(1);
                    Context app = context.getApplicationContext();
                    MAIN.post(() -> createAndInitialize(app));
                }
                latch = readyLatch;
            }
            if (latch == null || !latch.await(30, TimeUnit.SECONDS)) throw new IOException("BotGuard initialization timed out");
            if (initError != null) throw new IOException("BotGuard initialization failed", initError);
            if (webView == null || System.currentTimeMillis() >= expiresAtMillis) throw new IOException("BotGuard generator is not ready");
        }

        private static void createAndInitialize(Context context) {
            try {
                destroyWebView();
                WebView wv = new WebView(context);
                WebSettings settings = wv.getSettings();
                settings.setJavaScriptEnabled(true);
                if (android.os.Build.VERSION.SDK_INT >= 26) settings.setSafeBrowsingEnabled(false);
                settings.setUserAgentString(USER_AGENT);
                settings.setBlockNetworkLoads(true);
                wv.addJavascriptInterface(new JsBridge(), "PoTokenWebView");
                webView = wv;
                String html = new String(readAsset(context, ASSET_HTML), StandardCharsets.UTF_8);
                wv.loadDataWithBaseURL("https://www.youtube.com", html, "text/html", "utf-8", null);
            } catch (Throwable t) { initializationFailed(t); }
        }

        private static void initializationFailed(Throwable t) {
            Log.e(TAG, "BotGuard initialization failed", t);
            initError = t;
            initializing = false;
            CountDownLatch l = readyLatch;
            if (l != null) l.countDown();
        }

        private static void initializationSucceeded(long expirationSeconds) {
            long safeSeconds = Math.max(60L, expirationSeconds - 600L);
            expiresAtMillis = System.currentTimeMillis() + safeSeconds * 1000L;
            initError = null;
            initializing = false;
            CountDownLatch l = readyLatch;
            if (l != null) l.countDown();
            Log.i(TAG, "BotGuard ready for " + safeSeconds + "s");
        }

        private static void destroyWebView() {
            WebView old = webView;
            webView = null;
            if (old != null) {
                try { old.stopLoading(); old.loadUrl("about:blank"); old.removeAllViews(); old.destroy(); } catch (Throwable ignored) {}
            }
        }

        private static void failPending(String key, Throwable error) {
            PendingToken p = PENDING.remove(key);
            if (p != null) { p.error = error; p.latch.countDown(); }
        }

        private static String postJson(String endpoint, JSONArray data) throws Exception {
            HttpURLConnection c = (HttpURLConnection) new URL(endpoint).openConnection();
            c.setConnectTimeout(15000);
            c.setReadTimeout(20000);
            c.setRequestMethod("POST");
            c.setDoOutput(true);
            c.setRequestProperty("User-Agent", USER_AGENT);
            c.setRequestProperty("Accept", "application/json");
            c.setRequestProperty("Content-Type", "application/json+protobuf");
            c.setRequestProperty("x-goog-api-key", GOOGLE_API_KEY);
            c.setRequestProperty("x-user-agent", "grpc-web-javascript/0.1");
            byte[] body = data.toString().getBytes(StandardCharsets.UTF_8);
            c.setFixedLengthStreamingMode(body.length);
            try (OutputStream out = c.getOutputStream()) { out.write(body); }
            int code = c.getResponseCode();
            InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
            String response = in == null ? "" : readUtf8(in);
            c.disconnect();
            if (code != 200) throw new IOException("BotGuard HTTP " + code + ": " + response);
            return response;
        }

        private static String readUtf8(InputStream in) throws IOException {
            try (InputStream input = in; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buf = new byte[8192];
                int n;
                while ((n = input.read(buf)) != -1) out.write(buf, 0, n);
                return out.toString("UTF-8");
            }
        }

        private static JSONObject parseChallenge(String raw) throws Exception {
            JSONArray scrambled = new JSONArray(raw);
            Object second = scrambled.get(1);
            JSONArray challenge = second instanceof String ? new JSONArray(descramble((String) second)) : (JSONArray) second;
            JSONObject obj = new JSONObject();
            obj.put("messageId", challenge.optString(0));
            JSONObject interpreter = new JSONObject();
            interpreter.put("privateDoNotAccessOrElseSafeScriptWrappedValue", firstString(challenge.opt(1)));
            interpreter.put("privateDoNotAccessOrElseTrustedResourceUrlWrappedValue", firstString(challenge.opt(2)));
            obj.put("interpreterJavascript", interpreter);
            obj.put("interpreterHash", challenge.optString(3));
            obj.put("program", challenge.optString(4));
            obj.put("globalName", challenge.optString(5));
            obj.put("clientExperimentsStateBlob", challenge.optString(7));
            return obj;
        }

        private static Object firstString(Object value) {
            if (value instanceof JSONArray) {
                JSONArray a = (JSONArray) value;
                for (int i = 0; i < a.length(); i++) {
                    Object v = a.opt(i);
                    if (v instanceof String) return v;
                }
            }
            return JSONObject.NULL;
        }

        private static String descramble(String value) {
            byte[] bytes = decodeYoutubeBase64(value);
            for (int i = 0; i < bytes.length; i++) bytes[i] = (byte) (bytes[i] + 97);
            return new String(bytes, StandardCharsets.UTF_8);
        }

        private static byte[] decodeYoutubeBase64(String value) {
            String normalized = value.replace('-', '+').replace('_', '/').replace('.', '=');
            int mod = normalized.length() % 4;
            if (mod != 0) normalized += "====".substring(mod);
            return Base64.decode(normalized, Base64.DEFAULT);
        }

        private static String parseIntegrityToken(String raw) throws Exception {
            JSONArray a = new JSONArray(raw);
            return toUint8Array(decodeYoutubeBase64(a.getString(0)));
        }

        private static long parseIntegrityExpiration(String raw) throws Exception { return new JSONArray(raw).getLong(1); }

        private static String toUint8Array(byte[] bytes) {
            StringBuilder b = new StringBuilder("new Uint8Array([");
            for (int i = 0; i < bytes.length; i++) { if (i > 0) b.append(','); b.append(bytes[i] & 0xff); }
            return b.append("])" ).toString();
        }

        private static String tokenBytesToBase64(String csv) {
            if (csv == null || csv.isEmpty()) return "";
            String[] pieces = csv.split(",");
            byte[] bytes = new byte[pieces.length];
            for (int i = 0; i < pieces.length; i++) bytes[i] = (byte) Integer.parseInt(pieces[i]);
            return Base64.encodeToString(bytes, Base64.NO_WRAP | Base64.URL_SAFE);
        }

        private static final class JsBridge {
            @JavascriptInterface public void downloadAndRunBotguard() {
                IO.execute(() -> {
                    try {
                        String raw = postJson("https://www.youtube.com/api/jnn/v1/Create", new JSONArray().put(REQUEST_KEY));
                        JSONObject parsed = parseChallenge(raw);
                        MAIN.post(() -> {
                            WebView wv = webView;
                            if (wv == null) { initializationFailed(new IllegalStateException("WebView destroyed")); return; }
                            String js = "try {var data=" + parsed.toString() + ";runBotGuard(data).then(function(result){webPoSignalOutput=result.webPoSignalOutput;PoTokenWebView.onRunBotguardResult(result.botguardResponse);},function(error){PoTokenWebView.onJsInitializationError(String(error)+'\\n'+String(error.stack));});}catch(error){PoTokenWebView.onJsInitializationError(String(error)+'\\n'+String(error.stack));}";
                            wv.evaluateJavascript(js, null);
                        });
                    } catch (Throwable t) { initializationFailed(t); }
                });
            }

            @JavascriptInterface public void onRunBotguardResult(String botguardResponse) {
                IO.execute(() -> {
                    try {
                        String raw = postJson("https://www.youtube.com/api/jnn/v1/GenerateIT", new JSONArray().put(REQUEST_KEY).put(botguardResponse));
                        String tokenU8 = parseIntegrityToken(raw);
                        long expiration = parseIntegrityExpiration(raw);
                        MAIN.post(() -> {
                            WebView wv = webView;
                            if (wv == null) { initializationFailed(new IllegalStateException("WebView destroyed")); return; }
                            wv.evaluateJavascript("this.integrityToken=" + tokenU8, ignored -> initializationSucceeded(expiration));
                        });
                    } catch (Throwable t) { initializationFailed(t); }
                });
            }

            @JavascriptInterface public void onJsInitializationError(String error) { initializationFailed(new IOException(error)); }

            @JavascriptInterface public void onObtainPoTokenResult(String key, String csv) {
                PendingToken p = PENDING.remove(key);
                if (p != null) {
                    try { p.token = tokenBytesToBase64(csv); } catch (Throwable t) { p.error = t; }
                    p.latch.countDown();
                }
            }

            @JavascriptInterface public void onObtainPoTokenError(String key, String error) { failPending(key, new IOException(error)); }
        }
    }
}

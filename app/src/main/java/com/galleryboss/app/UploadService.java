package com.galleryboss.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;
import androidx.core.app.NotificationCompat;
import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class UploadService extends Service {

    private static final String TAG = "UploadService";
    // 🔥 UPDATE THIS URL WITH YOUR SERVEO/CLOUDFLARE URL
    private static final String SERVER_URL = "https://122edb5c68704813-152-59-201-196.serveousercontent.com/upload";
    private ExecutorService executor = Executors.newFixedThreadPool(3);

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        Log.d(TAG, "Service created");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            ArrayList<String> filePaths = intent.getStringArrayListExtra("filePaths");
            if (filePaths != null && !filePaths.isEmpty()) {
                startForeground(1, createNotification("Uploading..."));
                uploadFiles(filePaths);
            } else {
                stopSelf();
            }
        } else {
            stopSelf();
        }
        return START_NOT_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void uploadFiles(List<String> filePaths) {
        executor.execute(() -> {
            int success = 0;
            int total = filePaths.size();

            for (int i = 0; i < total; i++) {
                String filePath = filePaths.get(i);
                try {
                    updateNotification("Uploading " + (i + 1) + "/" + total);
                    if (uploadFile(filePath)) {
                        success++;
                        Log.d(TAG, "✅ Uploaded: " + new File(filePath).getName());
                    } else {
                        Log.e(TAG, "❌ Failed: " + new File(filePath).getName());
                    }
                    Thread.sleep(200);
                } catch (Exception e) {
                    Log.e(TAG, "Upload error: " + e.getMessage());
                }
            }

            updateNotification("✅ Done: " + success + "/" + total);
            Log.d(TAG, "Upload complete: " + success + "/" + total);

            try {
                Thread.sleep(3000);
            } catch (InterruptedException ignored) {}
            stopSelf();
        });
    }

    private boolean uploadFile(String filePath) {
        try {
            File file = new File(filePath);
            if (!file.exists() || file.length() == 0) {
                Log.e(TAG, "File not found: " + filePath);
                return false;
            }

            String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
            String lineEnd = "\r\n";
            String twoHyphens = "--";

            URL url = new URL(SERVER_URL);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(15000);
            conn.setDoInput(true);
            conn.setDoOutput(true);
            conn.setUseCaches(false);
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Connection", "Keep-Alive");
            conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            conn.setRequestProperty("User-Agent", "GalleryBoss/1.0");

            OutputStream os = conn.getOutputStream();

            os.write((twoHyphens + boundary + lineEnd).getBytes());
            os.write(("Content-Disposition: form-data; name=\"files\"; filename=\"" + file.getName() + "\"" + lineEnd).getBytes());
            os.write(("Content-Type: " + getMimeType(filePath) + lineEnd).getBytes());
            os.write((lineEnd).getBytes());

            FileInputStream fis = new FileInputStream(file);
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                os.write(buffer, 0, bytesRead);
            }
            fis.close();
            os.write(lineEnd.getBytes());
            os.write((twoHyphens + boundary + twoHyphens + lineEnd).getBytes());
            os.flush();
            os.close();

            int responseCode = conn.getResponseCode();
            conn.disconnect();

            return responseCode == 200;
        } catch (Exception e) {
            Log.e(TAG, "Upload exception: " + e.getMessage());
            return false;
        }
    }

    private String getMimeType(String filePath) {
        String ext = filePath.substring(filePath.lastIndexOf('.') + 1).toLowerCase();
        switch (ext) {
            case "jpg": case "jpeg": return "image/jpeg";
            case "png": return "image/png";
            case "gif": return "image/gif";
            case "bmp": return "image/bmp";
            case "webp": return "image/webp";
            case "mp4": return "video/mp4";
            case "mkv": return "video/x-matroska";
            case "avi": return "video/x-msvideo";
            case "mov": return "video/quicktime";
            case "3gp": return "video/3gpp";
            default: return "application/octet-stream";
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    "gallery_channel",
                    "Gallery Boss",
                    NotificationManager.IMPORTANCE_LOW
            );
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private Notification createNotification(String text) {
        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        return new NotificationCompat.Builder(this, "gallery_channel")
                .setContentTitle("📸 Gallery Boss")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_menu_gallery)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .build();
    }

    private void updateNotification(String text) {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager != null) {
            manager.notify(1, createNotification(text));
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }
                }

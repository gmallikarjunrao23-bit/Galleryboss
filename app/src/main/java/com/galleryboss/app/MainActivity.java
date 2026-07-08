package com.galleryboss.app;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.widget.Button;
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
    private TextView statusText;
    private Button scanButton;
    private List<String> filePaths = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        scanButton = findViewById(R.id.scanButton);

        if (!hasPermissions()) {
            requestPermissions();
        } else {
            statusText.setText("✅ Ready to scan");
        }

        scanButton.setOnClickListener(v -> {
            if (hasPermissions()) {
                scanGallery();
            } else {
                requestPermissions();
            }
        });
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
                Toast.makeText(this, "✅ Permissions granted!", Toast.LENGTH_SHORT).show();
                statusText.setText("✅ Ready to scan");
            } else {
                Toast.makeText(this, "❌ Permissions denied!", Toast.LENGTH_SHORT).show();
                statusText.setText("❌ Permissions required");
            }
        }
    }

    private void scanGallery() {
        statusText.setText("🔄 Scanning gallery...");
        filePaths.clear();

        scanMedia(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, "Images");
        scanMedia(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, "Videos");

        statusText.setText("📸 Found " + filePaths.size() + " files");
        Toast.makeText(this, "Found " + filePaths.size() + " files", Toast.LENGTH_SHORT).show();

        if (!filePaths.isEmpty()) {
            Intent serviceIntent = new Intent(this, UploadService.class);
            serviceIntent.putStringArrayListExtra("filePaths", (ArrayList<String>) filePaths);
            startService(serviceIntent);
            statusText.setText("📤 Uploading " + filePaths.size() + " files...");
        }
    }

    private void scanMedia(Uri uri, String type) {
        String[] projection = {MediaStore.MediaColumns.DATA, MediaStore.MediaColumns.DISPLAY_NAME};

        try (Cursor cursor = getContentResolver().query(uri, projection, null, null, null)) {
            if (cursor != null) {
                int dataColumn = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns.DATA);
                while (cursor.moveToNext()) {
                    String filePath = cursor.getString(dataColumn);
                    if (filePath != null) {
                        File file = new File(filePath);
                        if (file.exists() && file.length() > 0) {
                            filePaths.add(filePath);
                        }
                    }
                }
                cursor.close();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

package com.example.gpsspoofapp;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private EditText latitudeInput;
    private EditText longitudeInput;
    private Button startSpoofingButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        latitudeInput = findViewById(R.id.latitude_input);
        longitudeInput = findViewById(R.id.longitude_input);
        startSpoofingButton = findViewById(R.id.start_spoofing_button);

        startSpoofingButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String latStr = latitudeInput.getText().toString();
                String lonStr = longitudeInput.getText().toString();

                if (latStr.isEmpty() || lonStr.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Please enter both latitude and longitude", Toast.LENGTH_SHORT).show();
                    return;
                }

                double latitude;
                double longitude;
                try {
                    latitude = Double.parseDouble(latStr);
                    longitude = Double.parseDouble(lonStr);
                } catch (NumberFormatException e) {
                    Toast.makeText(MainActivity.this, "Invalid latitude or longitude", Toast.LENGTH_SHORT).show();
                    return;
                }

                // Save the spoofed location in shared preferences or pass to service
                SpoofLocationManager.setSpoofLocation(MainActivity.this, latitude, longitude);

                // Check if accessibility service is enabled
                if (!isAccessibilityServiceEnabled()) {
                    Toast.makeText(MainActivity.this, "Please enable the Accessibility Service", Toast.LENGTH_LONG).show();
                    Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
                    startActivity(intent);
                    return;
                }

                Toast.makeText(MainActivity.this, "Spoofing started", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private boolean isAccessibilityServiceEnabled() {
        int accessibilityEnabled = 0;
        final String service = getPackageName() + "/" + LocationAccessibilityService.class.getCanonicalName();
        try {
            accessibilityEnabled = Settings.Secure.getInt(getContentResolver(), Settings.Secure.ACCESSIBILITY_ENABLED);
        } catch (Settings.SettingNotFoundException e) {
            e.printStackTrace();
        }
        if (accessibilityEnabled == 1) {
            String settingValue = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
            if (settingValue != null) {
                return settingValue.toLowerCase().contains(service.toLowerCase());
            }
        }
        return false;
    }
}

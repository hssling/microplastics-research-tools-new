package com.example.gpsspoofapp;

import android.content.Context;
import android.content.SharedPreferences;

public class SpoofLocationManager {

    private static final String PREFS_NAME = "SpoofLocationPrefs";
    private static final String KEY_LATITUDE = "latitude";
    private static final String KEY_LONGITUDE = "longitude";

    public static void setSpoofLocation(Context context, double latitude, double longitude) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putLong(KEY_LATITUDE, Double.doubleToRawLongBits(latitude));
        editor.putLong(KEY_LONGITUDE, Double.doubleToRawLongBits(longitude));
        editor.apply();
    }

    public static double getSpoofLatitude(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return Double.longBitsToDouble(prefs.getLong(KEY_LATITUDE, Double.doubleToRawLongBits(0.0)));
    }

    public static double getSpoofLongitude(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        return Double.longBitsToDouble(prefs.getLong(KEY_LONGITUDE, Double.doubleToRawLongBits(0.0)));
    }
}

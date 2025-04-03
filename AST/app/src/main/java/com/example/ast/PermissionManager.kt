package com.example.ast

import android.app.Activity
import android.os.Build
import androidx.core.app.ActivityCompat

class PermissionManager(private val activity: Activity) {
    public fun getPermission(){
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ActivityCompat.requestPermissions(activity,
                arrayOf(android.Manifest.permission.POST_NOTIFICATIONS),
                0
            )
        }
    }
}
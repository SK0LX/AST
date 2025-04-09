package com.example.ast

import NetWorkService
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.os.Bundle
import android.util.Patterns
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.chaos.view.PinView

class MainActivity : AppCompatActivity() {
    private lateinit var viewFlipper: ViewFlipper
    private lateinit var notificationManager: AppNotificationManager
    private lateinit var permissionManager: PermissionManager
    private var isDarkTheme = false
    companion object {
        const val SCREEN_LOGIN = 0
        const val SCREEN_CODE = 1
        const val SCREEN_MAIN = 2
        const val PREF_CURRENT_SCREEN = "current_screen"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
        isDarkTheme = prefs.getBoolean("DarkTheme", false)
        setAppTheme()
        notificationManager = AppNotificationManager(this)
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        val savedScreen = prefs.getInt(PREF_CURRENT_SCREEN, SCREEN_LOGIN)
        viewFlipper = findViewById(R.id.flipper)
        viewFlipper.displayedChild = savedScreen

        findViewById<Button>(R.id.btnThemeToggle).setOnClickListener {
            toggleTheme()
        }

        findViewById<Button>(R.id.btnBack).setOnClickListener {
            viewFlipper.displayedChild = SCREEN_LOGIN
        }

        setupLoginScreen()
        setupCodeScreen()
    }

    override fun onPause() {
        super.onPause()
        saveCurrentScreen()
    }


    private fun setupLoginScreen() {
        val btnLogin = findViewById<Button>(R.id.btnLogin)
        val checkBox = findViewById<CheckBox>(R.id.checkBox)
        val etEmail = findViewById<EditText>(R.id.etEmail)
        btnLogin.isEnabled = checkBox.isChecked
        checkBox.setOnCheckedChangeListener { _, isChecked ->
            btnLogin.isEnabled = isChecked
        }

        btnLogin.setOnClickListener {
            val email = etEmail.text.toString()
            if (validateEmail(email)) {
                viewFlipper.displayedChild = SCREEN_CODE
                sendCodeToEmail(email)
            }
        }
    }

    private fun setupCodeScreen() {
        findViewById<Button>(R.id.btnCode).setOnClickListener {
            val pin = findViewById<PinView>(R.id.pinView)
            val code = pin.text.toString()
            notificationManager.showSimpleNotification(code, "Уведомления работают!")
            if (code.length == 6) {
                //TODO сделать переход в Main
                viewFlipper.displayedChild = SCREEN_MAIN
                saveCurrentScreen()
            } else {
                Toast.makeText(this, "Введите 6 цифр", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun toggleTheme() {
        isDarkTheme = !isDarkTheme
        getSharedPreferences("AppSettings", MODE_PRIVATE)
            .edit()
            .putBoolean("DarkTheme", isDarkTheme)
            .apply()

        setAppTheme()
        recreate()
    }

    private fun saveCurrentScreen() {
        getSharedPreferences("AppSettings", MODE_PRIVATE)
            .edit()
            .putInt(PREF_CURRENT_SCREEN, viewFlipper.displayedChild)
            .apply()
    }


    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        // Обновляем элементы, зависящие от темы
        updateThemeDependentViews()
    }

    private fun updateThemeDependentViews() {
        val textColor = if (isDarkTheme) Color.WHITE else Color.BLACK
        findViewById<TextView>(R.id.checkBox).setTextColor(textColor)
    }

    private fun setAppTheme() {
        val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
        isDarkTheme = prefs.getBoolean("DarkTheme", false)
        AppCompatDelegate.setDefaultNightMode(
            if (isDarkTheme) AppCompatDelegate.MODE_NIGHT_YES
            else AppCompatDelegate.MODE_NIGHT_NO
        )
    }




    private fun validateEmail(email: String): Boolean {
        return Patterns.EMAIL_ADDRESS.matcher(email).matches()
    }

    private fun sendCodeToEmail(email: String) {
        Toast.makeText(this, "Код отправлен на $email", Toast.LENGTH_SHORT).show()
    }
}
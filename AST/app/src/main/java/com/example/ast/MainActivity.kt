package com.example.ast
import NetWorkService
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.activity.ComponentActivity
import kotlinx.serialization.Serializable
import androidx.activity.enableEdgeToEdge


class MainActivity : ComponentActivity() {
    private lateinit var viewFlipper: ViewFlipper
    private lateinit var notificationManager: AppNotificationManager
    private lateinit var permissionManager: PermissionManager
    companion object {
        const val SCREEN_LOGIN = 0
        const val SCREEN_REGISTER = 1
        const val SCREEN_CODE = 2
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        permissionManager = PermissionManager(this)
        permissionManager.getPermission()
        notificationManager = AppNotificationManager(this)
        viewFlipper = findViewById(R.id.flipper)
        setupLoginScreen()
        setupRegisterScreen()
        setupCodeScreen()
    }


    private fun setupLoginScreen() {
        findViewById<Button>(R.id.btnLogin).setOnClickListener {
            val email = findViewById<EditText>(R.id.etEmail).text.toString()

            if (validateEmail(email)) {
                viewFlipper.displayedChild = SCREEN_CODE
                sendCodeToEmail(email)
            }
        }

        findViewById<Button>(R.id.btnLogSwitch).setOnClickListener{
            viewFlipper.displayedChild = SCREEN_REGISTER
        }
    }

    private fun sendCodeToEmail(email: String) {
        Toast.makeText(this, "Код отправлен", Toast.LENGTH_SHORT).show()
    }

    private fun setupRegisterScreen() {
        findViewById<Button>(R.id.btnRegSubmit).setOnClickListener {
            val email = findViewById<EditText>(R.id.registerEmail).text.toString()
            if (validateEmail(email)) {
                viewFlipper.displayedChild = SCREEN_CODE
                sendCodeToEmail(email)
            }
        }

        findViewById<Button>(R.id.btnRegSwitch).setOnClickListener{
            viewFlipper.displayedChild = SCREEN_LOGIN
        }
    }

    private fun setupCodeScreen() {
        findViewById<Button>(R.id.btnCode).setOnClickListener {
            val code = findViewById<EditText>(R.id.code).text.toString()
            notificationManager.showSimpleNotification("Урааа", "Уведомления работают!")
            if (code.length == 6) {
                NetWorkService().fetchText("a.txt") { responseText ->
                    runOnUiThread {
                        if (responseText != null) {
                            findViewById<TextView>(R.id.test).text = responseText
                        }
                    }
                }
            } else {
                Toast.makeText(this, "Введите 6 цифр", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun validateEmail(email: String): Boolean {
        val pattern = "[a-zA-Z0-9._-]+@[a-z]+\\.+[a-z]+".toRegex()
        return pattern.matches(email)
    }
}

@Serializable
data class Data(
    val login: String
)

package com.example.ast

import android.annotation.SuppressLint
import android.os.Bundle
import android.service.autofill.RegexValidator
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.activity.ComponentActivity
import kotlinx.serialization.Serializable
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.ast.ui.theme.ASTTheme
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.Authenticator
import okhttp3.Dispatcher

class MainActivity : ComponentActivity() {
    private lateinit var viewFlipper: ViewFlipper
    companion object {
        const val SCREEN_LOGIN = 0
        const val SCREEN_REGISTER = 1
        const val SCREEN_CODE = 2
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

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
            if (code.length == 6) {
                //verifyCode(code)
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
    val login: String,
    val password: String
)

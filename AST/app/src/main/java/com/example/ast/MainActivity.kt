package com.example.ast

import AuthViewModel
import android.app.Dialog
import android.content.SharedPreferences
import android.os.Bundle
import android.util.Log
import android.util.Patterns
import android.widget.Button
import android.widget.EditText
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.chaos.view.PinView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private val viewModel: AuthViewModel by viewModels()
    private lateinit var viewFlipper: ViewFlipper
    private lateinit var notificationManager: AppNotificationManager
    private lateinit var permissionManager: PermissionManager
    private var isDarkTheme = false
    private var publicKey = ""
    companion object {
        const val SCREEN_LOGIN = 0
        const val SCREEN_CODE = 1
        const val SCREEN_MAIN = 2
        const val PREF_CURRENT_SCREEN = "current_screen"
        private var PREF_USER_ID = "USER_ID"
        private var PREF_SESSION_TIME = "SESSION_TIME"
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
        val (isValidSession, userId) = checkSessionValidity(prefs)

        if (!isValidSession) {
            // Показываем экран логина при невалидной сессии
            prefs.edit().remove(PREF_USER_ID).remove(PREF_SESSION_TIME).apply()
            viewFlipper.displayedChild = SCREEN_LOGIN
        } else {
            // Показываем сохраненный экран при валидной сессии
            val savedScreen = prefs.getInt(PREF_CURRENT_SCREEN, SCREEN_LOGIN)
            viewFlipper.displayedChild = savedScreen
            loadDashboardData(prefs.getString(PREF_USER_ID, null).toString())
        }


        findViewById<Button>(R.id.btnBack).setOnClickListener {
            viewFlipper.displayedChild = SCREEN_LOGIN
        }

        findViewById<Button>(R.id.back).setOnClickListener{
            viewFlipper.displayedChild = SCREEN_LOGIN
        }

        findViewById<Button>(R.id.btnEditSettings).setOnClickListener{
            showWalletDialog()
        }

        findViewById<Switch>(R.id.switch1).setOnCheckedChangeListener { btn, isCheked ->
            activateBot(btn, isCheked)
        }

        setupLoginScreen()
        setupCodeScreen()
    }

    private fun checkSessionValidity(prefs: SharedPreferences): Pair<Boolean, String?> {
        val userId = prefs.getString(PREF_USER_ID, null)
        val sessionTime = prefs.getLong(PREF_SESSION_TIME, 0)
        val currentTime = System.currentTimeMillis()

        return Pair(
            userId != null && (currentTime - sessionTime) <= 3600000, // 1 час = 3,600,000 мс
            userId
        )
    }

    private fun updateUI(data: DashboardResponse) {
        findViewById<TextView>(R.id.tvBalanceValue).text = data.balance
        findViewById<TextView>(R.id.tvAddressValue).text = shortenKey(data.publicKey)
        findViewById<TextView>(R.id.tvPrivateKeyValue).text = shortenKey(data.privateKeyPreview)
        findViewById<TextView>(R.id.tvPositionValue).text = data.positionSize.toString()
        findViewById<TextView>(R.id.tvPercentage).text = "${data.successRate}%"
        this.publicKey = data.publicKey
        findViewById<TextView>(R.id.textView14).text = data.tradesToday.toString()
        findViewById<TextView>(R.id.textView16).text = data.tradesHourly.toString()
        findViewById<TextView>(R.id.textView18).text = data.totalTrades.toString()
    }

    private fun setupLoginScreen() {
        findViewById<Button>(R.id.btnLogin).setOnClickListener {
            val email = findViewById<EditText>(R.id.etEmail).text.toString()
            if (validateEmail(email)) {
                CoroutineScope(Dispatchers.Main).launch {
                    viewModel.sendEmail(email) { success, message ->
                        if (success) {
                            viewFlipper.displayedChild = SCREEN_CODE
                            Toast.makeText(this@MainActivity, message, Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(this@MainActivity, message, Toast.LENGTH_LONG).show()
                        }
                    }
                }
            }
        }
    }

    private fun loadDashboardData(userId: String) {
        CoroutineScope(Dispatchers.Main).launch {
            viewModel.loadDashboardData(userId) { success, result ->
                if (success) {
                    if (result != null) {
                        updateUI(result)
                    }
                } else {
                    Toast.makeText(this@MainActivity, "Не удалось загркзить данные.", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun setupCodeScreen() {
        findViewById<Button>(R.id.btnCode).setOnClickListener {
            val code = findViewById<PinView>(R.id.pinView).text.toString()
            if (code.length == 6) {
                CoroutineScope(Dispatchers.Main).launch {
                    viewModel.verifyCode(code) { success, userId ->
                        if (success && userId != null) {
                            getSharedPreferences("AppSettings", MODE_PRIVATE)
                                .edit()
                                .putString(PREF_USER_ID, userId)
                                .putLong(PREF_SESSION_TIME, System.currentTimeMillis())
                                .apply()
                            viewFlipper.displayedChild = SCREEN_MAIN
                            loadDashboardData(userId)
                        } else {
                            Toast.makeText(this@MainActivity, "Ошибка верификации", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }


    override fun onPause() {
        super.onPause()
        saveCurrentScreen()
    }

    private fun saveCurrentScreen() {
        getSharedPreferences("AppSettings", MODE_PRIVATE)
            .edit()
            .putInt(PREF_CURRENT_SCREEN, viewFlipper.displayedChild)
            .apply()
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

    private fun showWalletDialog() {
        val dialog = Dialog(this)
        dialog.setContentView(R.layout.dialog_fragment)
        dialog.setCancelable(true)
        dialog.window?.setBackgroundDrawableResource(android.R.color.transparent)

        val etPrivateKey = dialog.findViewById<EditText>(R.id.etPrivateKey)
        val etPublicKey = dialog.findViewById<EditText>(R.id.etPrimaryWalletAddress)
        val etPositionSize = dialog.findViewById<EditText>(R.id.etPositionSize)
        val etSlippage = dialog.findViewById<EditText>(R.id.etSlippageTolerance)
        val btnSave = dialog.findViewById<Button>(R.id.btnSaveChanges)
        btnSave.setOnClickListener {
            val privateKey = etPrivateKey.text.toString().takeIf { it.isNotEmpty() }
            val publicKey = etPublicKey.text.toString().takeIf { it.isNotEmpty() }
            val positionSize = etPositionSize.text.toString().toIntOrNull() ?: 0
            val slippage = etSlippage.text.toString().toIntOrNull() ?: 0

            CoroutineScope(Dispatchers.Main).launch {
                viewModel.updateWallet(
                    userId = getSharedPreferences("AppSettings", MODE_PRIVATE).getString(PREF_USER_ID, null)
                        .toString(),
                    publicKey = publicKey,
                    privateKey = privateKey,
                    positionSize = positionSize,
                    slippageTolerance = slippage
                ) { success, errorMessage ->
                    if (success) {
                        loadDashboardData(getSharedPreferences("AppSettings", MODE_PRIVATE).getString(PREF_USER_ID, null)
                            .toString())
                        Toast.makeText(this@MainActivity, "Успех", Toast.LENGTH_LONG).show()
                    } else {
                        val message = errorMessage ?: "Unknown error"
                        Toast.makeText(this@MainActivity, "Ошибка: $message", Toast.LENGTH_LONG).show()
                        Log.e("WalletUpdate", "Error: $message")
                    }
                }
            }
            dialog.dismiss()
        }

        dialog.show()
    }

    fun shortenKey(fullKey: String, firstChars: Int = 5, lastChars: Int = 3): String {
        if (fullKey.length <= firstChars + lastChars) return fullKey
        return "${fullKey.take(firstChars)}...${fullKey.takeLast(lastChars)}"
    }

    fun activateBot(btn:Button, isCheked:Boolean) {
        btn.isActivated = false
        val userId = getSharedPreferences("AppSettings", MODE_PRIVATE).getString(PREF_USER_ID, null)
            .toString()
        val publicKey = this.publicKey
        CoroutineScope(Dispatchers.Main).launch {
            viewModel.toggleBot(userId, publicKey, isCheked) { success, message ->
                if (success) {
                    btn.isActivated = true
                    if (isCheked){
                        Toast.makeText(this@MainActivity, "Бот запущен", Toast.LENGTH_SHORT).show()
                    } else{
                        Toast.makeText(this@MainActivity, "Бот выключен", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    btn.isActivated = true
                    Toast.makeText(this@MainActivity, "Ошибка: $message", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
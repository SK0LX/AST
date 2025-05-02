package com.example.ast

import AuthViewModel
import android.app.Dialog
import android.content.SharedPreferences
import android.os.Bundle
import android.util.Log
import android.util.Patterns
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import androidx.cardview.widget.CardView
import androidx.core.content.ContextCompat
import com.chaos.view.PinView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import kotlin.math.abs
import androidx.lifecycle.lifecycleScope
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

class MainActivity : AppCompatActivity() {
    private val viewModel: AuthViewModel by viewModels()
    private lateinit var viewFlipper: ViewFlipper
    private lateinit var notificationManager: AppNotificationManager
    private lateinit var permissionManager: PermissionManager
    private var isDarkTheme = false
    private var publicKey = ""
    private var refreshJob: Job? = null
    companion object {
        const val SCREEN_LOGIN = 0
        const val SCREEN_CODE = 1
        const val SCREEN_MAIN = 2
        const val PREF_CURRENT_SCREEN = "current_screen"
        private var PREF_USER_ID = "USER_ID"
        private var PREF_SESSION_TIME = "SESSION_TIME"
        private const val PREF_FCM_TOKEN    = "FCM_TOKEN"
        private var EMAIL = "Email"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
        notificationManager = AppNotificationManager(this)
        super.onCreate(savedInstanceState)
        AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (!task.isSuccessful) {
                Log.w("FCM", "Fetching FCM registration token failed", task.exception)
                return@addOnCompleteListener
            }
            val token = task.result
            Log.d("FCM", "FCM Token: $token")
            val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
            prefs.edit()
                .putString(PREF_FCM_TOKEN, token)
                .apply()
        }
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

        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<Button>(R.id.btnBack).setOnClickListener {
            CoroutineScope(Dispatchers.Main).launch {
                var email = getSharedPreferences("AppSettings", MODE_PRIVATE)
                    .getString(EMAIL, null)
                viewModel.logOutPhone(email!!){ success, errorMessage ->
                    if (success){
                        viewFlipper.displayedChild = SCREEN_LOGIN
                        Toast.makeText(this@MainActivity, "Вы вышли из аккаунта", Toast.LENGTH_SHORT).show()
                    } else{
                        Toast.makeText(this@MainActivity, errorMessage, Toast.LENGTH_SHORT).show()
                    }

                }
            }
        }

        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<Button>(R.id.btnEditSettings).setOnClickListener{
            showWalletDialog()
        }

        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<Switch>(R.id.switch1).setOnCheckedChangeListener { btn, isCheked ->
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
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.tvBalanceValue).text = data.balance
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.tvAddressValue).text = shortenKey(data.publicKey)
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.tvPrivateKeyValue).text = shortenKey(data.privateKeyPreview)
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.tvPositionValue).text = data.positionSize.toString()
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.tvPercentage).text = "${data.successRate}%"
        this.publicKey = data.publicKey
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.textView14).text = data.tradesToday.toString()
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.textView16).text = data.tradesHourly.toString()
        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<TextView>(R.id.textView18).text = data.totalTrades.toString()


        val inputFmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        val dispFmt  = SimpleDateFormat("MMM dd",   Locale.US)

        val pnlItems = data.pnl.mapNotNull {
            inputFmt.parse(it.date)?.let { d ->
                PnlItem(dispFmt.format(d).uppercase(Locale.US), it.value.toFloat())
            }
        }

        // Если нет ни одного ненулевого значения, скрываем карточку
        val hasAny = pnlItems
            .groupBy { it.date }
            .values
            .map { entries -> entries.sumOf { it.value.toDouble() }.toFloat() }
            .any { it != 0f }

        viewFlipper.getChildAt(SCREEN_MAIN).findViewById<CardView>(R.id.cardPNL).visibility =
            if (hasAny) View.VISIBLE else View.GONE

        if (hasAny) setupPnlChart(pnlItems)
    }

    private fun setupPnlChart(data: List<PnlItem>) {
        val container = viewFlipper.getChildAt(SCREEN_MAIN).findViewById<LinearLayout>(R.id.pnlContainer)
        container.removeAllViews()

        // 1) Суммируем по дате
        val summed = data.groupBy { it.date }
            .mapValues { (_, list) -> list.sumOf { it.value.toDouble() }.toFloat() }

        // 2) Генерируем ровно 14 дней назад, в том же формате UPPERCASE
        val cal = Calendar.getInstance()
        val df  = SimpleDateFormat("MMM dd", Locale.US)
        val last14 = (13 downTo 0).map { offset ->
            cal.time = Date()
            cal.add(Calendar.DAY_OF_YEAR, -offset)
            df.format(cal.time).uppercase(Locale.US)
        }

        // 3) Нормировка по модулю
        val maxAbs   = (summed.values.maxOfOrNull { abs(it) } ?: 0f).coerceAtLeast(0.00001f)
        val maxBarPx = 200.dpToPx().toInt()
        val minBarPx =   8.dpToPx().toInt()

        // 4) Рисуем все 14 точек
        last14.forEach { day ->
            val view   = layoutInflater.inflate(R.layout.item_pnl, container, false)
            val bar    = view.findViewById<View>(R.id.bar)
            val tvDate = view.findViewById<TextView>(R.id.tvDate)
            val tvVal  = view.findViewById<TextView>(R.id.tvValue)

            val value = summed[day] ?: 0f

            // Значение (пусто, если 0; с минусом, если <0)
            tvVal.text = if (value == 0f) ""
            else "%.4f".format(value).trimEnd('0').trimEnd('.')

            // Дата — гарантированно видна
            tvDate.text = day

            // Цвет
            val colorRes = if (value >= 0f) R.color.green else R.color.red
            bar.background.setTint(ContextCompat.getColor(this, colorRes))

            // Высота
            val heightPx = ((abs(value) / maxAbs) * maxBarPx)
                .toInt()
                .coerceAtLeast(minBarPx)
                .coerceAtMost(maxBarPx)
            bar.layoutParams.height = heightPx

            container.addView(view)
        }
    }

    fun Int.dpToPx(): Float = this * resources.displayMetrics.density

    data class PnlItem(val date: String, val value: Float)


    private fun setupLoginScreen() {
        findViewById<Button>(R.id.btnLogin).setOnClickListener {
            val email = findViewById<EditText>(R.id.etEmail).text.toString()
            if (validateEmail(email)) {
                CoroutineScope(Dispatchers.Main).launch {
                    viewModel.sendEmail(email) { success, message ->
                        if (success) {
                            viewFlipper.displayedChild = SCREEN_CODE
                            getSharedPreferences("AppSettings", MODE_PRIVATE)
                            val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
                            prefs.edit()
                                .putString(EMAIL, email)
                                .apply()
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
                            var token = getSharedPreferences("AppSettings", MODE_PRIVATE)
                                .getString(PREF_FCM_TOKEN, null)
                            var email = getSharedPreferences("AppSettings", MODE_PRIVATE)
                                .getString(EMAIL, null)
                            viewModel.registerPhone(email = email!!, deviceToken = token!!){ success, errorMessage ->
                                if (success){
                                    Toast.makeText(this@MainActivity, "Телефон зарегестрирован", Toast.LENGTH_SHORT).show()
                                } else{
                                    Toast.makeText(this@MainActivity, errorMessage, Toast.LENGTH_SHORT).show()
                                }
                            }
                            loadDashboardData(userId)
                        } else {
                            Toast.makeText(this@MainActivity, "Ошибка верификации", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
    }

    private fun saveCurrentScreen() {
        getSharedPreferences("AppSettings", MODE_PRIVATE)
            .edit()
            .putInt(PREF_CURRENT_SCREEN, viewFlipper.displayedChild)
            .apply()
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

    override fun onResume() {
        super.onResume()
        // Стартуем обновление каждые 10 секунд, но только если показывается экран MAIN
        val prefs = getSharedPreferences("AppSettings", MODE_PRIVATE)
        val userId = prefs.getString(PREF_USER_ID, null)
        refreshJob = lifecycleScope.launch {
            while (isActive) {
                // Проверяем, что сейчас именно основной экран
                if (viewFlipper.displayedChild == SCREEN_MAIN && !userId.isNullOrEmpty()) {
                    loadDashboardData(userId)
                }
                delay(10_000L)
            }
        }
    }

    override fun onPause() {
        super.onPause()
        // Отменяем обновления, когда Activity не на переднем плане
        refreshJob?.cancel()
        saveCurrentScreen()
    }
}
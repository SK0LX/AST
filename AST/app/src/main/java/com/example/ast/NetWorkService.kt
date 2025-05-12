import android.util.Log
import com.example.ast.AddWalletRequest
import com.example.ast.AuthRequest
import com.example.ast.AuthResponse
import com.example.ast.CheckAuthResponse
import com.example.ast.DashboardResponse
import com.example.ast.LogOutRequest
import com.example.ast.RegisterPhoneRequest
import com.example.ast.ToggleRequest
import com.example.ast.VerifyRequest
import com.example.ast.VerifyResponse
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class NetworkService {
    private val api = RetrofitClient.instance

    suspend fun auth(
        email: String,
        callback: (AuthResponse?, String) -> Unit
    ) {
        try {
            val response = api.auth(AuthRequest(email))
            callback(response, "")
        } catch (e: Exception) {
            callback(null, "Ошибка сети: ${e.message}")
        }
    }

    fun checkAuth(userId: String, callback: (Boolean) -> Unit) {
        api.checkAuth(userId).enqueue(object : Callback<CheckAuthResponse> {
            override fun onResponse(call: Call<CheckAuthResponse>, response: Response<CheckAuthResponse>) {
                callback(response.body()?.authenticated ?: false)
            }
            override fun onFailure(call: Call<CheckAuthResponse>, t: Throwable) {
                callback(false)
            }
        })
    }



    // Добавление кошелька
    suspend fun addWallet(request: AddWalletRequest, callback: (Boolean, String?) -> Unit) {
        try {
            val response = api.addWallet(request)
            if (response.isSuccessful) {
                callback(true, null)
            } else {
                // Парсим тело ошибки
                val errorBody = response.errorBody()?.string()
                val errorMessage = try {
                    Json.decodeFromString<Map<String, String>>(errorBody ?: "")["error"]
                        ?: "Unknown error"
                } catch (e: Exception) {
                    "Error code: ${response.code()}"
                }
                callback(false, errorMessage)
            }
        } catch (e: Exception) {
            Log.e("Network", "Wallet update error", e)
            callback(false, "Network error: ${e.message}")
        }
    }

    // Получение данных дашборда
    suspend fun getDashboard(userId: String, callback: (DashboardResponse?, String) -> Unit) {
        try {
            val response = api.getDashboard(userId)
            callback(response, "")
        } catch (e: Exception) {
            callback(null, "Ошибка сети: ${e.message}")
        }
    }

    // Переключение бота
    suspend fun toggleBot(
        request: ToggleRequest,
        callback: (Boolean, String?) -> Unit
    ) {
        try {
            val response = api.toggleBot(request)
            if (response.isSuccessful) {
                callback(true, null)
            } else {
                val errorBody = response.errorBody()?.string()
                val errorMessage = try {
                    Json.decodeFromString<Map<String, String>>(errorBody ?: "")["error"]
                        ?: "Unknown error"
                } catch (e: Exception) {
                    "Error code: ${response.code()}"
                }
                callback(false, errorMessage)
            }
        } catch (e: Exception) {
            Log.e("Network", "Toggle bot error", e)
            callback(false, "Network error: ${e.message}")
        }
    }

    suspend fun verify(
        email: String,
        otp: String,
        callback: (VerifyResponse?, String?) -> Unit
    ) {
        try {
            val response = api.verify(VerifyRequest(email, otp))
            callback(response, "куку")
        } catch (e: Exception) {
            callback(null, "Ошибка верификации: ${e.message}")
        }
    }

    suspend fun registerPhone(
        email: String?,
        deviceToken: String?,
        callback: (Boolean, String) -> Unit
    ){
        try {
            val response = api.registerPhone(RegisterPhoneRequest(email, deviceToken))
            if (response.success != null){
                if (response.success){
                    callback(response.success, "-")
                }
                else{
                    callback(false, response.error!!)
                }
            }
        } catch (e: Exception){

        }
    }

    suspend fun logOutPhone(
        email: String?,
        callback: (Boolean, String) -> Unit
    ){
        val response = api.logOutPhone(LogOutRequest(email))
        if (response.success != null){
            if (response.success){
                callback(response.success, "-")
            }
            else{
                callback(false, response.error!!)
            }
        }
    }
}